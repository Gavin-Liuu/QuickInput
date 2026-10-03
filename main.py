# -*- coding: utf-8 -*-
"""Main entry point for QuickInput (通用快捷输入工作台)."""

import os
import sys
import ctypes

from PyQt5 import QtCore, QtWidgets

from domain.action import Action
from domain.button import Button
from domain.layout import Layout
from domain.profile import Profile
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
from ui.floating_panel import FloatingPanel
from ui.tray_icon import SystemTrayIcon

SINGLE_INSTANCE_MUTEX_NAME = "Global\\QuickInput_App_SingleInstance_Mutex_v1"


def create_single_instance_mutex():
    kernel32 = ctypes.windll.kernel32
    mutex = kernel32.CreateMutexW(None, False, SINGLE_INSTANCE_MUTEX_NAME)
    last_error = kernel32.GetLastError()
    ERROR_ALREADY_EXISTS = 183
    if last_error == ERROR_ALREADY_EXISTS:
        return None
    return mutex


def load_default_packs(layout_mgr: LayoutManager, base_dir: str):
    packs_dir = os.path.join(base_dir, "packs")
    if not os.path.exists(packs_dir):
        return

    for pack_name in ["chess", "annotation", "customer_service", "programmer"]:
        p_dir = os.path.join(packs_dir, pack_name)
        if os.path.isdir(p_dir):
            ok, msg, data = PackStore.import_pack(p_dir)
            if ok:
                for a in data["actions"]:
                    layout_mgr.register_action(a)
                for b in data["buttons"]:
                    layout_mgr.register_button(b)
                for l in data["layouts"]:
                    layout_mgr.register_layout(l)


def populate_from_config(layout_mgr: LayoutManager, cfg: dict):
    # Actions
    for aid, a_dict in cfg.get("actions", {}).items():
        layout_mgr.register_action(Action.from_dict(a_dict))
    # Buttons
    for bid, b_dict in cfg.get("buttons", {}).items():
        layout_mgr.register_button(Button.from_dict(b_dict))
    # Layouts
    for lid, l_dict in cfg.get("layouts", {}).items():
        layout_mgr.register_layout(Layout.from_dict(l_dict))
    # Profiles
    for p_dict in cfg.get("profiles", []):
        layout_mgr.register_profile(Profile.from_dict(p_dict))

    active_id = cfg.get("active_layout_id", "")
    if active_id and active_id in layout_mgr.layouts:
        layout_mgr.set_active_layout(active_id)


def main():
    # 1. Single Instance Check
    mutex = create_single_instance_mutex()
    if not mutex:
        print("[QuickInput] Another instance of QuickInput is already running.")
        # If running in GUI, alert user
        if not QtWidgets.QApplication.instance():
            QtWidgets.QApplication(sys.argv)
        QtWidgets.QMessageBox.information(
            None, "提示", "通用快捷输入工作台已经在运行中！\n请查看右下角系统托盘或按 Alt+Q 呼出。"
        )
        sys.exit(0)

    # 2. DPI & High-res screen attributes
    QtWidgets.QApplication.setAttribute(QtCore.Qt.AA_EnableHighDpiScaling, True)
    QtWidgets.QApplication.setAttribute(QtCore.Qt.AA_UseHighDpiPixmaps, True)

    app = QtWidgets.QApplication(sys.argv)
    app.setApplicationName("QuickInput")
    app.setQuitOnLastWindowClosed(False)  # Keep running in system tray

    if getattr(sys, "frozen", False):
        exe_dir = os.path.dirname(sys.executable)
        base_dir = exe_dir if os.path.exists(os.path.join(exe_dir, "packs")) else getattr(sys, "_MEIPASS", exe_dir)
    else:
        base_dir = os.path.dirname(os.path.abspath(__file__))

    # 3. Platform & Core Services
    injector = WindowsInputInjector()
    window_mgr = WindowsWindowManager()
    clipboard_mgr = WindowsClipboardManager(injector=injector)
    target_mgr = TargetManager(window_manager=window_mgr)
    hotkey_mgr = WindowsGlobalHotkeyManager()
    executor = ActionExecutor(
        injector=injector,
        clipboard_mgr=clipboard_mgr,
        target_mgr=target_mgr,
    )
    config_store = ConfigStore()
    cfg = config_store.load_config()

    # 4. Layout Manager Initialization
    layout_mgr = LayoutManager()

    # First load built-in packs
    load_default_packs(layout_mgr, base_dir)

    # Then overlay user config if present
    populate_from_config(layout_mgr, cfg)

    # If active layout not set or not found, default to 'chess'
    if not layout_mgr.active_layout_id or layout_mgr.active_layout_id not in layout_mgr.layouts:
        if "chess" in layout_mgr.layouts:
            layout_mgr.set_active_layout("chess")

    # 5. Floating Panel UI
    panel = FloatingPanel(
        layout_mgr=layout_mgr,
        executor=executor,
        target_mgr=target_mgr,
        config_store=config_store,
        hotkey_mgr=hotkey_mgr,
    )
    window_mgr.set_self_hwnd(int(panel.winId()))
    panel.show()

    # 6. Global Hotkeys
    def toggle_visible():
        if panel.isVisible():
            panel.save_window_config()
            panel.hide()
        else:
            panel.showNormal()
            # The panel is intentionally non-activating; showing it must not
            # move the user's typing focus away from the target application.
            panel.raise_()

    hk_toggle = cfg.get("hotkeys", {}).get("toggle_visible", "ALT+Q")
    if hk_toggle:
        hotkey_mgr.register_hotkey(hk_toggle, toggle_visible)

    hk_stop = cfg.get("hotkeys", {}).get("emergency_stop", "ESC")
    # If emergency_stop has modifiers (e.g. CTRL+ALT+S), register it globally.
    # Bare keys like ESC are handled dynamically by FloatingPanel only while macros run.
    if hk_stop and ("+" in hk_stop):
        hotkey_mgr.register_named_hotkey("emergency_stop_permanent", hk_stop, executor.cancel_current)

    # 7. System Tray Icon
    def open_settings():
        panel.open_settings()

    def quit_app():
        executor.cancel_current()
        hotkey_mgr.unregister_all()
        panel._allow_close = True
        panel.save_window_config()
        panel.close()
        tray.hide()
        app.quit()

    tray = SystemTrayIcon(
        layout_mgr=layout_mgr,
        target_mgr=target_mgr,
        on_toggle_visible=toggle_visible,
        on_open_settings=open_settings,
        on_quit=quit_app,
    )
    tray.show()

    try:
        sys.exit(app.exec_())
    finally:
        executor.cancel_current()
        hotkey_mgr.unregister_all()
        if mutex:
            ctypes.windll.kernel32.CloseHandle(mutex)


if __name__ == "__main__":
    main()
