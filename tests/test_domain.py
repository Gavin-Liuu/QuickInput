# -*- coding: utf-8 -*-
"""Domain model unit tests."""

from domain.action import Action, ActionStep
from domain.button import Button
from domain.layout import Layout, LayoutButtonSlot, LayoutSettings
from domain.profile import Profile


def test_action_step_serialization():
    step = ActionStep(type="text", value="defect")
    d = step.to_dict()
    assert d["type"] == "text"
    assert d["value"] == "defect"

    restored = ActionStep.from_dict(d)
    assert restored.type == "text"
    assert restored.value == "defect"


def test_action_step_validation():
    valid_step = ActionStep(type="key", key="ENTER")
    assert valid_step.validate() == []

    invalid_type = ActionStep(type="unsupported_step")
    assert len(invalid_type.validate()) > 0

    invalid_delay = ActionStep(type="delay", ms=-10)
    assert len(invalid_delay.validate()) > 0

    invalid_var = ActionStep(type="variable", name="unknown_var")
    assert len(invalid_var.validate()) > 0


def test_action_serialization_and_clone():
    act = Action(
        id="act_test",
        label="测试动作",
        steps=[
            ActionStep(type="text", value="hello"),
            ActionStep(type="key", key="ENTER"),
        ],
        on_error="stop",
        confirm=True,
    )
    d = act.to_dict()
    restored = Action.from_dict(d)
    assert restored.id == "act_test"
    assert restored.label == "测试动作"
    assert len(restored.steps) == 2
    assert restored.confirm is True

    cloned = act.clone("act_test_2")
    assert cloned.id == "act_test_2"
    assert len(cloned.steps) == 2


def test_button_model():
    btn = Button(
        id="btn_1",
        label="测试按钮",
        action_id="act_1",
        color="#E53935",
        tooltip="输入提示",
    )
    d = btn.to_dict()
    restored = Button.from_dict(d)
    assert restored.id == "btn_1"
    assert restored.label == "测试按钮"
    assert restored.action_id == "act_1"
    assert restored.color == "#E53935"
    assert restored.validate() == []


def test_layout_model():
    layout = Layout(
        id="lay_1",
        name="测试布局",
        orientation="horizontal",
        rows=2,
        columns=4,
        buttons=[
            LayoutButtonSlot(button_id="btn_1", row=0, column=0),
            LayoutButtonSlot(button_id="btn_2", row=0, column=1),
        ],
        settings=LayoutSettings(opacity=0.9, button_size="touch", confirm_before_action=True, auto_enter_default=True),
    )
    d = layout.to_dict()
    restored = Layout.from_dict(d)
    assert restored.id == "lay_1"
    assert restored.name == "测试布局"
    assert restored.rows == 2
    assert restored.columns == 4
    assert len(restored.buttons) == 2
    assert restored.settings.opacity == 0.9
    assert restored.settings.button_size == "touch"
    assert restored.settings.confirm_before_action is True
    assert restored.settings.auto_enter_default is True
    assert restored.validate() == []


def test_profile_matching():
    prof = Profile(
        process="labelme.exe",
        window_title_contains="标注",
        layout_id="annotation",
    )
    assert prof.matches("labelme.exe", "图片标注工具") is True
    assert prof.matches("Labelme.exe", "任意标注窗口") is True
    assert prof.matches("notepad.exe", "图片标注工具") is False
    assert prof.matches("labelme.exe", "无匹配标题") is False

    # Title-only profile
    prof_title = Profile(window_title_contains="记事本", layout_id="notes")
    assert prof_title.matches("notepad.exe", "新建文本文档 - 记事本") is True
    assert prof_title.matches("calc.exe", "计算器") is False
