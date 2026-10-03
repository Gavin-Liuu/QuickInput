# -*- coding: utf-8 -*-
"""Windows Global Hotkey manager using RegisterHotKey and background message loop."""

import ctypes
from ctypes import wintypes
import threading
from typing import Dict, Callable, Optional, Tuple, Set
from ..base import BaseGlobalHotkeyManager

# Win32 Hotkey Modifiers
MOD_ALT = 0x0001
MOD_CONTROL = 0x0002
MOD_SHIFT = 0x0004
MOD_WIN = 0x0008
MOD_NOREPEAT = 0x4000

WM_HOTKEY = 0x0312
WM_QUIT = 0x0012

# Common virtual keys
VK_MAP = {
    "ESC": 0x1B,
    "ESCAPE": 0x1B,
    "SPACE": 0x20,
    "TAB": 0x09,
    "ENTER": 0x0D,
    "F1": 0x70, "F2": 0x71, "F3": 0x72, "F4": 0x73, "F5": 0x74, "F6": 0x75,
    "F7": 0x76, "F8": 0x77, "F9": 0x78, "F10": 0x79, "F11": 0x7A, "F12": 0x7B,
}
for i in range(ord('A'), ord('Z') + 1):
    VK_MAP[chr(i)] = i
for i in range(10):
    VK_MAP[str(i)] = 0x30 + i


# Add OEM punctuation and symbol keys
VK_MAP.update({
    ".": 0xBE, "PERIOD": 0xBE, "DOT": 0xBE,
    ",": 0xBC, "COMMA": 0xBC,
    "-": 0xBD, "MINUS": 0xBD,
    "=": 0xBB, "EQUAL": 0xBB, "PLUS": 0xBB,
    "/": 0xBF, "SLASH": 0xBF,
    ";": 0xBA, "SEMICOLON": 0xBA,
    "'": 0xDE, "QUOTE": 0xDE,
    "[": 0xDB, "LBRACKET": 0xDB,
    "]": 0xDD, "RBRACKET": 0xDD,
    "\\": 0xDC, "BACKSLASH": 0xDC,
    "`": 0xC0, "BACKQUOTE": 0xC0,
})

MSG_REGISTER_HOTKEY = 0x0400 + 1
MSG_UNREGISTER_HOTKEY = 0x0400 + 2


class WindowsGlobalHotkeyManager(BaseGlobalHotkeyManager):
    """Listens for global hotkeys in a dedicated thread using RegisterHotKey."""

    def __init__(self):
        self._user32 = ctypes.windll.user32
        self._thread: Optional[threading.Thread] = None
        self._thread_id: Optional[int] = None
        self._running = False
        self._callbacks: Dict[int, Callable[[], None]] = {}
        self._pending_regs: Dict[int, Tuple[int, int]] = {}
        self._pending_unregs: Set[int] = set()
        self._named_hotkeys: Dict[str, int] = {}
        self._next_id = 1
        self._lock = threading.Lock()

    def _parse_hotkey(self, hotkey_str: str) -> Tuple[int, int]:
        parts = [p.strip() for p in hotkey_str.split("+") if p.strip()]
        modifiers = MOD_NOREPEAT
        vk = 0
        for part in parts:
            up_part = part.upper()
            if up_part in ("CTRL", "CONTROL"):
                modifiers |= MOD_CONTROL
            elif up_part == "ALT":
                modifiers |= MOD_ALT
            elif up_part == "SHIFT":
                modifiers |= MOD_SHIFT
            elif up_part == "WIN":
                modifiers |= MOD_WIN
            elif up_part in VK_MAP:
                vk = VK_MAP[up_part]
            elif part in VK_MAP:
                vk = VK_MAP[part]
            elif len(part) == 1:
                if 'A' <= up_part <= 'Z' or '0' <= up_part <= '9':
                    vk = ord(up_part)
                else:
                    vk_scan = self._user32.VkKeyScanW(ord(part))
                    if vk_scan != -1 and vk_scan != 0xFFFF:
                        vk = vk_scan & 0xFF
                    else:
                        vk = ord(up_part)
        return modifiers, vk

    def register_hotkey(self, hotkey_str: str, callback: Callable[[], None]) -> int:
        modifiers, vk = self._parse_hotkey(hotkey_str)
        if vk == 0:
            return 0

        with self._lock:
            hotkey_id = self._next_id
            self._next_id += 1
            self._callbacks[hotkey_id] = callback
            self._pending_regs[hotkey_id] = (modifiers, vk)

        if not self._running:
            self._start_thread()
        else:
            if self._thread_id:
                self._user32.PostThreadMessageW(self._thread_id, MSG_REGISTER_HOTKEY, hotkey_id, 0)
        return hotkey_id

    def unregister_hotkey(self, hotkey_id: int) -> bool:
        with self._lock:
            if hotkey_id in self._callbacks:
                del self._callbacks[hotkey_id]
            if hotkey_id in self._pending_regs:
                del self._pending_regs[hotkey_id]
            self._pending_unregs.add(hotkey_id)

        if self._thread_id:
            self._user32.PostThreadMessageW(self._thread_id, MSG_UNREGISTER_HOTKEY, hotkey_id, 0)
        return True

    def register_named_hotkey(self, name: str, hotkey_str: str, callback: Callable[[], None]) -> int:
        self.unregister_named_hotkey(name)
        hid = self.register_hotkey(hotkey_str, callback)
        if hid:
            with self._lock:
                self._named_hotkeys[name] = hid
        return hid

    def unregister_named_hotkey(self, name: str) -> bool:
        with self._lock:
            hid = self._named_hotkeys.pop(name, None)
        if hid:
            return self.unregister_hotkey(hid)
        return False

    def _start_thread(self):
        self._running = True
        started_event = threading.Event()
        self._thread = threading.Thread(
            target=self._run_loop, args=(started_event,), daemon=True
        )
        self._thread.start()
        started_event.wait(timeout=1.0)

    def _run_loop(self, started_event: threading.Event):
        self._thread_id = ctypes.windll.kernel32.GetCurrentThreadId()

        # Force message queue creation before notifying starter
        msg = wintypes.MSG()
        self._user32.PeekMessageW(ctypes.byref(msg), None, 0, 0, 0)
        started_event.set()

        registered_ids: Set[int] = set()
        with self._lock:
            for hid, (mod, vk) in list(self._pending_regs.items()):
                if self._user32.RegisterHotKey(None, hid, mod, vk):
                    registered_ids.add(hid)

        while self._running:
            res = self._user32.GetMessageW(ctypes.byref(msg), None, 0, 0)
            if res <= 0:
                break

            if msg.message == WM_HOTKEY:
                hid = int(msg.wParam)
                cb = None
                with self._lock:
                    cb = self._callbacks.get(hid)
                if cb:
                    try:
                        cb()
                    except Exception:
                        pass
            elif msg.message == MSG_REGISTER_HOTKEY:
                with self._lock:
                    for hid, (mod, vk) in list(self._pending_regs.items()):
                        if hid not in registered_ids:
                            if self._user32.RegisterHotKey(None, hid, mod, vk):
                                registered_ids.add(hid)
            elif msg.message == MSG_UNREGISTER_HOTKEY:
                with self._lock:
                    unregs = list(self._pending_unregs)
                    self._pending_unregs.clear()
                for hid in unregs:
                    if hid in registered_ids:
                        self._user32.UnregisterHotKey(None, hid)
                        registered_ids.remove(hid)

            self._user32.TranslateMessage(ctypes.byref(msg))
            self._user32.DispatchMessageW(ctypes.byref(msg))

        # Cleanup
        for hid in registered_ids:
            try:
                self._user32.UnregisterHotKey(None, hid)
            except Exception:
                pass

    def unregister_all(self):
        self._running = False
        with self._lock:
            self._callbacks.clear()
            self._pending_regs.clear()
            self._pending_unregs.clear()
            self._named_hotkeys.clear()
        if self._thread_id:
            try:
                self._user32.PostThreadMessageW(self._thread_id, WM_QUIT, 0, 0)
            except Exception:
                pass
        self._thread = None
        self._thread_id = None
