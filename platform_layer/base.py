# -*- coding: utf-8 -*-
"""Base platform abstractions for input injection, window inspection, and clipboard."""

from abc import ABC, abstractmethod
from typing import Dict, Any, List, Optional, Callable


class BaseInputInjector(ABC):
    """Abstract interface for synthetic keyboard and mouse input."""

    @abstractmethod
    def send_text(self, text: str) -> bool:
        """Inject unicode text into target application without IME interference."""
        pass

    @abstractmethod
    def send_key(self, key_name: str, key_up: bool = False, key_down: bool = True) -> bool:
        """Send virtual key event."""
        pass

    @abstractmethod
    def send_key_press(self, key_name: str) -> bool:
        """Press and release a virtual key."""
        pass

    @abstractmethod
    def send_hotkey(self, keys: List[str]) -> bool:
        """Press a sequence of modifier keys, hit the main key, and release in reverse."""
        pass

    @abstractmethod
    def send_mouse(self, action: str = "click", x: Optional[int] = None, y: Optional[int] = None) -> bool:
        """Inject mouse events."""
        pass


class BaseWindowManager(ABC):
    """Abstract interface for inspecting and interacting with external windows."""

    @abstractmethod
    def get_foreground_window_handle(self) -> Any:
        """Get the native handle or identifier of the active foreground window."""
        pass

    @abstractmethod
    def get_window_info(self, handle: Any) -> Dict[str, Any]:
        """Return dict with title, process_name, pid, is_admin, is_valid."""
        pass

    @abstractmethod
    def is_window_valid(self, handle: Any) -> bool:
        """Check if the given window handle still exists."""
        pass

    @abstractmethod
    def set_foreground_safe(self, handle: Any) -> bool:
        """Safely restore or bring window to foreground without seizing focus aggressively."""
        pass

    @abstractmethod
    def is_target_elevated(self, handle: Any) -> bool:
        """Detect if target window is running with Administrator/root privileges."""
        pass


class BaseClipboardManager(ABC):
    """Abstract interface for clipboard access and restoration."""

    @abstractmethod
    def get_text(self) -> str:
        pass

    @abstractmethod
    def set_text(self, text: str) -> bool:
        pass

    @abstractmethod
    def paste_text(self, text: str, restore_clipboard: bool = True) -> bool:
        """Copy text to clipboard, trigger paste hotkey, and optionally restore prior clipboard."""
        pass


class BaseGlobalHotkeyManager(ABC):
    """Abstract interface for system-wide hotkeys."""

    @abstractmethod
    def register_hotkey(self, hotkey_str: str, callback: Callable[[], None]) -> bool:
        pass

    @abstractmethod
    def unregister_all(self):
        pass
