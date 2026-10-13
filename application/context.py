# -*- coding: utf-8 -*-
"""Application context and dependency injection container for QuickInput."""

import os
from typing import Optional, Dict, Any

from PyQt5 import QtCore

from domain.action import Action
from domain.button import Button
from domain.layout import Layout
from domain.profile import Profile
from domain.i18n import set_current_language
from platform_layer.windows import (
    WindowsInputInjector,
    WindowsWindowManager,
    WindowsClipboardManager,
    WindowsGlobalHotkeyManager,
)
from application.target_manager import TargetManager
from application.action_executor import ActionExecutor
from application.layout_manager import LayoutManager
from storage.config_store import ConfigStore
from storage.pack_store import PackStore
from ui.qt_signals import HotkeySignalBridge


class AppContext:
    """Central application context encapsulating core services and lifecycle management."""

    def __init__(
        self,
        injector: Optional[WindowsInputInjector] = None,
        window_mgr: Optional[WindowsWindowManager] = None,
        clipboard_mgr: Optional[WindowsClipboardManager] = None,
        target_mgr: Optional[TargetManager] = None,
        hotkey_mgr: Optional[WindowsGlobalHotkeyManager] = None,
        executor: Optional[ActionExecutor] = None,
        config_store: Optional[ConfigStore] = None,
        layout_mgr: Optional[LayoutManager] = None,
        base_dir: str = "",
    ):
        self.base_dir = base_dir or os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        self.injector = injector or WindowsInputInjector()
        self.window_mgr = window_mgr or WindowsWindowManager()
        self.clipboard_mgr = clipboard_mgr or WindowsClipboardManager(injector=self.injector)
        self.target_mgr = target_mgr or TargetManager(window_manager=self.window_mgr)
        self.hotkey_mgr = hotkey_mgr or WindowsGlobalHotkeyManager()
        self.executor = executor or ActionExecutor(
            injector=self.injector,
            clipboard_mgr=self.clipboard_mgr,
            target_mgr=self.target_mgr,
        )
        self.config_store = config_store or ConfigStore()
        self.layout_mgr = layout_mgr or LayoutManager()
        self.hotkey_bridge = HotkeySignalBridge()
        self._panel = None

    @classmethod
    def create_default(cls, base_dir: str = "", config_dir: Optional[str] = None) -> "AppContext":
        """Factory method to assemble a fully wired production AppContext instance."""
        config_store = ConfigStore(config_dir=config_dir) if config_dir else ConfigStore()
        return cls(config_store=config_store, base_dir=base_dir)

    def load_default_packs(self, custom_packs_dir: Optional[str] = None):
        """Load built-in layout and button packs."""
        packs_dir = custom_packs_dir or os.path.join(self.base_dir, "packs")
        if not os.path.exists(packs_dir):
            return

        for pack_name in ["official_doc", "annotation", "customer_service", "programmer"]:
            p_dir = os.path.join(packs_dir, pack_name)
            if os.path.isdir(p_dir):
                ok, msg, data = PackStore.import_pack(p_dir)
                if ok:
                    for a in data["actions"]:
                        self.layout_mgr.register_action(a)
                    for b in data["buttons"]:
                        self.layout_mgr.register_button(b)
                    for l in data["layouts"]:
                        self.layout_mgr.register_layout(l)

    def populate_from_config(self, cfg: Optional[Dict[str, Any]] = None):
        """Overlay user config layouts, actions, buttons, and profiles."""
        if cfg is None:
            cfg = self.config_store.load_config()

        for aid, a_dict in cfg.get("actions", {}).items():
            self.layout_mgr.register_action(Action.from_dict(a_dict))
        for bid, b_dict in cfg.get("buttons", {}).items():
            self.layout_mgr.register_button(Button.from_dict(b_dict))
        for lid, l_dict in cfg.get("layouts", {}).items():
            self.layout_mgr.register_layout(Layout.from_dict(l_dict))
        for p_dict in cfg.get("profiles", []):
            self.layout_mgr.register_profile(Profile.from_dict(p_dict))

        active_id = cfg.get("active_layout_id", "")
        if active_id and active_id in self.layout_mgr.layouts:
            self.layout_mgr.set_active_layout(active_id)

    def initialize(self):
        """Perform end-to-end initialization of packs, config, and language."""
        cfg = self.config_store.load_config()
        self.load_default_packs()
        self.populate_from_config(cfg)

        # Initialize language
        app_lang = cfg.get("settings", {}).get("language", "zh")
        set_current_language(app_lang)

        # Ensure active layout
        if not self.layout_mgr.active_layout_id or self.layout_mgr.active_layout_id not in self.layout_mgr.layouts:
            if "word" in self.layout_mgr.layouts:
                self.layout_mgr.set_active_layout("word")
            elif self.layout_mgr.layouts:
                self.layout_mgr.set_active_layout(next(iter(self.layout_mgr.layouts.keys())))

        return cfg

    def register_toggle_hotkey(self, hotkey_str: str):
        """Thread-safe registration of the global show/hide toggle hotkey."""
        if not self.hotkey_mgr:
            return
        self.hotkey_mgr.unregister_named_hotkey("toggle_visible")
        if hotkey_str:
            self.hotkey_mgr.register_named_hotkey(
                "toggle_visible", hotkey_str, self.hotkey_bridge.toggle_requested.emit
            )

    def bind_panel(self, panel):
        """Bind floating panel to context and connect signals."""
        self._panel = panel
        self.hotkey_bridge.toggle_requested.connect(panel.toggle_visibility, QtCore.Qt.QueuedConnection)
        panel.set_toggle_hotkey_handler(self.register_toggle_hotkey)
        self.window_mgr.set_self_hwnd(int(panel.winId()))

    def cleanup(self):
        """Gracefully cancel running tasks, unregister hooks, and free resources."""
        if self.executor:
            self.executor.cancel_current()
        if self.hotkey_mgr:
            self.hotkey_mgr.unregister_all()
