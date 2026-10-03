# -*- coding: utf-8 -*-
"""Windows Window Manager implementation."""

import ctypes
from ctypes import wintypes
import os
from typing import Dict, Any, Optional
import win32gui
import win32process
import win32api
import win32con
import psutil

from ..base import BaseWindowManager


class WindowsWindowManager(BaseWindowManager):
    """Windows implementation of window queries, focus detection, and safety checks."""

    def __init__(self, my_hwnd: Optional[int] = None):
        self.my_hwnd = my_hwnd

    def set_self_hwnd(self, hwnd: int):
        self.my_hwnd = hwnd

    def get_foreground_window_handle(self) -> Optional[int]:
        try:
            hwnd = win32gui.GetForegroundWindow()
            return hwnd if hwnd and hwnd != 0 else None
        except Exception:
            return None

    def is_window_valid(self, handle: Any) -> bool:
        if not handle:
            return False
        try:
            return bool(win32gui.IsWindow(int(handle)))
        except Exception:
            return False

    def get_window_info(self, handle: Any) -> Dict[str, Any]:
        info: Dict[str, Any] = {
            "handle": handle,
            "title": "",
            "process_name": "",
            "process_id": 0,
            "is_admin": False,
            "is_valid": False,
        }
        if not handle or not self.is_window_valid(handle):
            return info

        hwnd = int(handle)
        info["is_valid"] = True

        # Title
        try:
            info["title"] = win32gui.GetWindowText(hwnd) or ""
        except Exception:
            info["title"] = ""

        # Process ID & Name
        try:
            _, pid = win32process.GetWindowThreadProcessId(hwnd)
            info["process_id"] = pid
            if pid > 0:
                try:
                    proc = psutil.Process(pid)
                    info["process_name"] = proc.name()
                except Exception:
                    # Fallback via win32api
                    h_proc = win32api.OpenProcess(
                        win32con.PROCESS_QUERY_LIMITED_INFORMATION, False, pid
                    )
                    if h_proc:
                        try:
                            info["process_name"] = os.path.basename(
                                win32process.GetModuleFileNameEx(h_proc, 0)
                            )
                        finally:
                            win32api.CloseHandle(h_proc)
        except Exception:
            pass

        # Elevated check
        info["is_admin"] = self.is_target_elevated(hwnd)
        return info

    def is_target_elevated(self, handle: Any) -> bool:
        """Check if target process has elevated token."""
        if not handle or not self.is_window_valid(handle):
            return False
        try:
            _, pid = win32process.GetWindowThreadProcessId(int(handle))
            if pid <= 0:
                return False
            
            # Query token elevation via OpenProcessToken
            PROCESS_QUERY_LIMITED_INFORMATION = 0x1000
            TOKEN_QUERY = 0x0008
            TokenElevation = 20

            advapi32 = ctypes.windll.advapi32
            kernel32 = ctypes.windll.kernel32

            h_proc = kernel32.OpenProcess(PROCESS_QUERY_LIMITED_INFORMATION, False, pid)
            if not h_proc:
                # If we cannot open with query info, target might be running as elevated while we are standard
                return True

            h_token = wintypes.HANDLE()
            elevated = False
            try:
                if advapi32.OpenProcessToken(h_proc, TOKEN_QUERY, ctypes.byref(h_token)):
                    class TOKEN_ELEVATION(ctypes.Structure):
                        _fields_ = [("TokenIsElevated", wintypes.DWORD)]

                    elevation = TOKEN_ELEVATION()
                    size = wintypes.DWORD(ctypes.sizeof(elevation))
                    ret_size = wintypes.DWORD()
                    if advapi32.GetTokenInformation(
                        h_token,
                        TokenElevation,
                        ctypes.byref(elevation),
                        size,
                        ctypes.byref(ret_size),
                    ):
                        elevated = bool(elevation.TokenIsElevated)
            finally:
                if h_token:
                    kernel32.CloseHandle(h_token)
                kernel32.CloseHandle(h_proc)

            return elevated
        except Exception:
            return False

    def set_foreground_safe(self, handle: Any) -> bool:
        """Safely bring window to foreground using AttachThreadInput technique to avoid stealing focus error."""
        if not handle or not self.is_window_valid(handle):
            return False

        hwnd = int(handle)
        try:
            curr_fg = win32gui.GetForegroundWindow()
            if curr_fg == hwnd:
                return True

            curr_thread_id = win32api.GetCurrentThreadId()
            fg_thread_id = 0
            if curr_fg:
                try:
                    fg_thread_id, _ = win32process.GetWindowThreadProcessId(curr_fg)
                except Exception:
                    fg_thread_id = 0

            if curr_thread_id != fg_thread_id and fg_thread_id != 0:
                ctypes.windll.user32.AttachThreadInput(curr_thread_id, fg_thread_id, True)

            win32gui.SetForegroundWindow(hwnd)

            if curr_thread_id != fg_thread_id and fg_thread_id != 0:
                ctypes.windll.user32.AttachThreadInput(curr_thread_id, fg_thread_id, False)

            return True
        except Exception:
            return False
