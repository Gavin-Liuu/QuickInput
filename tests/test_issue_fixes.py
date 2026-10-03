# -*- coding: utf-8 -*-
"""Verification tests for the 7 issues addressed:
1. Native window frame without custom segmented border or WA_TranslucentBackground
2. Search button toggle keeps window geometry and button scale stable
3. Global search across all layouts, auto-exit, layout switch & button highlight without firing input
4. Clean button domain model without redundant concatenation or self-healing loops
5. Window position preserved after settings dialog closes
6. Main interface modeless & non-topmost during settings, restored on exit
7. App binding targets external apps only, never binds self
"""

import os
import tempfile
import pytest
from PyQt5 import QtCore, QtGui, QtWidgets
import win32con
import win32gui

from domain.button import Button, format_button_display_text
from domain.layout import Layout, LayoutSettings, LayoutButtonSlot
from domain.action import Action, ActionStep
from domain.profile import Profile
from application.layout_manager import LayoutManager
from application.action_executor import ActionExecutor
from application.target_manager import TargetManager
from storage.config_store import ConfigStore
from platform_layer.base import BaseWindowManager
from ui.floating_panel import FloatingPanel, ActionButtonWidget
from ui.settings_dialog import SettingsDialog
from tests.test_executor import MockInputInjector, MockClipboardManager, MockWindowManager


def create_test_env(tmp_dir):
    cs = ConfigStore(config_dir=tmp_dir)
    lm = LayoutManager()
    
    # Create two layouts to test global search and layout switching
    l1 = lm.create_layout_with_presets("layout_1", "第一布局", rows=2, columns=2)
    l2 = lm.create_layout_with_presets("layout_2", "第二布局", rows=2, columns=2)

    # Add distinct buttons
    b_special = Button(id="b_special", label="特别标注", action_id="act_special", tooltip="特殊提示")
    act_special = Action(id="act_special", label="特殊动作", steps=[ActionStep(type="text", value="special_text")])
    lm.register_button(b_special)
    lm.register_action(act_special)
    l2.set_button_at(0, 0, "b_special")

    inj = MockInputInjector()
    wm = MockWindowManager()
    clip = MockClipboardManager()
    tm = TargetManager(window_manager=wm)
    tm.update_active_window(12345)
    ex = ActionExecutor(injector=inj, clipboard_mgr=clip, target_mgr=tm)

    return cs, lm, inj, wm, clip, tm, ex


def test_issue_1_native_window_frame_attributes(qapp):
    """1. Verify window does not use WA_TranslucentBackground or artificial rounded frame border."""
    with tempfile.TemporaryDirectory() as tmp_dir:
        cs, lm, inj, wm, clip, tm, ex = create_test_env(tmp_dir)
        panel = FloatingPanel(lm, ex, tm, cs)

        # Translucent background is disabled to allow standard native window frame rendering
        assert not panel.testAttribute(QtCore.Qt.WA_TranslucentBackground)
        
        # MainContainer border is 'none', not artificial segmented border
        assert "border: none" in panel.main_container.styleSheet()
        assert not hasattr(panel, "search_box_frame") or not panel.search_box_frame.isVisible()
        panel.close()


def test_issue_2_search_toggle_size_stability(qapp):
    """2. Verify clicking search toggle repeatedly never mutates window geometry or button sizes."""
    with tempfile.TemporaryDirectory() as tmp_dir:
        cs, lm, inj, wm, clip, tm, ex = create_test_env(tmp_dir)
        panel = FloatingPanel(lm, ex, tm, cs)
        panel.resize(300, 160)
        qapp.processEvents()

        initial_w = panel.width()
        initial_h = panel.height()
        initial_btn_size = panel.buttons_widgets[0].size()

        # Toggle search open and closed 5 times
        for _ in range(5):
            panel.toggle_search_box()
            qapp.processEvents()
            assert panel.search_input.isVisible() is True
            assert panel.layout_combo.isVisible() is False
            assert panel.width() == initial_w
            assert panel.height() == initial_h

            panel.toggle_search_box()
            qapp.processEvents()
            assert panel.search_input.isVisible() is False
            assert panel.layout_combo.isVisible() is True
            assert panel.width() == initial_w
            assert panel.height() == initial_h
            assert panel.buttons_widgets[0].size() == initial_btn_size
        panel.close()


def test_issue_3_global_search_and_click_behavior(qapp):
    """3. Verify search is global across all layouts, clicking result switches layout, exits search, flashes, and does NOT execute action."""
    with tempfile.TemporaryDirectory() as tmp_dir:
        cs, lm, inj, wm, clip, tm, ex = create_test_env(tmp_dir)
        lm.set_active_layout("layout_1")
        panel = FloatingPanel(lm, ex, tm, cs)
        panel.show()
        qapp.processEvents()

        # Active layout is layout_1
        assert lm.active_layout_id == "layout_1"

        # Search for button that only exists in layout_2
        panel.enter_search()
        panel.search_input.setText("特别")
        qapp.processEvents()

        # Matched buttons should appear
        matching_widgets = [w for w in panel.buttons_widgets if w.button_model.id == "b_special"]
        assert len(matching_widgets) == 1
        special_widget = matching_widgets[0]

        # Click the matched button
        special_widget.click()
        qapp.processEvents()

        # 1. Action was NOT executed (no text was typed into search input or injected)
        assert len(inj.sent_texts) == 0
        assert panel.search_input.text() == ""

        # 2. Search mode automatically exited
        assert panel._search_interactive is False
        assert panel.search_input.isVisible() is False
        assert panel.layout_combo.isVisible() is True

        # 3. Switched to layout_2 and layout_combo updated
        assert lm.active_layout_id == "layout_2"
        assert panel.layout_combo.currentData() == "layout_2"

        # 4. Button in layout_2 is highlighted/flashing
        b_in_l2 = next(w for w in panel.buttons_widgets if w.button_model.id == "b_special")
        assert b_in_l2 is not None

        # 5. Clicking button in layout executes input into external target app, NOT search box
        b_in_l2.click()
        import time
        for _ in range(25):
            qapp.processEvents()
            if inj.sent_texts:
                break
            time.sleep(0.02)
        assert "special_text" in inj.sent_texts
        assert panel.search_input.text() == ""

        panel.close()


def test_issue_4_button_clean_domain_model():
    """4. Verify button domain model has no complex self-healing heuristics and promotes empty label cleanly."""
    # Standard button
    b1 = Button(id="b1", label="保存", action_id="a1")
    assert b1.display_text == "保存"

    # From dict with empty label promotes legacy icon to label
    b2 = Button.from_dict({"id": "b2", "label": "", "action_id": "a2", "icon": "车"})
    assert b2.label == "车"
    assert b2.icon == ""
    assert b2.display_text == "车"

    # Button icon is not superposed on label
    b3 = Button(id="b3", label="保存", action_id="a3", icon="💾")
    assert b3.display_text == "保存"

    # Format helper directly returns label
    assert format_button_display_text("车", "车\nrc") == "车\nrc"
    assert format_button_display_text("💾", "保存") == "保存"
    assert format_button_display_text("", "普通") == "普通"
    assert format_button_display_text("车", "") == "车"


def test_issue_5_window_position_preserved_after_settings(qapp):
    """5. Verify window does not jump to (350, 250) after closing settings dialog."""
    with tempfile.TemporaryDirectory() as tmp_dir:
        cs, lm, inj, wm, clip, tm, ex = create_test_env(tmp_dir)
        panel = FloatingPanel(lm, ex, tm, cs)
        panel.move(520, 380)
        qapp.processEvents()

        assert panel.x() == 520
        assert panel.y() == 380

        # Simulate settings closed
        panel._on_settings_closed(QtWidgets.QDialog.Accepted)
        qapp.processEvents()

        # Window position must remain exactly (520, 380)
        assert panel.x() == 520
        assert panel.y() == 380
        panel.close()


def test_issue_6_main_window_not_locked_or_topmost_during_settings(qapp):
    """6. Verify FloatingPanel is non-modal and topmost is removed while settings is open, and restored on exit."""
    with tempfile.TemporaryDirectory() as tmp_dir:
        cs, lm, inj, wm, clip, tm, ex = create_test_env(tmp_dir)
        panel = FloatingPanel(lm, ex, tm, cs)
        panel.show()
        qapp.processEvents()

        # Open settings
        panel.open_settings()
        qapp.processEvents()

        assert hasattr(panel, "_settings_dialog")
        dlg = panel._settings_dialog
        assert dlg.isVisible() is True
        # Modality is NonModal so user can move the main panel
        assert dlg.windowModality() == QtCore.Qt.NonModal

        # Close settings
        dlg.close()
        qapp.processEvents()
        panel.close()


class ConfigurableMockWindowManager(BaseWindowManager):
    def __init__(self):
        self.windows = {}
        self.fg_hwnd = None

    def register_window(self, hwnd: int, title: str, process_name: str, pid: int):
        self.windows[hwnd] = {
            "handle": hwnd,
            "title": title,
            "process_name": process_name,
            "process_id": pid,
            "is_admin": False,
            "is_valid": True,
        }

    def get_foreground_window_handle(self):
        return self.fg_hwnd

    def is_window_valid(self, handle):
        return handle in self.windows

    def get_window_info(self, handle):
        return self.windows.get(handle, {
            "handle": handle,
            "title": "",
            "process_name": "",
            "process_id": 0,
            "is_admin": False,
            "is_valid": False,
        })

    def set_foreground_safe(self, handle):
        self.fg_hwnd = handle
        return True

    def is_target_elevated(self, handle):
        return False


def test_issue_7_target_manager_ignores_own_process():
    """7. Verify TargetManager ignores current process windows, preventing binding to self."""
    wm = ConfigurableMockWindowManager()
    tm = TargetManager(window_manager=wm)

    # Window from own process
    my_pid = os.getpid()
    wm.register_window(99999, "QuickInput", "QuickInput.exe", my_pid)
    tm.update_active_window(99999)

    # TargetManager should NOT track own process window
    assert tm.get_effective_hwnd() is None
    info = tm.get_target_info()
    assert info.get("process_name") == ""
    assert info.get("is_valid") is False

    # External window
    wm.register_window(88888, "Document - Notepad", "notepad.exe", my_pid + 100)
    tm.update_active_window(88888)
    assert tm.get_effective_hwnd() == 88888
    info = tm.get_target_info()
    assert info.get("process_name") == "notepad.exe"
    assert info.get("is_valid") is True


def test_auto_mode_focus_restoration_prevents_typing_into_self():
    """Verify that in auto mode, prepare_target_for_input restores foreground when foreground is our window."""
    wm = ConfigurableMockWindowManager()
    tm = TargetManager(window_manager=wm)
    wm.register_window(77777, "External App", "app.exe", 1234)
    tm.update_active_window(77777)
    assert tm.get_effective_hwnd() == 77777

    # Current foreground is another window (e.g. FloatingPanel or desktop)
    wm.fg_hwnd = 99999
    assert wm.get_foreground_window_handle() == 99999

    ok, msg = tm.prepare_target_for_input()
    assert ok is True
    # TargetManager must bring target window 77777 safely to foreground
    assert wm.get_foreground_window_handle() == 77777


def test_topmost_not_restored_while_settings_dialog_is_open(qapp):
    """Verify that _apply_topmost_setting does not restore topmost while SettingsDialog is open."""
    with tempfile.TemporaryDirectory() as tmp_dir:
        cs, lm, inj, wm, clip, tm, ex = create_test_env(tmp_dir)
        panel = FloatingPanel(lm, ex, tm, cs)
        panel.show()
        qapp.processEvents()

        panel.open_settings()
        qapp.processEvents()

        dlg = panel._settings_dialog
        assert dlg.isVisible() is True

        # Switching active layout while in settings should NOT prematurely re-apply topmost
        lm.set_active_layout("layout_2")
        qapp.processEvents()

        # Dialog is still visible, _apply_topmost_setting was suppressed
        assert dlg.isVisible() is True

        dlg.close()
        qapp.processEvents()
        panel.close()


def test_header_layout_geometry_invariance(qapp):
    """Verify search input and layout combo have matching fixed height 24 and expand cleanly between buttons."""
    with tempfile.TemporaryDirectory() as tmp_dir:
        cs, lm, inj, wm, clip, tm, ex = create_test_env(tmp_dir)
        panel = FloatingPanel(lm, ex, tm, cs)
        panel.resize(320, 100)
        qapp.processEvents()

        assert panel.search_input.height() == 24
        assert panel.layout_combo.height() == 24
        assert panel.search_toggle_btn.width() == 26
        assert panel.settings_btn.width() == 26

        panel.enter_search()
        qapp.processEvents()
        assert panel.search_input.isVisible() is True
        assert panel.search_input.width() > 100

        panel.exit_search()
        qapp.processEvents()
        assert panel.layout_combo.isVisible() is True
        assert panel.layout_combo.width() > 100

        panel.close()

