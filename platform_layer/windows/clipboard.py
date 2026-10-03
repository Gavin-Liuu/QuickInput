# -*- coding: utf-8 -*-
"""Windows Clipboard Manager with auto-restore capability."""

import time
import win32clipboard
import win32con
from typing import Optional
from ..base import BaseClipboardManager, BaseInputInjector


class WindowsClipboardManager(BaseClipboardManager):
    """Windows clipboard manager with backup and restore."""

    def __init__(self, injector: Optional[BaseInputInjector] = None):
        self.injector = injector

    def get_text(self) -> str:
        for _ in range(5):
            try:
                win32clipboard.OpenClipboard()
                try:
                    if win32clipboard.IsClipboardFormatAvailable(win32con.CF_UNICODETEXT):
                        return win32clipboard.GetClipboardData(win32con.CF_UNICODETEXT) or ""
                    elif win32clipboard.IsClipboardFormatAvailable(win32con.CF_TEXT):
                        data = win32clipboard.GetClipboardData(win32con.CF_TEXT)
                        return data.decode("utf-8", errors="ignore") if isinstance(data, bytes) else str(data or "")
                    return ""
                finally:
                    win32clipboard.CloseClipboard()
            except Exception:
                time.sleep(0.01)
        return ""

    def set_text(self, text: str) -> bool:
        for _ in range(5):
            try:
                win32clipboard.OpenClipboard()
                try:
                    win32clipboard.EmptyClipboard()
                    win32clipboard.SetClipboardData(win32con.CF_UNICODETEXT, text)
                    return True
                finally:
                    win32clipboard.CloseClipboard()
            except Exception:
                time.sleep(0.01)
        return False

    def paste_text(self, text: str, restore_clipboard: bool = True) -> bool:
        """Sets clipboard to text, triggers Ctrl+V, then optionally restores original text."""
        original_text = self.get_text() if restore_clipboard else None

        if not self.set_text(text):
            return False

        if self.injector:
            self.injector.send_hotkey(["CTRL", "V"])
        else:
            # Fallback
            import win32api
            win32api.keybd_event(win32con.VK_CONTROL, 0, 0, 0)
            win32api.keybd_event(ord('V'), 0, 0, 0)
            win32api.keybd_event(ord('V'), 0, win32con.KEYEVENTF_KEYUP, 0)
            win32api.keybd_event(win32con.VK_CONTROL, 0, win32con.KEYEVENTF_KEYUP, 0)

        if restore_clipboard and original_text is not None:
            time.sleep(0.05)
            self.set_text(original_text)

        return True
