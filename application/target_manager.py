# -*- coding: utf-8 -*-
"""Target Window Manager managing auto-detection, explicit lock, and app-binding."""

import os
from typing import Optional, Dict, Any, Callable, List, Tuple
from platform_layer.base import BaseWindowManager


class TargetManager:
    """Manages the target application window that receives shortcut inputs."""

    MODE_AUTO = "auto"
    MODE_LOCKED = "locked"

    def __init__(self, window_manager: BaseWindowManager, own_hwnds: Optional[List[int]] = None):
        self.window_manager = window_manager
        self.own_hwnds = set(own_hwnds or [])
        self.mode = self.MODE_AUTO

        self._recent_external_hwnd: Optional[int] = None
        self._locked_hwnd: Optional[int] = None
        self._locked_info: Dict[str, Any] = {}
        self._on_target_changed_callbacks: List[Callable[[Dict[str, Any]], None]] = []

    def register_own_hwnd(self, hwnd: int):
        if hwnd:
            self.own_hwnds.add(int(hwnd))

    def unregister_own_hwnd(self, hwnd: int):
        if hwnd in self.own_hwnds:
            self.own_hwnds.remove(int(hwnd))

    def add_target_changed_listener(self, cb: Callable[[Dict[str, Any]], None]):
        self._on_target_changed_callbacks.append(cb)

    def _notify_target_changed(self):
        info = self.get_target_info()
        for cb in self._on_target_changed_callbacks:
            try:
                cb(info)
            except Exception:
                pass

    def update_active_window(self, hwnd: Optional[int]):
        """Called periodically (e.g. 100ms) with current foreground window."""
        if not hwnd or hwnd in self.own_hwnds:
            return

        if not self.window_manager.is_window_valid(hwnd):
            return

        # Never track any window belonging to our own application process
        info = self.window_manager.get_window_info(hwnd)
        if info.get("process_id") == os.getpid():
            self.own_hwnds.add(int(hwnd))
            return

        prev_target = self.get_effective_hwnd()
        self._recent_external_hwnd = hwnd

        if self.mode == self.MODE_AUTO and self._recent_external_hwnd != prev_target:
            self._notify_target_changed()

    def lock_target(self, hwnd: Optional[int] = None) -> bool:
        """Lock input delivery to specific window or current recent window."""
        target = hwnd or self._recent_external_hwnd or self.window_manager.get_foreground_window_handle()
        if not target or target in self.own_hwnds or not self.window_manager.is_window_valid(target):
            return False

        info = self.window_manager.get_window_info(target)
        if info.get("process_id") == os.getpid():
            return False

        self._locked_hwnd = int(target)
        self._locked_info = info
        self.mode = self.MODE_LOCKED
        self._notify_target_changed()
        return True

    def unlock_target(self):
        """Unlock and revert to auto-tracking."""
        self.mode = self.MODE_AUTO
        self._locked_hwnd = None
        self._locked_info = {}
        self._notify_target_changed()

    def toggle_lock(self) -> bool:
        if self.mode == self.MODE_LOCKED:
            self.unlock_target()
            return False
        else:
            return self.lock_target()

    def get_effective_hwnd(self) -> Optional[int]:
        if self.mode == self.MODE_LOCKED:
            if self._locked_hwnd and self.window_manager.is_window_valid(self._locked_hwnd):
                return self._locked_hwnd
            return None
        return self._recent_external_hwnd

    def get_target_info(self) -> Dict[str, Any]:
        hwnd = self.get_effective_hwnd()
        if not hwnd or not self.window_manager.is_window_valid(hwnd):
            return {
                "handle": None,
                "title": "(无目标)" if self.mode == self.MODE_AUTO else "(锁定目标已失效)",
                "process_name": "",
                "is_admin": False,
                "is_locked": self.mode == self.MODE_LOCKED,
                "is_valid": False,
            }

        info = self.window_manager.get_window_info(hwnd)
        if info.get("process_id") == os.getpid():
            return {
                "handle": None,
                "title": "(无目标)" if self.mode == self.MODE_AUTO else "(锁定目标已失效)",
                "process_name": "",
                "is_admin": False,
                "is_locked": self.mode == self.MODE_LOCKED,
                "is_valid": False,
            }
        info["is_locked"] = (self.mode == self.MODE_LOCKED)
        info["is_valid"] = True
        return info

    def prepare_target_for_input(self) -> Tuple[bool, str]:
        """
        Verify target window validity and privilege state before macro execution.
        Returns (success, message_or_warning).
        """
        hwnd = self.get_effective_hwnd()
        if not hwnd:
            return False, "未找到目标输入窗口，请先点击一下目标软件！"

        if not self.window_manager.is_window_valid(hwnd):
            if self.mode == self.MODE_LOCKED:
                return False, "锁定的目标窗口已关闭，请重新锁定或切换为自动模式！"
            return False, "目标窗口无效或已关闭！"

        # Ensure target window is brought safely to foreground if it's not currently foreground
        curr_fg = self.window_manager.get_foreground_window_handle()
        if curr_fg != hwnd:
            self.window_manager.set_foreground_safe(hwnd)

        info = self.window_manager.get_window_info(hwnd)
        if info.get("is_admin", False):
            # Target is running as Administrator
            return True, "警告：目标软件以管理员权限运行，如果输入无效请尝试以管理员身份运行本程序。"

        return True, ""
