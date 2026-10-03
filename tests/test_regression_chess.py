# -*- coding: utf-8 -*-
"""Regression tests verifying Chinese chess shortcut buttons behavior."""

import os
from storage.pack_store import PackStore
from application.action_executor import ActionExecutor
from application.target_manager import TargetManager
from tests.test_executor import MockInputInjector, MockClipboardManager, MockWindowManager


def test_chinese_chess_buttons_regression():
    base_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
    chess_pack_dir = os.path.join(base_dir, "packs", "chess")

    ok, msg, data = PackStore.import_pack(chess_pack_dir)
    assert ok is True

    actions_map = {a.id: a for a in data["actions"]}
    buttons_map = {b.id: b for b in data["buttons"]}

    # Verify red_bing -> rb
    assert "red_bing" in buttons_map
    rb_btn = buttons_map["red_bing"]
    assert rb_btn.action_id == "act_rb"
    assert actions_map["act_rb"].steps[0].value == "rb"

    # Verify black_jiang -> bj
    assert "black_jiang" in buttons_map
    bj_btn = buttons_map["black_jiang"]
    assert bj_btn.action_id == "act_bj"
    assert actions_map["act_bj"].steps[0].value == "bj"

    # Verify all 14 chess pieces present
    expected_codes = {
        "act_rb": "rb", "act_rp": "rp", "act_rm": "rm", "act_rc": "rc",
        "act_rs": "rs", "act_rx": "rx", "act_rshuai": "rshuai",
        "act_bz": "bz", "act_bp": "bp", "act_bm": "bm", "act_bc": "bc",
        "act_bs": "bs", "act_bx": "bx", "act_bj": "bj",
    }
    for aid, code in expected_codes.items():
        assert aid in actions_map
        assert actions_map[aid].steps[0].value == code


def test_chess_execution_with_auto_enter():
    inj = MockInputInjector()
    clip = MockClipboardManager()
    wm = MockWindowManager()
    tm = TargetManager(window_manager=wm)
    tm.update_active_window(12345)

    executor = ActionExecutor(injector=inj, clipboard_mgr=clip, target_mgr=tm)

    base_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
    chess_pack_dir = os.path.join(base_dir, "packs", "chess")
    _, _, data = PackStore.import_pack(chess_pack_dir)
    actions_map = {a.id: a for a in data["actions"]}

    # 1. Click red_bing without auto_enter
    success, _ = executor.execute_sync(actions_map["act_rb"], auto_enter_override=False)
    assert success is True
    assert inj.sent_texts == ["rb"]
    assert "ENTER" not in inj.sent_keys

    # 2. Click black_jiang with auto_enter enabled
    inj.sent_texts.clear()
    inj.sent_keys.clear()
    success, _ = executor.execute_sync(actions_map["act_bj"], auto_enter_override=True)
    assert success is True
    assert inj.sent_texts == ["bj"]
    assert "ENTER" in inj.sent_keys


def test_chess_buttons_no_duplicate_characters(qapp):
    """Verify that chess buttons don't have duplicate piece characters (e.g. 车车rc)."""
    from domain.button import Button, format_button_display_text
    from ui.floating_panel import ActionButtonWidget

    base_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
    chess_pack_dir = os.path.join(base_dir, "packs", "chess")
    ok, _, data = PackStore.import_pack(chess_pack_dir)
    assert ok is True

    # 1. Verify buttons in pack do not have duplicate piece characters in icon
    for btn in data["buttons"]:
        widget = ActionButtonWidget(btn)
        first_line = btn.label.split("\n")[0].strip()
        # The piece name should appear exactly once in widget text
        assert widget.text().count(first_line) == 1, f"Duplicate character in button {btn.id}: {widget.text()}"

    # 2. Verify red_che specifically
    che_btn = next(b for b in data["buttons"] if b.id == "red_che")
    assert che_btn.label == "车\nrc"
    w_che = ActionButtonWidget(che_btn)
    assert w_che.text() == "车\nrc"
    assert w_che.text().count("车") == 1
    assert "rc" in w_che.text()

    # 3. Defensive deduplication against legacy config containing icon="车" and label="车\nrc"
    legacy_data = {"id": "legacy_che", "label": "车\nrc", "action_id": "act_rc", "icon": "车"}
    legacy_btn = Button.from_dict(legacy_data)
    assert legacy_btn.icon == ""  # Automatically sanitized
    assert legacy_btn.display_text == "车\nrc"

    # 4. format_button_display_text returns clean label without icon badge superposition
    assert format_button_display_text("车", "车\nrc") == "车\nrc"
    assert format_button_display_text("兵", "兵\nrb") == "兵\nrb"
    assert format_button_display_text("车", "红车\nrc") == "红车\nrc"
    assert format_button_display_text("车", "  车\nrc  ") == "  车\nrc  "
    assert format_button_display_text("💾", "保存") == "保存"
    assert format_button_display_text("", "普通按钮") == "普通按钮"
    assert format_button_display_text("车", "") == "车"


def test_button_empty_label_icon_promotion():
    """Verify that if label is empty but icon is set, icon is promoted to label."""
    from domain.button import Button

    btn = Button.from_dict({"id": "damaged", "label": "", "action_id": "act_d", "icon": "兵"})
    assert btn.label == "兵"
    assert btn.icon == ""
    assert btn.validate() == []


def test_settings_dialog_multiline_label_editing_preserves_newline(qapp):
    """Verify that editing button label in SettingsDialog preserves newline characters via \\n."""
    from ui.settings_dialog import SettingsDialog
    from application.layout_manager import LayoutManager
    from storage.config_store import ConfigStore
    from main import load_default_packs
    import tempfile

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
        idx = dlg.layout_selector.findData("chess")
        dlg.layout_selector.setCurrentIndex(idx)
        qapp.processEvents()

        # Select red_che button
        che_btn = lm.get_button("red_che")
        assert che_btn is not None
        assert che_btn.label == "车\nrc"

        dlg._select_slot(0, 3, "red_che")
        # In edit field, displayed with \n escaped as \n for easy editing
        assert dlg.btn_label_edit.text() == "车\\nrc"

        # Edit to a new multiline label
        dlg.btn_label_edit.setText("帅\\nrshuai")
        assert che_btn.label == "帅\nrshuai"
        assert "车车" not in che_btn.display_text
        dlg.close()


def test_settings_dialog_reset_layout_to_preset(qapp, monkeypatch):
    """Verify that clicking reset preset button successfully restores official layout."""
    from ui.settings_dialog import SettingsDialog
    from application.layout_manager import LayoutManager
    from storage.config_store import ConfigStore
    from main import load_default_packs
    from PyQt5 import QtWidgets
    import tempfile

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
        idx = dlg.layout_selector.findData("chess")
        dlg.layout_selector.setCurrentIndex(idx)
        qapp.processEvents()

        # Mutate the layout (clear slot 0, 0)
        dlg._select_slot(0, 0, "red_bing")
        dlg._clear_selected_slot()
        assert lm.layouts["chess"].get_slot_at(0, 0) is None

        # Auto-accept confirmation dialogs
        monkeypatch.setattr(QtWidgets.QMessageBox, "question", lambda *args, **kwargs: QtWidgets.QMessageBox.Yes)
        monkeypatch.setattr(QtWidgets.QMessageBox, "information", lambda *args, **kwargs: QtWidgets.QMessageBox.Ok)

        # Trigger reset
        dlg._reset_current_layout_to_preset()
        qapp.processEvents()

        # Slot (0, 0) is restored to red_bing
        slot00 = lm.layouts["chess"].get_slot_at(0, 0)
        assert slot00 is not None
        assert slot00.button_id == "red_bing"
        dlg.close()


