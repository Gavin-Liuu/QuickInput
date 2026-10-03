# -*- coding: utf-8 -*-
"""Action Executor unit and integration tests."""

import time
from typing import List, Optional, Dict, Any

from domain.action import Action, ActionStep
from platform_layer.base import (
    BaseInputInjector,
    BaseClipboardManager,
    BaseWindowManager,
)
from application.target_manager import TargetManager
from application.action_executor import ActionExecutor


class MockInputInjector(BaseInputInjector):
    def __init__(self):
        self.sent_texts: List[str] = []
        self.sent_keys: List[str] = []
        self.sent_hotkeys: List[List[str]] = []
        self.sent_mouse: List[str] = []

    def send_text(self, text: str) -> bool:
        self.sent_texts.append(text)
        return True

    def send_key(self, key_name: str, key_up: bool = False, key_down: bool = True) -> bool:
        self.sent_keys.append(key_name)
        return True

    def send_key_press(self, key_name: str) -> bool:
        self.sent_keys.append(key_name)
        return True

    def send_hotkey(self, keys: List[str]) -> bool:
        self.sent_hotkeys.append(keys)
        return True

    def send_mouse(self, action: str = "click", x: Optional[int] = None, y: Optional[int] = None) -> bool:
        self.sent_mouse.append(action)
        return True


class MockClipboardManager(BaseClipboardManager):
    def __init__(self, initial_text: str = ""):
        self.text = initial_text
        self.pasted_texts: List[str] = []

    def get_text(self) -> str:
        return self.text

    def set_text(self, text: str) -> bool:
        self.text = text
        return True

    def paste_text(self, text: str, restore_clipboard: bool = True) -> bool:
        self.pasted_texts.append(text)
        return True


class MockWindowManager(BaseWindowManager):
    def __init__(self, valid_hwnd: int = 12345):
        self.valid_hwnd = valid_hwnd

    def get_foreground_window_handle(self) -> Any:
        return self.valid_hwnd

    def get_window_info(self, handle: Any) -> Dict[str, Any]:
        return {
            "handle": handle,
            "title": "Labelme - Annotate Dataset",
            "process_name": "labelme.exe",
            "process_id": 9999,
            "is_admin": False,
            "is_valid": True,
        }

    def is_window_valid(self, handle: Any) -> bool:
        return bool(handle == self.valid_hwnd)

    def set_foreground_safe(self, handle: Any) -> bool:
        return True

    def is_target_elevated(self, handle: Any) -> bool:
        return False


def test_executor_text_and_key():
    inj = MockInputInjector()
    clip = MockClipboardManager()
    wm = MockWindowManager()
    tm = TargetManager(window_manager=wm)
    tm.update_active_window(12345)

    executor = ActionExecutor(injector=inj, clipboard_mgr=clip, target_mgr=tm)

    action = Action(
        id="act_test",
        label="Test Action",
        steps=[
            ActionStep(type="text", value="defect"),
            ActionStep(type="key", key="ENTER"),
            ActionStep(type="hotkey", hotkey="CTRL+S"),
        ],
    )

    success, msg = executor.execute_sync(action)
    assert success is True
    assert "defect" in inj.sent_texts
    assert "ENTER" in inj.sent_keys
    assert ["CTRL", "S"] in inj.sent_hotkeys


def test_executor_variable_interpolation():
    inj = MockInputInjector()
    clip = MockClipboardManager(initial_text="CLIPBOARD_DATA")
    wm = MockWindowManager()
    tm = TargetManager(window_manager=wm)
    tm.update_active_window(12345)

    executor = ActionExecutor(injector=inj, clipboard_mgr=clip, target_mgr=tm)
    executor.counter = 42

    action = Action(
        id="act_vars",
        label="Variable Action",
        steps=[
            ActionStep(type="text", value="Item-{{counter}} in {{app_name}}: {{clipboard}}"),
        ],
    )

    success, msg = executor.execute_sync(action)
    assert success is True
    assert len(inj.sent_texts) == 1
    assert "Item-42 in labelme.exe: CLIPBOARD_DATA" in inj.sent_texts[0]
    # Counter should increment
    assert executor.counter == 43


def test_executor_auto_enter():
    inj = MockInputInjector()
    clip = MockClipboardManager()
    wm = MockWindowManager()
    tm = TargetManager(window_manager=wm)
    tm.update_active_window(12345)

    executor = ActionExecutor(injector=inj, clipboard_mgr=clip, target_mgr=tm)

    action = Action(
        id="act_single",
        label="Single Step",
        steps=[ActionStep(type="text", value="rb")],
        auto_enter=False,
    )

    # auto_enter_override = True: sends ENTER even though action.auto_enter is False
    success, msg = executor.execute_sync(action, auto_enter_override=True)
    assert success is True
    assert "rb" in inj.sent_texts
    assert "ENTER" in inj.sent_keys

    # auto_enter_override = False: does NOT send ENTER even if action.auto_enter is True
    inj.sent_texts.clear()
    inj.sent_keys.clear()
    action_with_enter = Action(
        id="act_with_enter",
        label="With Enter",
        steps=[ActionStep(type="text", value="test")],
        auto_enter=True,
    )
    success2, _ = executor.execute_sync(action_with_enter, auto_enter_override=False)
    assert success2 is True
    assert "test" in inj.sent_texts
    assert "ENTER" not in inj.sent_keys


def test_executor_cancellation():
    inj = MockInputInjector()
    clip = MockClipboardManager()
    wm = MockWindowManager()
    tm = TargetManager(window_manager=wm)
    tm.update_active_window(12345)

    executor = ActionExecutor(injector=inj, clipboard_mgr=clip, target_mgr=tm)

    action = Action(
        id="act_long",
        label="Long Macro",
        steps=[ActionStep(type="delay", ms=500) for _ in range(10)],
    )

    # Start async
    executor.execute_async(action)
    time.sleep(0.05)
    assert executor.is_running is True

    # Request cancel
    executor.cancel_current()
    time.sleep(0.1)
    assert executor.is_running is False


def test_executor_max_steps_safeguard():
    inj = MockInputInjector()
    clip = MockClipboardManager()
    wm = MockWindowManager()
    tm = TargetManager(window_manager=wm)
    tm.update_active_window(12345)

    executor = ActionExecutor(
        injector=inj, clipboard_mgr=clip, target_mgr=tm, max_steps=5
    )

    action = Action(
        id="act_oversize",
        label="Oversize Macro",
        steps=[ActionStep(type="text", value="a") for _ in range(10)],
    )

    success, msg = executor.execute_sync(action)
    assert success is False
    assert "步骤超限" in msg
