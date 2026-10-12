# -*- coding: utf-8 -*-
"""Regression and unit tests verifying Microsoft Word preset pack and key capture behavior."""

import os
import tempfile
from PyQt5 import QtCore, QtGui, QtWidgets
from storage.pack_store import PackStore
from domain.action import ActionStep
from domain.i18n import tr, set_current_language, get_current_language
from application.action_executor import ActionExecutor
from application.target_manager import TargetManager
from ui.settings_dialog import KeyCaptureDialog, SettingsDialog
from tests.test_executor import MockInputInjector, MockClipboardManager, MockWindowManager


def test_word_preset_pack_regression():
    base_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
    word_pack_dir = os.path.join(base_dir, "packs", "word")

    ok, msg, data = PackStore.import_pack(word_pack_dir)
    assert ok is True, f"Word pack import failed: {msg}"

    actions_map = {a.id: a for a in data["actions"]}
    buttons_map = {b.id: b for b in data["buttons"]}
    layouts_map = {l.id: l for l in data["layouts"]}

    # 1. Verify formula shortcut (Alt+=)
    assert "word_formula" in actions_map
    act_formula = actions_map["word_formula"]
    assert len(act_formula.steps) == 1
    assert act_formula.steps[0].type == "hotkey"
    assert act_formula.steps[0].hotkey == "ALT+="

    # 2. Verify date & time shortcut (ALT+SHIFT+D -> SPACE -> ALT+SHIFT+T)
    assert "word_date_time" in actions_map
    act_dt = actions_map["word_date_time"]
    types = [s.type for s in act_dt.steps]
    assert "hotkey" in types
    assert any(s.hotkey == "ALT+SHIFT+D" for s in act_dt.steps)
    assert any(s.type == "key" and s.key == "SPACE" for s in act_dt.steps)
    assert any(s.hotkey == "ALT+SHIFT+T" for s in act_dt.steps)

    # 3. Verify line spacing shortcut (Alt -> H -> P -> G -> Alt+N -> Alt+A)
    assert "word_line_spacing" in actions_map
    act_ls = actions_map["word_line_spacing"]
    keys_sent = [s.key for s in act_ls.steps if s.type == "key"]
    assert "ALT" in keys_sent
    assert "H" in keys_sent
    assert "P" in keys_sent
    assert "G" in keys_sent
    hotkeys_sent = [s.hotkey for s in act_ls.steps if s.type == "hotkey"]
    assert "ALT+N" in hotkeys_sent
    assert "ALT+A" in hotkeys_sent

    # 4. Verify FangSong GB2312 font shortcut
    assert "word_fangsong_gb2312" in actions_map
    act_fs = actions_map["word_fangsong_gb2312"]
    assert any(s.type == "paste" and s.value == "仿宋_GB2312" for s in act_fs.steps)

    # 5. Verify layouts
    assert "word" in layouts_map
    lay_word = layouts_map["word"]
    assert lay_word.rows == 2
    assert lay_word.columns == 4


def test_word_execution_shortcuts():
    inj = MockInputInjector()
    clip = MockClipboardManager()
    wm = MockWindowManager()
    tm = TargetManager(window_manager=wm)
    tm.update_active_window(12345)

    executor = ActionExecutor(injector=inj, clipboard_mgr=clip, target_mgr=tm)

    base_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
    word_pack_dir = os.path.join(base_dir, "packs", "word")
    _, _, data = PackStore.import_pack(word_pack_dir)
    actions_map = {a.id: a for a in data["actions"]}

    # Execute formula
    ok, _ = executor.execute_sync(actions_map["word_formula"])
    assert ok is True
    assert ["ALT", "="] in inj.sent_hotkeys

    # Execute save
    inj.sent_hotkeys.clear()
    ok, _ = executor.execute_sync(actions_map["word_save"])
    assert ok is True
    assert ["CTRL", "S"] in inj.sent_hotkeys


def test_key_capture_dialog_enter_protection(qapp):
    """CRITICAL: Pressing Enter must NOT submit or close the dialog!

    Enter must be captured as the key string 'ENTER', and only clicking OK commits.
    """
    dlg = KeyCaptureDialog(parent=None)
    dlg.show()
    qapp.processEvents()

    # Press Enter
    event_enter = QtGui.QKeyEvent(
        QtCore.QEvent.KeyPress, QtCore.Qt.Key_Return, QtCore.Qt.NoModifier
    )
    dlg.keyPressEvent(event_enter)
    qapp.processEvents()

    # The dialog MUST still be open and not accepted
    assert dlg.isVisible() is True
    assert dlg.result() == 0  # Not accepted
    assert dlg.get_captured_key() == "ENTER"

    # Press Ctrl+S
    event_ctrl_s = QtGui.QKeyEvent(
        QtCore.QEvent.KeyPress, QtCore.Qt.Key_S, QtCore.Qt.ControlModifier, "s"
    )
    dlg.keyPressEvent(event_ctrl_s)
    qapp.processEvents()

    assert dlg.isVisible() is True
    assert dlg.get_captured_key() == "CTRL+S"

    # Now click OK button with mouse
    dlg.ok_btn.click()
    qapp.processEvents()

    assert dlg.result() == QtWidgets.QDialog.Accepted
    assert dlg.get_captured_key() == "CTRL+S"
    dlg.close()


def test_settings_dialog_language_system(qapp):
    """Verify that language switching dynamically translates settings and persists."""
    from application.layout_manager import LayoutManager
    from storage.config_store import ConfigStore
    from main import load_default_packs

    with tempfile.TemporaryDirectory() as tmp_dir:
        cs = ConfigStore(config_dir=tmp_dir)
        lm = LayoutManager()
        load_default_packs(lm, ".")
        inj = MockInputInjector()
        wm = MockWindowManager()
        clip = MockClipboardManager()
        tm = TargetManager(window_manager=wm)
        ex = ActionExecutor(injector=inj, clipboard_mgr=clip, target_mgr=tm)

        dlg = SettingsDialog(lm, ex, tm, cs)
        dlg.show()
        qapp.processEvents()

        # Switch to English
        en_idx = dlg.language_combo.findData("en")
        assert en_idx >= 0
        dlg.language_combo.setCurrentIndex(en_idx)
        qapp.processEvents()

        assert get_current_language() == "en"
        assert "QuickInput - Settings Center" in dlg.windowTitle()
        assert dlg.tabs.tabText(0) == "Layouts & Buttons"
        assert dlg.tabs.tabText(1) == "General & Diagnostics"

        # Switch back to Chinese
        zh_idx = dlg.language_combo.findData("zh")
        assert zh_idx >= 0
        dlg.language_combo.setCurrentIndex(zh_idx)
        qapp.processEvents()

        assert get_current_language() == "zh"
        assert "快捷输入工作台 - 设置中心" in dlg.windowTitle()
        assert dlg.tabs.tabText(0) == "布局与按钮"
        assert dlg.tabs.tabText(1) == "常规与诊断"
        dlg.close()


def test_settings_dialog_reset_word_preset(qapp, monkeypatch):
    """Verify that clicking reset preset button successfully restores official Word layout."""
    from application.layout_manager import LayoutManager
    from storage.config_store import ConfigStore
    from main import load_default_packs

    with tempfile.TemporaryDirectory() as tmp_dir:
        cs = ConfigStore(config_dir=tmp_dir)
        lm = LayoutManager()
        load_default_packs(lm, ".")
        inj = MockInputInjector()
        wm = MockWindowManager()
        clip = MockClipboardManager()
        tm = TargetManager(window_manager=wm)
        ex = ActionExecutor(injector=inj, clipboard_mgr=clip, target_mgr=tm)

        dlg = SettingsDialog(lm, ex, tm, cs)
        idx = dlg.layout_selector.findData("word")
        assert idx >= 0
        dlg.layout_selector.setCurrentIndex(idx)
        qapp.processEvents()

        # Clear slot (0, 0)
        dlg._select_slot(0, 0, "btn_word_formula")
        dlg._clear_selected_slot()
        assert lm.layouts["word"].get_slot_at(0, 0) is None

        # Auto-accept confirmation dialogs
        monkeypatch.setattr(QtWidgets.QMessageBox, "question", lambda *args, **kwargs: QtWidgets.QMessageBox.Yes)
        monkeypatch.setattr(QtWidgets.QMessageBox, "information", lambda *args, **kwargs: QtWidgets.QMessageBox.Ok)

        # Trigger reset
        dlg._reset_current_layout_to_preset()
        qapp.processEvents()

        # Slot (0, 0) restored
        slot00 = lm.layouts["word"].get_slot_at(0, 0)
        assert slot00 is not None
        assert slot00.button_id == "btn_word_formula"
        dlg.close()


def test_floating_panel_ui_polish_and_i18n(qapp):
    """Verify that FloatingPanel has vector gear icon, sleek opacity slider, and retranslates."""
    from ui.floating_panel import FloatingPanel
    from application.layout_manager import LayoutManager
    from storage.config_store import ConfigStore
    from main import load_default_packs

    with tempfile.TemporaryDirectory() as tmp_dir:
        cs = ConfigStore(config_dir=tmp_dir)
        lm = LayoutManager()
        load_default_packs(lm, ".")
        lm.set_active_layout("word")
        inj = MockInputInjector()
        wm = MockWindowManager()
        clip = MockClipboardManager()
        tm = TargetManager(window_manager=wm)
        ex = ActionExecutor(injector=inj, clipboard_mgr=clip, target_mgr=tm)

        panel = FloatingPanel(lm, ex, tm, cs)
        panel.show()
        qapp.processEvents()

        # 1. Gear icon is non-null and text is empty (no square emoji glyph)
        assert not panel.settings_btn.icon().isNull()
        assert panel.settings_btn.text() == ""
        assert panel.settings_btn.toolTip() == "打开设置中心"

        # 2. Opacity slider is sleek 18px height
        assert panel.opacity_slider.height() == 18
        assert panel.opacity_slider.width() == 68

        # 3. Test i18n
        set_current_language("en")
        panel.retranslate_ui()
        assert panel.windowTitle() == "QuickInput Workbench"
        assert panel.settings_btn.toolTip() == "Open Settings Center"
        assert panel.opacity_label.text() == "Opacity"

        # Switch back to zh
        set_current_language("zh")
        panel.retranslate_ui()
        assert panel.windowTitle() == "快捷输入工作台"
        panel.close()

