# -*- coding: utf-8 -*-
"""Layout Manager unit tests."""

from application.layout_manager import LayoutManager
from domain.action import Action
from domain.button import Button
from domain.layout import Layout
from domain.profile import Profile


def test_layout_manager_crud_and_switching():
    lm = LayoutManager()

    lay1 = Layout(id="lay_1", name="Layout 1")
    lay2 = Layout(id="lay_2", name="Layout 2")
    lm.register_layout(lay1)
    lm.register_layout(lay2)

    assert lm.active_layout_id == "lay_1"

    # Switch
    ok = lm.set_active_layout("lay_2")
    assert ok is True
    assert lm.get_active_layout().id == "lay_2"

    # Duplicate
    copy_lay = lm.duplicate_layout("lay_2", "lay_2_copy", "Layout 2 Copy")
    assert copy_lay is not None
    assert "lay_2_copy" in lm.layouts

    # Delete
    del_ok = lm.delete_layout("lay_2")
    assert del_ok is True
    assert "lay_2" not in lm.layouts


def test_profile_auto_switch():
    lm = LayoutManager()
    lm.register_layout(Layout(id="notes", name="Notes Layout"))
    lm.register_layout(Layout(id="code", name="Code Layout"))

    lm.register_profile(Profile(process="code.exe", layout_id="code"))

    lm.set_active_layout("notes")
    assert lm.active_layout_id == "notes"

    # Trigger profile check
    switched = lm.check_and_apply_profile("code.exe", "test.py - VSCode")
    assert switched == "code"
    assert lm.active_layout_id == "code"


def test_search_and_recent_buttons():
    lm = LayoutManager()
    act = Action(id="act_save", label="保存文件")
    btn = Button(id="btn_save", label="保存", action_id="act_save", tooltip="按键保存")
    lm.register_action(act)
    lm.register_button(btn)

    results = lm.search_buttons("保存")
    assert len(results) == 1
    assert results[0].id == "btn_save"

    # Recent tracking
    lm.record_button_click("btn_save")
    assert "btn_save" in lm.recent_button_ids


def test_create_layout_with_presets():
    lm = LayoutManager()
    lay = lm.create_layout_with_presets(
        layout_id="new_lay",
        name="九宫格",
        orientation="horizontal",
        rows=3,
        columns=3,
        button_size="standard",
    )
    assert lay.id == "new_lay"
    assert lay.name == "九宫格"
    assert lay.rows == 3
    assert lay.columns == 3
    assert lay.settings.button_size == "standard"
    assert len(lay.buttons) == 9

    # Each slot has a valid button and action
    for idx, slot in enumerate(lay.buttons, start=1):
        btn = lm.get_button(slot.button_id)
        assert btn is not None
        assert btn.label == f"按钮 {idx}"
        act = lm.get_action_for_button(slot.button_id)
        assert act is not None
        assert act.label == f"按钮 {idx}"


def test_duplicate_layout_button_isolation():
    lm = LayoutManager()
    lay = lm.create_layout_with_presets("orig", "原布局", rows=1, columns=2)
    orig_btn0_id = lay.buttons[0].button_id
    orig_btn0 = lm.get_button(orig_btn0_id)
    assert orig_btn0.label == "按钮 1"

    # Duplicate
    clone = lm.duplicate_layout("orig", "orig_copy", "副本布局")
    clone_btn0_id = clone.buttons[0].button_id
    assert clone_btn0_id != orig_btn0_id

    # Modify clone's button
    clone_btn0 = lm.get_button(clone_btn0_id)
    clone_btn0.label = "修改后的按钮"
    clone_act0 = lm.get_action_for_button(clone_btn0_id)
    clone_act0.label = "修改后的按钮"

    # Verify original layout's button remains untouched
    assert orig_btn0.label == "按钮 1"
    orig_act0 = lm.get_action_for_button(orig_btn0_id)
    assert orig_act0.label == "按钮 1"


def test_slot_creation_and_removal():
    lm = LayoutManager()
    lay = Layout(id="grid_test", name="空网格", rows=2, columns=2)
    lm.register_layout(lay)

    # Create button at (1, 1)
    btn = lm.create_button_for_slot("grid_test", 1, 1, label="自定义按键")
    assert btn is not None
    assert lay.get_button_at(1, 1) == btn.id

    # Remove button at (1, 1)
    ok = lm.remove_button_from_slot("grid_test", 1, 1)
    assert ok is True
    assert lay.get_button_at(1, 1) is None
    assert btn.id not in lm.buttons
