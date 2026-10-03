# -*- coding: utf-8 -*-
"""Target Manager unit tests."""

from platform_layer.base import BaseWindowManager
from application.target_manager import TargetManager


class FakeWindowManager(BaseWindowManager):
    def __init__(self):
        self.windows = {
            1001: {"title": "Notepad", "process_name": "notepad.exe", "is_admin": False},
            1002: {"title": "Admin CMD", "process_name": "cmd.exe", "is_admin": True},
        }

    def get_foreground_window_handle(self):
        return 1001

    def get_window_info(self, handle):
        if handle in self.windows:
            w = self.windows[handle]
            return {
                "handle": handle,
                "title": w["title"],
                "process_name": w["process_name"],
                "is_admin": w["is_admin"],
                "is_valid": True,
            }
        return {"handle": handle, "title": "", "process_name": "", "is_admin": False, "is_valid": False}

    def is_window_valid(self, handle):
        return handle in self.windows

    def set_foreground_safe(self, handle):
        return True

    def is_target_elevated(self, handle):
        return self.windows.get(handle, {}).get("is_admin", False)


def test_target_manager_auto_mode():
    fwm = FakeWindowManager()
    tm = TargetManager(window_manager=fwm, own_hwnds=[9999])

    # Ignore own hwnd
    tm.update_active_window(9999)
    assert tm.get_effective_hwnd() is None

    # Update with external window
    tm.update_active_window(1001)
    assert tm.get_effective_hwnd() == 1001
    info = tm.get_target_info()
    assert info["process_name"] == "notepad.exe"
    assert info["is_locked"] is False


def test_target_manager_lock_mode():
    fwm = FakeWindowManager()
    tm = TargetManager(window_manager=fwm)
    tm.update_active_window(1001)

    # Lock to 1001
    locked = tm.lock_target(1001)
    assert locked is True
    assert tm.mode == TargetManager.MODE_LOCKED

    # Even if active window changes to 1002, locked remains 1001
    tm.update_active_window(1002)
    assert tm.get_effective_hwnd() == 1001

    # Unlock
    tm.unlock_target()
    assert tm.mode == TargetManager.MODE_AUTO
    assert tm.get_effective_hwnd() == 1002


def test_target_manager_admin_elevation_warning():
    fwm = FakeWindowManager()
    tm = TargetManager(window_manager=fwm)
    tm.update_active_window(1002)  # Admin CMD

    ok, warning = tm.prepare_target_for_input()
    assert ok is True
    assert "管理员权限" in warning


def test_target_manager_locked_focus_restore():
    fwm = FakeWindowManager()
    fwm.set_fg_called_with = None

    def mock_set_fg(h):
        fwm.set_fg_called_with = h
        return True

    fwm.set_foreground_safe = mock_set_fg

    tm = TargetManager(window_manager=fwm)
    tm.lock_target(1002)

    # Currently foreground is 1001, but target is locked to 1002
    assert fwm.get_foreground_window_handle() == 1001

    ok, msg = tm.prepare_target_for_input()
    assert ok is True
    assert fwm.set_fg_called_with == 1002
