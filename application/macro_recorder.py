# -*- coding: utf-8 -*-
"""Macro Recorder for capturing user keystrokes, shortcuts, and text."""

import os
import ctypes
from ctypes import wintypes
import threading
import time
from typing import List, Optional, Callable, Set
from domain.action import ActionStep

WH_KEYBOARD_LL = 13
WM_KEYDOWN = 0x0100
WM_KEYUP = 0x0101
WM_SYSKEYDOWN = 0x0104
WM_SYSKEYUP = 0x0105
WM_QUIT = 0x0012

ULONG_PTR = ctypes.c_ulong if ctypes.sizeof(ctypes.c_void_p) == 4 else ctypes.c_ulonglong


class KBDLLHOOKSTRUCT(ctypes.Structure):
    _fields_ = [
        ("vkCode", wintypes.DWORD),
        ("scanCode", wintypes.DWORD),
        ("flags", wintypes.DWORD),
        ("time", wintypes.DWORD),
        ("dwExtraInfo", ULONG_PTR),
    ]


SPECIAL_VKS = {
    0x0D: "ENTER",
    0x09: "TAB",
    0x1B: "ESC",
    0x20: "SPACE",
    0x08: "BACKSPACE",
    0x2E: "DELETE",
    0x2D: "INSERT",
    0x24: "HOME",
    0x23: "END",
    0x21: "PAGEUP",
    0x22: "PAGEDOWN",
    0x25: "LEFT",
    0x26: "UP",
    0x27: "RIGHT",
    0x28: "DOWN",
    0x70: "F1", 0x71: "F2", 0x72: "F3", 0x73: "F4",
    0x74: "F5", 0x75: "F6", 0x76: "F7", 0x77: "F8",
    0x78: "F9", 0x79: "F10", 0x7A: "F11", 0x7B: "F12",
}

MODIFIER_VKS = {
    0x11: "CTRL", 0xA2: "CTRL", 0xA3: "CTRL",
    0x10: "SHIFT", 0xA0: "SHIFT", 0xA1: "SHIFT",
    0x12: "ALT", 0xA4: "ALT", 0xA5: "ALT",
    0x5B: "WIN", 0x5C: "WIN",
}

MOD_ORDER = {"CTRL": 1, "ALT": 2, "SHIFT": 3, "WIN": 4}


class MacroRecorder:
    """Records keystrokes into clean ActionStep sequences with strict target filtering."""

    def __init__(
        self,
        record_delays: bool = True,
        min_delay_ms: int = 150,
        max_delay_ms: int = 5000,
        record_auto_repeat: bool = False,
        own_hwnds: Optional[List[int]] = None,
    ):
        self.record_delays = record_delays
        self.min_delay_ms = min_delay_ms
        self.max_delay_ms = max_delay_ms
        self.record_auto_repeat = record_auto_repeat
        self.own_hwnds: Set[int] = set(own_hwnds or [])
        self.own_pid: int = os.getpid()

        # Target filtering
        self.target_hwnd: Optional[int] = None
        self.target_pid: Optional[int] = None
        self.target_process_name: str = ""
        self.target_title: str = ""
        self.allow_same_process: bool = True
        self.is_target_in_focus: bool = True

        self.is_recording = False
        self.is_paused = False
        self.steps: List[ActionStep] = []
        self._lock = threading.Lock()

        self._active_modifiers: Set[str] = set()
        self._currently_down_vks: Set[int] = set()
        self._last_down_vk: Optional[int] = None
        self._last_event_time: Optional[float] = None
        self._hook_thread: Optional[threading.Thread] = None
        self._hook_thread_id: Optional[int] = None
        self._hook_handle = None
        self._hook_proc = None  # keep reference to prevent GC

        # Callbacks
        self.on_step_recorded: Optional[Callable[[ActionStep], None]] = None
        self.on_target_lost: Optional[Callable[[], None]] = None
        self.on_target_regained: Optional[Callable[[], None]] = None

    def register_own_hwnd(self, hwnd: int):
        if hwnd:
            self.own_hwnds.add(int(hwnd))

    def set_target(
        self,
        hwnd: Optional[int],
        pid: Optional[int] = None,
        process_name: str = "",
        title: str = "",
    ):
        """Set the target window to restrict keystroke recording."""
        self.target_hwnd = int(hwnd) if hwnd else None
        self.target_pid = int(pid) if pid else None
        self.target_process_name = process_name
        self.target_title = title
        if self.target_hwnd and not self.target_pid:
            try:
                target_pid = wintypes.DWORD()
                ctypes.windll.user32.GetWindowThreadProcessId(self.target_hwnd, ctypes.byref(target_pid))
                self.target_pid = target_pid.value
            except Exception:
                pass

    def start(self):
        """Start capturing keyboard events."""
        with self._lock:
            self.steps = []
            self.is_recording = True
            self.is_paused = False
            self.is_target_in_focus = True
            self._active_modifiers.clear()
            self._currently_down_vks.clear()
            self._last_down_vk = None
            self._last_event_time = time.time()

        self._start_hook()

    def pause(self):
        """Pause recording without clearing existing steps, resetting modifier state."""
        with self._lock:
            self.is_paused = True
            self._active_modifiers.clear()
            self._currently_down_vks.clear()
            self._last_down_vk = None

    def resume(self):
        """Resume recording with reset modifier state."""
        with self._lock:
            self._last_event_time = time.time()
            self._active_modifiers.clear()
            self._currently_down_vks.clear()
            self._last_down_vk = None
            self.is_paused = False

    def cancel(self):
        """Cancel recording and discard steps."""
        self.stop()
        with self._lock:
            self.steps = []

    def stop(self) -> List[ActionStep]:
        """Stop recording and return captured steps, freeing all hook resources."""
        self._stop_hook()
        with self._lock:
            self.is_recording = False
            self.is_paused = False
            self._active_modifiers.clear()
            self._currently_down_vks.clear()
            return list(self.steps)

    def get_steps(self) -> List[ActionStep]:
        """Thread-safe snapshot of currently recorded steps."""
        with self._lock:
            return list(self.steps)

    def add_text_step(self, text: str, as_paste: bool = False):
        """Direct text capture mode without physical typing quirks."""
        with self._lock:
            step = ActionStep(type="paste" if as_paste else "text", value=text)
            self.steps.append(step)
            if self.on_step_recorded:
                self.on_step_recorded(step)

    def _start_hook(self):
        if self._hook_thread and self._hook_thread.is_alive():
            return

        ready_event = threading.Event()
        self._hook_thread = threading.Thread(
            target=self._hook_worker, args=(ready_event,), daemon=True
        )
        self._hook_thread.start()
        ready_event.wait(timeout=1.0)

    def _stop_hook(self):
        if self._hook_thread_id:
            try:
                ctypes.windll.user32.PostThreadMessageW(self._hook_thread_id, WM_QUIT, 0, 0)
            except Exception:
                pass
        if self._hook_thread:
            self._hook_thread.join(timeout=1.0)
            self._hook_thread = None
            self._hook_thread_id = None
        if self._hook_handle:
            try:
                ctypes.windll.user32.UnhookWindowsHookEx(self._hook_handle)
            except Exception:
                pass
            self._hook_handle = None
        self._hook_proc = None

    def _hook_worker(self, ready_event: threading.Event):
        self._hook_thread_id = ctypes.windll.kernel32.GetCurrentThreadId()

        user32 = ctypes.windll.user32
        user32.SetWindowsHookExW.argtypes = [ctypes.c_int, ctypes.c_void_p, wintypes.HINSTANCE, wintypes.DWORD]
        user32.SetWindowsHookExW.restype = wintypes.HHOOK

        user32.CallNextHookEx.argtypes = [wintypes.HHOOK, ctypes.c_int, wintypes.WPARAM, wintypes.LPARAM]
        user32.CallNextHookEx.restype = ctypes.c_longlong

        user32.UnhookWindowsHookEx.argtypes = [wintypes.HHOOK]
        user32.UnhookWindowsHookEx.restype = wintypes.BOOL

        kernel32 = ctypes.windll.kernel32
        kernel32.GetModuleHandleW.argtypes = [wintypes.LPCWSTR]
        kernel32.GetModuleHandleW.restype = wintypes.HMODULE
        hmod = kernel32.GetModuleHandleW(None)

        HOOKPROC = ctypes.WINFUNCTYPE(
            ctypes.c_longlong, ctypes.c_int, wintypes.WPARAM, wintypes.LPARAM
        )

        def low_level_handler(nCode, wParam, lParam):
            if nCode >= 0:
                self._handle_raw_event(int(wParam), lParam)
            return user32.CallNextHookEx(self._hook_handle, nCode, wParam, lParam)

        self._hook_proc = HOOKPROC(low_level_handler)
        self._hook_handle = user32.SetWindowsHookExW(
            WH_KEYBOARD_LL,
            self._hook_proc,
            hmod,
            0,
        )

        # Force message queue creation
        msg = wintypes.MSG()
        user32.PeekMessageW(ctypes.byref(msg), None, 0, 0, 0)
        ready_event.set()

        while user32.GetMessageW(ctypes.byref(msg), None, 0, 0) > 0:
            user32.TranslateMessage(ctypes.byref(msg))
            user32.DispatchMessageW(ctypes.byref(msg))

        if self._hook_handle:
            user32.UnhookWindowsHookEx(self._hook_handle)
            self._hook_handle = None
        self._hook_proc = None

    def _should_capture_foreground(self, current_fg: Optional[int] = None) -> bool:
        """Verify whether foreground window matches recording target and excludes own windows."""
        try:
            fg = current_fg if current_fg is not None else ctypes.windll.user32.GetForegroundWindow()
        except Exception:
            fg = None

        if not fg:
            return False

        try:
            fg_pid = wintypes.DWORD()
            ctypes.windll.user32.GetWindowThreadProcessId(fg, ctypes.byref(fg_pid))
            pid_val = fg_pid.value
        except Exception:
            pid_val = None

        is_own = bool((fg in self.own_hwnds) or (pid_val and pid_val == self.own_pid))

        # Check target window requirement
        if self.target_hwnd:
            is_target_hwnd = (fg == self.target_hwnd)
            is_target_proc = bool(
                self.allow_same_process and self.target_pid and pid_val and pid_val == self.target_pid
            )
            is_valid_target = (is_target_hwnd or is_target_proc) and not is_own
            if not is_valid_target:
                if self.is_target_in_focus:
                    self.is_target_in_focus = False
                    if self.on_target_lost:
                        try:
                            self.on_target_lost()
                        except Exception:
                            pass
                return False
            else:
                if not self.is_target_in_focus:
                    self.is_target_in_focus = True
                    if self.on_target_regained:
                        try:
                            self.on_target_regained()
                        except Exception:
                            pass
                return True
        else:
            return not is_own

    def _handle_raw_event(self, msg_type: int, lparam: int):
        if not self.is_recording or self.is_paused:
            return

        if not self._should_capture_foreground():
            return

        kb = KBDLLHOOKSTRUCT.from_address(lparam)
        vk = kb.vkCode

        # Filter injected events
        if kb.flags & 0x10:
            return

        is_down = msg_type in (WM_KEYDOWN, WM_SYSKEYDOWN)
        is_up = msg_type in (WM_KEYUP, WM_SYSKEYUP)

        if vk in MODIFIER_VKS:
            mod_name = MODIFIER_VKS[vk]
            if is_down:
                self._active_modifiers.add(mod_name)
            elif is_up:
                self._active_modifiers.discard(mod_name)
            return

        if is_up:
            if vk == self._last_down_vk:
                self._last_down_vk = None
            self._currently_down_vks.discard(vk)
            return

        if is_down:
            # Auto-repeat filtering: only the most recently pressed down key can repeat
            if vk == self._last_down_vk and vk in self._currently_down_vks:
                if not self.record_auto_repeat:
                    return
            self._last_down_vk = vk
            self._currently_down_vks.add(vk)

            self._process_key_press(vk)

    def _process_key_press(self, vk: int):
        now = time.time()
        with self._lock:
            # Check delay
            if self.record_delays and self._last_event_time:
                delta_ms = int((now - self._last_event_time) * 1000)
                if delta_ms >= self.min_delay_ms:
                    delay_step = ActionStep(type="delay", ms=min(delta_ms, self.max_delay_ms))
                    self.steps.append(delay_step)
                    if self.on_step_recorded:
                        self.on_step_recorded(delay_step)

            self._last_event_time = now

            # If Ctrl, Alt, or Win is active -> hotkey
            non_shift_mods = self._active_modifiers - {"SHIFT"}
            if non_shift_mods:
                key_name = self._get_key_symbol(vk)
                sorted_mods = sorted(list(self._active_modifiers), key=lambda m: MOD_ORDER.get(m, 99))
                hotkey_str = "+".join(sorted_mods + [key_name])
                step = ActionStep(type="hotkey", hotkey=hotkey_str, keys=sorted_mods + [key_name])
                self.steps.append(step)
                if self.on_step_recorded:
                    self.on_step_recorded(step)
                return

            # If only Shift is active
            if "SHIFT" in self._active_modifiers:
                # If special non-printable key, it's a hotkey (e.g. SHIFT+TAB, SHIFT+ENTER, SHIFT+F3)
                if vk in SPECIAL_VKS and SPECIAL_VKS[vk] != "SPACE":
                    key_name = SPECIAL_VKS[vk]
                    hotkey_str = f"SHIFT+{key_name}"
                    step = ActionStep(type="hotkey", hotkey=hotkey_str, keys=["SHIFT", key_name])
                    self.steps.append(step)
                    if self.on_step_recorded:
                        self.on_step_recorded(step)
                    return

                # Otherwise printable character with Shift (e.g. 'A', '!', etc.)
                ch = self._vk_to_char_win32(vk, shift=True)
                if ch:
                    self._append_character(ch)
                return

            # Special keys without modifiers
            if vk in SPECIAL_VKS:
                key_name = SPECIAL_VKS[vk]
                if key_name == "SPACE":
                    self._append_character(" ")
                else:
                    step = ActionStep(type="key", key=key_name)
                    self.steps.append(step)
                    if self.on_step_recorded:
                        self.on_step_recorded(step)
                return

            # Printable characters without modifiers
            ch = self._vk_to_char_win32(vk, shift=False)
            if ch:
                self._append_character(ch)

    def _get_key_symbol(self, vk: int) -> str:
        if vk in SPECIAL_VKS:
            return SPECIAL_VKS[vk]
        if 0x41 <= vk <= 0x5A:  # A-Z
            return chr(vk)
        if 0x30 <= vk <= 0x39:  # 0-9
            return chr(vk)
        ch = self._vk_to_char_fallback(vk, shift=False)
        if ch:
            return ch.upper()
        return f"VK_{vk}"

    def _append_character(self, ch: str):
        # Auto-merge continuous characters into single text step
        if self.steps and self.steps[-1].type == "text":
            self.steps[-1].value += ch
            if self.on_step_recorded:
                self.on_step_recorded(self.steps[-1])
        else:
            step = ActionStep(type="text", value=ch)
            self.steps.append(step)
            if self.on_step_recorded:
                self.on_step_recorded(step)

    def _vk_to_char_win32(self, vk: int, shift: bool) -> Optional[str]:
        """Convert VK code to character using active window keyboard layout and scan code."""
        try:
            user32 = ctypes.windll.user32
            fg = user32.GetForegroundWindow()
            tid = user32.GetWindowThreadProcessId(fg, None) if fg else 0
            hkl = user32.GetKeyboardLayout(tid) if tid else user32.GetKeyboardLayout(0)

            state = (ctypes.c_ubyte * 256)()
            if shift:
                state[0x10] = 0x80  # VK_SHIFT
            if "CTRL" in self._active_modifiers:
                state[0x11] = 0x80
            if "ALT" in self._active_modifiers:
                state[0x12] = 0x80

            sc = user32.MapVirtualKeyExW(vk, 0, hkl)
            buf = ctypes.create_unicode_buffer(16)
            res = user32.ToUnicodeEx(vk, sc, state, buf, len(buf), 0, hkl)
            if res > 0 and buf.value:
                return buf.value[:res]
        except Exception:
            pass
        return self._vk_to_char_fallback(vk, shift)

    def _vk_to_char_fallback(self, vk: int, shift: bool) -> Optional[str]:
        if 0x41 <= vk <= 0x5A:  # A-Z
            c = chr(vk)
            return c if shift else c.lower()
        if 0x30 <= vk <= 0x39:  # 0-9
            shifted_digits = ")!@#$%^&*("
            digit = chr(vk)
            return shifted_digits[int(digit)] if shift else digit

        oem_map = {
            186: (";", ":"),
            187: ("=", "+"),
            188: (",", "<"),
            189: ("-", "_"),
            190: (".", ">"),
            191: ("/", "?"),
            192: ("`", "~"),
            219: ("[", "{"),
            220: ("\\", "|"),
            221: ("]", "}"),
            222: ("'", '"'),
        }
        if vk in oem_map:
            normal, shifted = oem_map[vk]
            return shifted if shift else normal

        return None

    def simulate_record_key(
        self,
        vk: int,
        modifiers: Optional[List[str]] = None,
        is_down: bool = True,
        fg_hwnd: Optional[int] = None,
    ):
        """Simulation helper for unit tests."""
        if not self.is_recording or self.is_paused:
            return

        sim_fg = fg_hwnd
        if sim_fg is None:
            sim_fg = self.target_hwnd if self.target_hwnd is not None else 99999999

        if not self._should_capture_foreground(sim_fg):
            return

        if vk in MODIFIER_VKS:
            mod_name = MODIFIER_VKS[vk]
            if is_down:
                self._active_modifiers.add(mod_name)
            else:
                self._active_modifiers.discard(mod_name)
            return

        if modifiers is not None:
            self._active_modifiers = set(modifiers)

        if not is_down:
            if vk == self._last_down_vk:
                self._last_down_vk = None
            self._currently_down_vks.discard(vk)
            return

        if vk == self._last_down_vk and vk in self._currently_down_vks:
            if not self.record_auto_repeat:
                return
        self._last_down_vk = vk
        self._currently_down_vks.add(vk)

        self._process_key_press(vk)
