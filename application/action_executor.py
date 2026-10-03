# -*- coding: utf-8 -*-
"""Action Executor for running multi-step macros asynchronously without blocking UI."""

import datetime
import threading
import time
from typing import Optional, Dict, Any, List, Callable, Tuple
from domain.action import Action, ActionStep
from platform_layer.base import BaseInputInjector, BaseClipboardManager
from application.target_manager import TargetManager


class ActionExecutor:
    """Executes actions and macro sequences with cancellation, timeouts, and variable interpolation."""

    def __init__(
        self,
        injector: BaseInputInjector,
        clipboard_mgr: BaseClipboardManager,
        target_mgr: TargetManager,
        max_steps: int = 500,
        max_duration_sec: float = 30.0,
    ):
        self.injector = injector
        self.clipboard_mgr = clipboard_mgr
        self.target_mgr = target_mgr
        self.max_steps = max_steps
        self.max_duration_sec = max_duration_sec

        self.counter = 1
        self._lock = threading.Lock()
        self._is_running = False
        self._cancel_requested = False
        self._current_thread: Optional[threading.Thread] = None

        # Callbacks
        self.on_start: Optional[Callable[[str, int], None]] = None
        self.on_step: Optional[Callable[[int, int, str], None]] = None
        self.on_finish: Optional[Callable[[str, bool, str], None]] = None

        # Recent execution logs
        self.execution_logs: List[Dict[str, Any]] = []

    @property
    def is_running(self) -> bool:
        with self._lock:
            return self._is_running

    def cancel_current(self):
        """Request cancellation of currently running macro."""
        with self._lock:
            if self._is_running:
                self._cancel_requested = True

    def execute_async(self, action: Action, auto_enter_override: Optional[bool] = None) -> bool:
        """Start non-blocking execution in a worker thread."""
        with self._lock:
            if self._is_running:
                return False
            self._is_running = True
            self._cancel_requested = False

        self._current_thread = threading.Thread(
            target=self._run_worker,
            args=(action, auto_enter_override),
            daemon=True,
        )
        self._current_thread.start()
        return True

    def execute_sync(self, action: Action, auto_enter_override: Optional[bool] = None) -> Tuple[bool, str]:
        """Synchronous execution (useful for unit tests and testing single steps)."""
        with self._lock:
            if self._is_running:
                return False, "已有动作正在执行中"
            self._is_running = True
            self._cancel_requested = False

        try:
            return self._run_steps(action, auto_enter_override)
        finally:
            with self._lock:
                self._is_running = False

    def _run_worker(self, action: Action, auto_enter_override: Optional[bool]):
        try:
            success, msg = self._run_steps(action, auto_enter_override)
        finally:
            with self._lock:
                self._is_running = False

    def _flatten_steps(self, steps: List[ActionStep]) -> List[ActionStep]:
        flat = []
        for s in steps:
            if s.type == "repeat":
                count = max(1, s.count)
                for _ in range(count):
                    flat.extend(self._flatten_steps(s.steps))
            else:
                flat.append(s)
        return flat

    def _resolve_variables(self, text: str, target_info: Dict[str, Any]) -> str:
        """Replace {{clipboard}}, {{date}}, {{time}}, {{counter}}, {{app_name}}."""
        if not text:
            return ""

        if "{{counter}}" in text:
            text = text.replace("{{counter}}", str(self.counter))
            self.counter += 1

        if "{{date}}" in text:
            now_date = datetime.datetime.now().strftime("%Y-%m-%d")
            text = text.replace("{{date}}", now_date)

        if "{{time}}" in text:
            now_time = datetime.datetime.now().strftime("%H:%M:%S")
            text = text.replace("{{time}}", now_time)

        if "{{clipboard}}" in text:
            clip = self.clipboard_mgr.get_text()
            text = text.replace("{{clipboard}}", clip)

        if "{{app_name}}" in text:
            app = target_info.get("process_name") or target_info.get("title") or "Unknown"
            text = text.replace("{{app_name}}", app)

        return text

    def _run_steps(self, action: Action, auto_enter_override: Optional[bool]) -> Tuple[bool, str]:
        start_time = time.time()
        ready, target_msg = self.target_mgr.prepare_target_for_input()
        if not ready:
            err = f"执行中止: {target_msg}"
            self._log_execution(action.id, False, err)
            if self.on_finish:
                self.on_finish(action.id, False, err)
            return False, err

        target_info = self.target_mgr.get_target_info()
        all_steps = self._flatten_steps(action.steps)

        # Append auto-enter step if required
        need_auto_enter = action.auto_enter
        if auto_enter_override is not None:
            need_auto_enter = auto_enter_override
        if need_auto_enter:
            all_steps.append(ActionStep(type="key", key="ENTER"))

        total = len(all_steps)
        if total > self.max_steps:
            err = f"步骤超限: 总步骤数 {total} 超过最大允许 {self.max_steps}"
            self._log_execution(action.id, False, err)
            if self.on_finish:
                self.on_finish(action.id, False, err)
            return False, err

        if self.on_start:
            try:
                self.on_start(action.id, total)
            except Exception:
                pass

        step_idx = 0
        success = True
        final_message = "执行完成"

        while step_idx < total:
            if self._cancel_requested:
                success = False
                final_message = "已取消执行"
                break

            elapsed = time.time() - start_time
            if elapsed > self.max_duration_sec:
                success = False
                final_message = f"执行超时: 超过最大时间限制 {self.max_duration_sec} 秒"
                break

            step = all_steps[step_idx]
            step_desc = self._get_step_summary(step)
            if self.on_step:
                try:
                    self.on_step(step_idx + 1, total, step_desc)
                except Exception:
                    pass

            step_ok = self._execute_single_step(step, target_info)
            if not step_ok:
                if action.on_error == "stop":
                    success = False
                    final_message = f"第 {step_idx + 1} 步执行失败: {step_desc}"
                    break

            step_idx += 1

        self._log_execution(action.id, success, final_message)
        if self.on_finish:
            try:
                self.on_finish(action.id, success, final_message)
            except Exception:
                pass

        return success, final_message

    def _get_step_summary(self, step: ActionStep) -> str:
        if step.type == "text":
            return f"输入文本: {step.value[:15]}"
        elif step.type == "key":
            return f"按键: {step.key}"
        elif step.type == "hotkey":
            return f"组合键: {step.hotkey or '+'.join(step.keys)}"
        elif step.type == "delay":
            return f"等待: {step.ms}ms"
        elif step.type == "paste":
            return f"粘贴: {step.value[:15]}"
        elif step.type == "variable":
            return f"变量: {{{{{step.name}}}}}"
        elif step.type == "mouse":
            return f"鼠标: {step.mouse_action}"
        return step.type

    def _execute_single_step(self, step: ActionStep, target_info: Dict[str, Any]) -> bool:
        try:
            if step.type == "text":
                resolved = self._resolve_variables(step.value, target_info)
                return self.injector.send_text(resolved)

            elif step.type == "key":
                return self.injector.send_key_press(step.key)

            elif step.type == "hotkey":
                keys = step.keys
                if not keys and step.hotkey:
                    keys = [k.strip() for k in step.hotkey.split("+") if k.strip()]
                return self.injector.send_hotkey(keys)

            elif step.type == "delay":
                total_ms = max(0, step.ms)
                slept_ms = 0
                while slept_ms < total_ms:
                    if self._cancel_requested:
                        return False
                    chunk = min(30, total_ms - slept_ms)
                    time.sleep(chunk / 1000.0)
                    slept_ms += chunk
                return True

            elif step.type == "paste":
                resolved = self._resolve_variables(step.value, target_info)
                return self.clipboard_mgr.paste_text(resolved)

            elif step.type == "variable":
                resolved = self._resolve_variables(f"{{{{{step.name}}}}}", target_info)
                return self.injector.send_text(resolved)

            elif step.type == "mouse":
                return self.injector.send_mouse(step.mouse_action, step.x, step.y)

            return True
        except Exception:
            return False

    def _log_execution(self, action_id: str, success: bool, message: str):
        record = {
            "timestamp": datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "action_id": action_id,
            "success": success,
            "message": message,
        }
        self.execution_logs.append(record)
        if len(self.execution_logs) > 100:
            self.execution_logs.pop(0)
