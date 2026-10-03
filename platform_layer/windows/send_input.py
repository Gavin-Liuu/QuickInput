# -*- coding: utf-8 -*-
"""Windows SendInput implementation replacing obsolete keybd_event."""

import ctypes
from ctypes import wintypes
import time
from typing import List, Optional, Dict
from ..base import BaseInputInjector

# Win32 SendInput constants
INPUT_MOUSE = 0
INPUT_KEYBOARD = 1
INPUT_HARDWARE = 2

KEYEVENTF_EXTENDEDKEY = 0x0001
KEYEVENTF_KEYUP = 0x0002
KEYEVENTF_UNICODE = 0x0004
KEYEVENTF_SCANCODE = 0x0008

MOUSEEVENTF_MOVE = 0x0001
MOUSEEVENTF_LEFTDOWN = 0x0002
MOUSEEVENTF_LEFTUP = 0x0004
MOUSEEVENTF_RIGHTDOWN = 0x0008
MOUSEEVENTF_RIGHTUP = 0x0010
MOUSEEVENTF_MIDDLEDOWN = 0x0020
MOUSEEVENTF_MIDDLEUP = 0x0040
MOUSEEVENTF_ABSOLUTE = 0x8000

# Virtual key map
VK_MAP: Dict[str, int] = {
    "ENTER": 0x0D,
    "RETURN": 0x0D,
    "TAB": 0x09,
    "SPACE": 0x20,
    "BACKSPACE": 0x08,
    "BS": 0x08,
    "DELETE": 0x2E,
    "DEL": 0x2E,
    "INSERT": 0x2D,
    "INS": 0x2D,
    "ESC": 0x1B,
    "ESCAPE": 0x1B,
    "UP": 0x26,
    "DOWN": 0x28,
    "LEFT": 0x25,
    "RIGHT": 0x27,
    "PAGEUP": 0x21,
    "PAGEDOWN": 0x22,
    "HOME": 0x24,
    "END": 0x23,
    "CTRL": 0x11,
    "CONTROL": 0x11,
    "LCTRL": 0xA2,
    "RCTRL": 0xA3,
    "SHIFT": 0x10,
    "LSHIFT": 0xA0,
    "RSHIFT": 0xA1,
    "ALT": 0x12,
    "LALT": 0xA4,
    "RALT": 0xA5,
    "WIN": 0x5B,
    "LWIN": 0x5B,
    "RWIN": 0x5C,
    "CAPSLOCK": 0x14,
    "NUMLOCK": 0x90,
    "SCROLLLOCK": 0x91,
    "PRINTSCREEN": 0x2C,
    "PAUSE": 0x13,
}

# Add F1-F12
for i in range(1, 13):
    VK_MAP[f"F{i}"] = 0x70 + (i - 1)

# Add 0-9
for i in range(10):
    VK_MAP[str(i)] = 0x30 + i

# Add A-Z
for ch in range(ord('A'), ord('Z') + 1):
    VK_MAP[chr(ch)] = ch

# Standard OEM punctuation and symbol keys
OEM_KEYS = {
    ".": 0xBE, "PERIOD": 0xBE, "DOT": 0xBE,
    ",": 0xBC, "COMMA": 0xBC,
    "-": 0xBD, "MINUS": 0xBD, "HYPHEN": 0xBD,
    "=": 0xBB, "EQUAL": 0xBB, "EQUALS": 0xBB, "PLUS": 0xBB,
    "/": 0xBF, "SLASH": 0xBF,
    ";": 0xBA, "SEMICOLON": 0xBA,
    "'": 0xDE, "QUOTE": 0xDE,
    "[": 0xDB, "LBRACKET": 0xDB,
    "]": 0xDD, "RBRACKET": 0xDD,
    "\\": 0xDC, "BACKSLASH": 0xDC,
    "`": 0xC0, "BACKQUOTE": 0xC0, "TILDE": 0xC0,
}
VK_MAP.update(OEM_KEYS)

EXTENDED_KEYS = {
    0x26, 0x28, 0x25, 0x27,  # UP, DOWN, LEFT, RIGHT
    0x24, 0x23, 0x21, 0x22,  # HOME, END, PAGEUP, PAGEDOWN
    0x2D, 0x2E,              # INSERT, DELETE
    0xA3, 0xA5,              # RCTRL, RALT
}


# Ctypes structures for SendInput
ULONG_PTR = ctypes.c_ulong if ctypes.sizeof(ctypes.c_void_p) == 4 else ctypes.c_ulonglong

class MOUSEINPUT(ctypes.Structure):
    _fields_ = [
        ("dx", wintypes.LONG),
        ("dy", wintypes.LONG),
        ("mouseData", wintypes.DWORD),
        ("dwFlags", wintypes.DWORD),
        ("time", wintypes.DWORD),
        ("dwExtraInfo", ULONG_PTR),
    ]

class KEYBDINPUT(ctypes.Structure):
    _fields_ = [
        ("wVk", wintypes.WORD),
        ("wScan", wintypes.WORD),
        ("dwFlags", wintypes.DWORD),
        ("time", wintypes.DWORD),
        ("dwExtraInfo", ULONG_PTR),
    ]

class HARDWAREINPUT(ctypes.Structure):
    _fields_ = [
        ("uMsg", wintypes.DWORD),
        ("wParamL", wintypes.WORD),
        ("wParamH", wintypes.WORD),
    ]

class _INPUT_UNION(ctypes.Union):
    _fields_ = [
        ("mi", MOUSEINPUT),
        ("ki", KEYBDINPUT),
        ("hi", HARDWAREINPUT),
    ]

class INPUT(ctypes.Structure):
    _anonymous_ = ("_union",)
    _fields_ = [
        ("type", wintypes.DWORD),
        ("_union", _INPUT_UNION),
    ]


class WindowsInputInjector(BaseInputInjector):
    """Windows input injector powered by Win32 SendInput."""

    def __init__(self, key_delay_sec: float = 0.005):
        self.key_delay_sec = key_delay_sec
        self._user32 = ctypes.windll.user32
        self._user32.SendInput.argtypes = [
            wintypes.UINT,
            ctypes.POINTER(INPUT),
            ctypes.c_int
        ]
        self._user32.SendInput.restype = wintypes.UINT

    def _send_inputs(self, inputs: List[INPUT]) -> bool:
        if not inputs:
            return True
        n = len(inputs)
        arr = (INPUT * n)(*inputs)
        res = self._user32.SendInput(n, arr, ctypes.sizeof(INPUT))
        return res == n

    def _make_key_input(self, vk: int = 0, scan: int = 0, flags: int = 0) -> INPUT:
        inp = INPUT()
        inp.type = INPUT_KEYBOARD
        inp.ki.wVk = vk
        inp.ki.wScan = scan
        inp.ki.dwFlags = flags
        inp.ki.time = 0
        inp.ki.dwExtraInfo = 0
        return inp

    def send_text(self, text: str) -> bool:
        """Inject unicode text directly via KEYEVENTF_UNICODE to bypass IME."""
        if not text:
            return True
        
        inputs = []
        for ch in text:
            # Handle unicode surrogate pairs if ord > 0xFFFF
            code = ord(ch)
            if code > 0xFFFF:
                # UTF-16 surrogate pair
                code -= 0x10000
                lead = 0xD800 + (code >> 10)
                trail = 0xDC00 + (code & 0x3FF)
                inputs.append(self._make_key_input(0, lead, KEYEVENTF_UNICODE))
                inputs.append(self._make_key_input(0, lead, KEYEVENTF_UNICODE | KEYEVENTF_KEYUP))
                inputs.append(self._make_key_input(0, trail, KEYEVENTF_UNICODE))
                inputs.append(self._make_key_input(0, trail, KEYEVENTF_UNICODE | KEYEVENTF_KEYUP))
            else:
                inputs.append(self._make_key_input(0, code, KEYEVENTF_UNICODE))
                inputs.append(self._make_key_input(0, code, KEYEVENTF_UNICODE | KEYEVENTF_KEYUP))

        return self._send_inputs(inputs)

    def _resolve_vk(self, key_name: str) -> Optional[int]:
        raw = key_name.strip()
        normalized = raw.upper()
        if raw in VK_MAP:
            return VK_MAP[raw]
        if normalized in VK_MAP:
            return VK_MAP[normalized]
        if len(raw) == 1:
            if 'A' <= normalized <= 'Z' or '0' <= normalized <= '9':
                return ord(normalized)
            # Query Windows VkKeyScanW for proper virtual key code of punctuation/symbol
            vk_scan = self._user32.VkKeyScanW(ord(raw))
            if vk_scan != -1 and vk_scan != 0xFFFF:
                return vk_scan & 0xFF
        return None

    def send_key(self, key_name: str, key_up: bool = False, key_down: bool = True) -> bool:
        vk = self._resolve_vk(key_name)
        if vk is None:
            # Fallback to sending as text
            if key_down and not key_up:
                return self.send_text(key_name)
            return True

        inputs = []
        flags = KEYEVENTF_EXTENDEDKEY if vk in EXTENDED_KEYS else 0

        if key_down:
            inputs.append(self._make_key_input(vk, 0, flags))
        if key_up:
            inputs.append(self._make_key_input(vk, 0, flags | KEYEVENTF_KEYUP))

        return self._send_inputs(inputs)

    def send_key_press(self, key_name: str) -> bool:
        vk = self._resolve_vk(key_name)
        if vk is None:
            return self.send_text(key_name)

        flags = KEYEVENTF_EXTENDEDKEY if vk in EXTENDED_KEYS else 0
        down = self._make_key_input(vk, 0, flags)
        up = self._make_key_input(vk, 0, flags | KEYEVENTF_KEYUP)
        return self._send_inputs([down, up])

    def send_hotkey(self, keys: List[str]) -> bool:
        """Press modifier keys, press main key, release in reverse order."""
        if not keys:
            return True

        vks = [self._resolve_vk(k) for k in keys]
        if any(vk is None for vk in vks):
            # Fallback
            return False

        down_inputs = []
        up_inputs = []
        for vk in vks:
            flags = KEYEVENTF_EXTENDEDKEY if vk in EXTENDED_KEYS else 0
            down_inputs.append(self._make_key_input(vk, 0, flags))
        for vk in reversed(vks):
            flags = KEYEVENTF_EXTENDEDKEY if vk in EXTENDED_KEYS else 0
            up_inputs.append(self._make_key_input(vk, 0, flags | KEYEVENTF_KEYUP))

        if self.key_delay_sec > 0:
            if not self._send_inputs(down_inputs):
                return False
            time.sleep(self.key_delay_sec)
            return self._send_inputs(up_inputs)
        return self._send_inputs(down_inputs + up_inputs)

    def send_mouse(self, action: str = "click", x: Optional[int] = None, y: Optional[int] = None) -> bool:
        inputs = []
        if x is not None and y is not None:
            # Normalized screen coords (0 to 65535)
            sm_cx = self._user32.GetSystemMetrics(0)  # SM_CXSCREEN
            sm_cy = self._user32.GetSystemMetrics(1)  # SM_CYSCREEN
            if sm_cx > 0 and sm_cy > 0:
                norm_x = int(x * 65535 / sm_cx)
                norm_y = int(y * 65535 / sm_cy)
                inp = INPUT()
                inp.type = INPUT_MOUSE
                inp.mi.dx = norm_x
                inp.mi.dy = norm_y
                inp.mi.dwFlags = MOUSEEVENTF_MOVE | MOUSEEVENTF_ABSOLUTE
                inputs.append(inp)

        act = action.lower()
        if act == "click":
            down = INPUT(type=INPUT_MOUSE)
            down.mi.dwFlags = MOUSEEVENTF_LEFTDOWN
            up = INPUT(type=INPUT_MOUSE)
            up.mi.dwFlags = MOUSEEVENTF_LEFTUP
            inputs.extend([down, up])
        elif act == "rclick":
            down = INPUT(type=INPUT_MOUSE)
            down.mi.dwFlags = MOUSEEVENTF_RIGHTDOWN
            up = INPUT(type=INPUT_MOUSE)
            up.mi.dwFlags = MOUSEEVENTF_RIGHTUP
            inputs.extend([down, up])
        elif act == "dblclick":
            for _ in range(2):
                down = INPUT(type=INPUT_MOUSE)
                down.mi.dwFlags = MOUSEEVENTF_LEFTDOWN
                up = INPUT(type=INPUT_MOUSE)
                up.mi.dwFlags = MOUSEEVENTF_LEFTUP
                inputs.extend([down, up])

        return self._send_inputs(inputs)
