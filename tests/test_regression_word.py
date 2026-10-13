# -*- coding: utf-8 -*-
"""Regression and unit tests verifying Official Document Format (GB/T 9704-2012) preset pack and key capture behavior."""

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


def test_official_doc_preset_pack_regression():
    base_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
    doc_pack_dir = os.path.join(base_dir, "packs", "official_doc")

    ok, msg, data = PackStore.import_pack(doc_pack_dir)
    assert ok is True, f"Official doc pack import failed: {msg}"

    actions_map = {a.id: a for a in data["actions"]}
    buttons_map = {b.id: b for b in data["buttons"]}
    layouts_map = {l.id: l for l in data["layouts"]}

    # 1. Verify margins action (GB/T 9704-2012 5.2.2: 37mm, 35mm, 28mm, 26mm)
    assert "doc_page_margins" in actions_map
    act_margin = actions_map["doc_page_margins"]
    pastes = [s.value for s in act_margin.steps if s.type == "paste"]
    assert "37毫米" in pastes
    assert "35毫米" in pastes
    assert "28毫米" in pastes
    assert "26毫米" in pastes
    hotkeys = [s.hotkey for s in act_margin.steps if s.type == "hotkey"]
    assert "ALT+T" in hotkeys
    assert "ALT+B" in hotkeys
    assert "ALT+L" in hotkeys
    assert "ALT+R" in hotkeys

    # 2. Verify body font action (仿宋_GB2312 + Times New Roman + 三号 + 两端对齐)
    assert "doc_body_font" in actions_map
    act_body = actions_map["doc_body_font"]
    pastes = [s.value for s in act_body.steps if s.type == "paste"]
    assert "仿宋_GB2312" in pastes
    assert "Times New Roman" in pastes
    assert "三号" in pastes
    hotkeys = [s.hotkey for s in act_body.steps if s.type == "hotkey"]
    assert "CTRL+D" in hotkeys
    assert "CTRL+J" in hotkeys

    # 3. Verify title font action (方正小标宋简体 + Times New Roman + 二号 + 居中)
    assert "doc_title_font" in actions_map
    act_title = actions_map["doc_title_font"]
    pastes = [s.value for s in act_title.steps if s.type == "paste"]
    assert "方正小标宋简体" in pastes
    assert "Times New Roman" in pastes
    assert "二号" in pastes
    hotkeys = [s.hotkey for s in act_title.steps if s.type == "hotkey"]
    assert "CTRL+E" in hotkeys

    # 4. Verify headings
    assert "doc_heading_1" in actions_map
    assert any(s.type == "paste" and s.value == "黑体" for s in actions_map["doc_heading_1"].steps)

    assert "doc_heading_2" in actions_map
    assert any(s.type == "paste" and s.value == "楷体_GB2312" for s in actions_map["doc_heading_2"].steps)

    assert "doc_heading_3" in actions_map
    assert any(s.type == "paste" and s.value == "仿宋_GB2312" for s in actions_map["doc_heading_3"].steps)
    assert any(s.type == "hotkey" and s.hotkey == "CTRL+B" for s in actions_map["doc_heading_3"].steps)

    # 5. Verify line spacing (28.9 磅) & indent (首行缩进 2 字符)
    assert "doc_line_spacing" in actions_map
    assert any(s.type == "paste" and s.value == "28.9磅" for s in actions_map["doc_line_spacing"].steps)

    assert "doc_indent_first_line" in actions_map
    assert any(s.type == "paste" and s.value == "2 字符" for s in actions_map["doc_indent_first_line"].steps)

    # 6. Verify hexagonal bracket for document number
    assert "doc_bracket" in actions_map
    assert any(s.type == "paste" and s.value == "〔 〕" for s in actions_map["doc_bracket"].steps)
    assert any(s.type == "key" and s.key == "LEFT" for s in actions_map["doc_bracket"].steps)

    # 7. Verify layout dimensions
    assert "official_doc" in layouts_map
    lay_doc = layouts_map["official_doc"]
    assert lay_doc.rows == 2
    assert lay_doc.columns == 5


def test_official_doc_execution_shortcuts():
    inj = MockInputInjector()
    clip = MockClipboardManager()
    wm = MockWindowManager()
    tm = TargetManager(window_manager=wm)
    tm.update_active_window(12345)

    executor = ActionExecutor(injector=inj, clipboard_mgr=clip, target_mgr=tm)

    base_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
    doc_pack_dir = os.path.join(base_dir, "packs", "official_doc")
    _, _, data = PackStore.import_pack(doc_pack_dir)
    actions_map = {a.id: a for a in data["actions"]}

    # Execute bracket
    ok, _ = executor.execute_sync(actions_map["doc_bracket"])
    assert ok is True
    assert "LEFT" in inj.sent_keys

    # Execute page number
    ok, _ = executor.execute_sync(actions_map["doc_page_number"])
    assert ok is True

    # Execute save
    inj.sent_hotkeys.clear()
    ok, _ = executor.execute_sync(actions_map["doc_save"])
    assert ok is True
    assert ["CTRL", "S"] in inj.sent_hotkeys


def test_key_capture_dialog_enter_protection(qapp):
    """CRITICAL: Pressing Enter must NOT submit or close the dialog!

    Enter must be captured as the key string 'ENTER', and only clicking OK commits.
    """
    dlg = KeyCaptureDialog(parent=None)
    dlg.show()
    qapp.processEvents()

    # Verify dialog is open and modal
    assert dlg.isVisible()

    # Simulate pressing Enter key
    event = QtGui.QKeyEvent(QtCore.QEvent.KeyPress, QtCore.Qt.Key_Return, QtCore.Qt.NoModifier, "\r")
    dlg.keyPressEvent(event)
    qapp.processEvents()

    # Dialog MUST remain open!
    assert dlg.isVisible()
    # Captured key must be ENTER
    assert dlg.get_captured_key() == "ENTER"
    assert dlg.key_edit.text() == "ENTER"

    # Simulate pressing Alt+Q
    event_alt_q = QtGui.QKeyEvent(QtCore.QEvent.KeyPress, QtCore.Qt.Key_Q, QtCore.Qt.AltModifier, "Q")
    dlg.keyPressEvent(event_alt_q)
    qapp.processEvents()
    assert dlg.get_captured_key() == "ALT+Q"
    assert dlg.key_edit.text() == "ALT+Q"

    # Now click OK button to commit
    dlg.ok_btn.click()
    qapp.processEvents()

    assert not dlg.isVisible()
    assert dlg.result() == QtWidgets.QDialog.Accepted


def test_key_capture_dialog_clean_ui_no_huge_instructions(qapp):
    """Verify that KeyCaptureDialog has clean, elegant UI without huge instruction paragraphs."""
    dlg = KeyCaptureDialog(parent=None)
    dlg.show()
    qapp.processEvents()

    # Find the descriptive label
    labels = dlg.findChildren(QtWidgets.QLabel)
    info_labels = [l for l in labels if "按键" in l.text() or "Press" in l.text()]
    assert len(info_labels) > 0
    info_label = info_labels[0]

    # Verify the instruction is concise (less than 80 chars) and does NOT contain messy multi-line disclaimers
    assert len(info_label.text()) < 80
    assert "回车保存" not in info_label.text()
    assert "免责声明" not in info_label.text()
    dlg.close()


def test_settings_dialog_step_editor_has_add_key_button(qapp):
    """Verify that SettingsDialog Macro Steps section provides '+ 按键' button opening KeyCaptureDialog."""
    from ui.settings_dialog import SettingsDialog
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

        # Check for Add Key button
        assert hasattr(dlg, "add_key_btn")
        assert "按键" in dlg.add_key_btn.text() or "Key" in dlg.add_key_btn.text()

        # Check for renamed Add Text button (formerly clipboard paste)
        assert hasattr(dlg, "add_text_btn")
        assert "文本" in dlg.add_text_btn.text() or "Text" in dlg.add_text_btn.text()
        dlg.close()


def test_macro_steps_table_height_display(qapp):
    """Verify that Macro Steps table has minimum height to show multiple rows without truncation."""
    from ui.settings_dialog import SettingsDialog
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

        assert hasattr(dlg, "steps_table")
        assert dlg.steps_table.minimumHeight() >= 140
        dlg.close()


def test_settings_dialog_reset_official_doc_preset(qapp, monkeypatch):
    """Verify that clicking reset preset button successfully restores official document layout."""
    from ui.settings_dialog import SettingsDialog
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
        idx = dlg.layout_selector.findData("official_doc")
        assert idx >= 0
        dlg.layout_selector.setCurrentIndex(idx)
        qapp.processEvents()

        # Clear slot (0, 0)
        dlg._select_slot(0, 0, "btn_doc_margin")
        dlg._clear_selected_slot()
        assert lm.layouts["official_doc"].get_slot_at(0, 0) is None

        # Auto-accept confirmation dialogs
        monkeypatch.setattr(QtWidgets.QMessageBox, "question", lambda *args, **kwargs: QtWidgets.QMessageBox.Yes)
        monkeypatch.setattr(QtWidgets.QMessageBox, "information", lambda *args, **kwargs: QtWidgets.QMessageBox.Ok)

        # Trigger reset
        dlg._reset_current_layout_to_preset()
        qapp.processEvents()

        # Slot (0, 0) restored
        slot00 = lm.layouts["official_doc"].get_slot_at(0, 0)
        assert slot00 is not None
        assert slot00.button_id == "btn_doc_margin"
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
        lm.set_active_layout("official_doc")
        inj = MockInputInjector()
        wm = MockWindowManager()
        clip = MockClipboardManager()
        tm = TargetManager(window_manager=wm)
        ex = ActionExecutor(injector=inj, clipboard_mgr=clip, target_mgr=tm)

        panel = FloatingPanel(lm, ex, tm, cs)
        panel.show()
        qapp.processEvents()

        # 1. Gear icon is non-null and text is empty
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
