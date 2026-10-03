# -*- coding: utf-8 -*-
"""Edge cases and boundary tests."""

import os
import tempfile
from domain.action import Action, ActionStep
from storage.pack_store import PackStore
from application.action_executor import ActionExecutor
from application.target_manager import TargetManager
from tests.test_executor import MockInputInjector, MockClipboardManager, MockWindowManager


def test_empty_action():
    inj = MockInputInjector()
    clip = MockClipboardManager()
    wm = MockWindowManager()
    tm = TargetManager(window_manager=wm)
    tm.update_active_window(12345)

    executor = ActionExecutor(injector=inj, clipboard_mgr=clip, target_mgr=tm)

    action = Action(id="act_empty", label="Empty Action", steps=[])
    success, msg = executor.execute_sync(action)
    assert success is True
    assert "完成" in msg
    assert len(inj.sent_texts) == 0


def test_nested_repeat_steps():
    inj = MockInputInjector()
    clip = MockClipboardManager()
    wm = MockWindowManager()
    tm = TargetManager(window_manager=wm)
    tm.update_active_window(12345)

    executor = ActionExecutor(injector=inj, clipboard_mgr=clip, target_mgr=tm)

    inner_step = ActionStep(type="text", value="x")
    action = Action(
        id="act_repeat",
        label="Repeat",
        steps=[
            ActionStep(
                type="repeat",
                count=3,
                steps=[
                    ActionStep(
                        type="repeat",
                        count=2,
                        steps=[inner_step],
                    )
                ],
            )
        ],
    )
    success, msg = executor.execute_sync(action)
    assert success is True
    # 3 * 2 = 6 times
    assert len(inj.sent_texts) == 6
    assert inj.sent_texts == ["x"] * 6


def test_concurrent_button_click_prevention():
    inj = MockInputInjector()
    clip = MockClipboardManager()
    wm = MockWindowManager()
    tm = TargetManager(window_manager=wm)
    tm.update_active_window(12345)

    executor = ActionExecutor(injector=inj, clipboard_mgr=clip, target_mgr=tm)

    action = Action(
        id="act_delay",
        label="Delay Action",
        steps=[ActionStep(type="delay", ms=150)],
    )

    started_first = executor.execute_async(action)
    assert started_first is True

    # Immediate second click attempt while first is running
    started_second = executor.execute_async(action)
    assert started_second is False


def test_unicode_and_emojis():
    inj = MockInputInjector()
    clip = MockClipboardManager()
    wm = MockWindowManager()
    tm = TargetManager(window_manager=wm)
    tm.update_active_window(12345)

    executor = ActionExecutor(injector=inj, clipboard_mgr=clip, target_mgr=tm)

    text_val = "中国象棋♟ 缺陷标记 🌹 123 !@#"
    action = Action(
        id="act_emoji",
        label="Emoji Test",
        steps=[ActionStep(type="text", value=text_val)],
    )
    success, _ = executor.execute_sync(action)
    assert success is True
    assert inj.sent_texts == [text_val]


def test_pack_zip_traversal_rejection():
    with tempfile.TemporaryDirectory() as tmp_dir:
        fake_zip = os.path.join(tmp_dir, "malicious.qipack")
        import zipfile
        with zipfile.ZipFile(fake_zip, "w") as zf:
            zf.writestr("../../../evil.bat", "echo hacked")
            zf.writestr("manifest.json", '{"id":"test","name":"test","schema_version":1}')

        ok, msg, _ = PackStore.import_pack(fake_zip)
        assert ok is False
        assert "不安全" in msg
