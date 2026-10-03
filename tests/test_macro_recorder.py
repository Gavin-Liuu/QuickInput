# -*- coding: utf-8 -*-
"""Macro Recorder simulation, target filtering, and key processing tests."""

from application.macro_recorder import MacroRecorder
from domain.action import Action
from application.action_executor import ActionExecutor
from application.target_manager import TargetManager
from tests.test_executor import MockInputInjector, MockClipboardManager, MockWindowManager


def test_recorder_character_merging():
    rec = MacroRecorder(record_delays=False)
    rec.is_recording = True

    # Simulate typing 'd', 'e', 'f', 'e', 'c', 't'
    for ch in "DEFECT":
        vk = ord(ch)
        rec.simulate_record_key(vk)

    steps = rec.steps
    # Should be merged into a single 'text' step with value 'defect'
    assert len(steps) == 1
    assert steps[0].type == "text"
    assert steps[0].value == "defect"


def test_recorder_special_keys_and_hotkeys():
    rec = MacroRecorder(record_delays=False)
    rec.is_recording = True

    # Press Enter
    rec.simulate_record_key(0x0D)
    assert len(rec.steps) == 1
    assert rec.steps[0].type == "key"
    assert rec.steps[0].key == "ENTER"

    # Press Ctrl+S
    rec.simulate_record_key(ord('S'), modifiers=["CTRL"])
    assert len(rec.steps) == 2
    assert rec.steps[1].type == "hotkey"
    assert "CTRL+S" in rec.steps[1].hotkey


def test_target_filtering_outside_window():
    rec = MacroRecorder(record_delays=False)
    rec.is_recording = True
    rec.set_target(hwnd=10001, pid=5555)

    # Key from foreign window (hwnd 20002)
    rec.simulate_record_key(ord('A'), fg_hwnd=20002)
    assert len(rec.steps) == 0

    # Key from target window (hwnd 10001)
    rec.simulate_record_key(ord('A'), fg_hwnd=10001)
    assert len(rec.steps) == 1
    assert rec.steps[0].value == "a"


def test_own_window_filtering():
    rec = MacroRecorder(record_delays=False)
    rec.is_recording = True
    rec.register_own_hwnd(30003)

    # Key from own registered window
    rec.simulate_record_key(ord('A'), fg_hwnd=30003)
    assert len(rec.steps) == 0


def test_stable_hotkey_ordering():
    rec = MacroRecorder(record_delays=False)
    rec.is_recording = True

    # Ctrl+Shift+P with modifiers in reverse order in input
    rec.simulate_record_key(ord('P'), modifiers=["SHIFT", "CTRL"])
    assert len(rec.steps) == 1
    assert rec.steps[0].type == "hotkey"
    assert rec.steps[0].hotkey == "CTRL+SHIFT+P"

    # Alt+Tab
    rec.simulate_record_key(0x09, modifiers=["ALT"])
    assert len(rec.steps) == 2
    assert rec.steps[1].hotkey == "ALT+TAB"


def test_shift_punctuation_and_special_keys():
    rec = MacroRecorder(record_delays=False)
    rec.is_recording = True

    # Shift + 1 -> '!'
    rec.simulate_record_key(ord('1'), modifiers=["SHIFT"])
    assert len(rec.steps) == 1
    assert rec.steps[0].type == "text"
    assert rec.steps[0].value == "!"

    # Shift + TAB (special key) -> 'SHIFT+TAB' hotkey
    rec.simulate_record_key(0x09, modifiers=["SHIFT"])
    assert len(rec.steps) == 2
    assert rec.steps[1].type == "hotkey"
    assert rec.steps[1].hotkey == "SHIFT+TAB"


def test_auto_repeat_filtering():
    rec = MacroRecorder(record_delays=False, record_auto_repeat=False)
    rec.is_recording = True

    # Press down 'A'
    rec.simulate_record_key(ord('A'), is_down=True)
    assert len(rec.steps) == 1
    assert rec.steps[0].value == "a"

    # Repeated down on 'A' while still held down
    rec.simulate_record_key(ord('A'), is_down=True)
    # Step count and text length should not increase
    assert len(rec.steps) == 1
    assert rec.steps[0].value == "a"

    # Key up
    rec.simulate_record_key(ord('A'), is_down=False)

    # Press down again after release
    rec.simulate_record_key(ord('A'), is_down=True)
    assert rec.steps[0].value == "aa"


def test_stop_and_cancel_state_reset():
    rec = MacroRecorder(record_delays=False)
    rec.start()
    rec.simulate_record_key(ord('A'))
    assert len(rec.steps) == 1

    rec.cancel()
    assert rec.steps == []
    assert rec.is_recording is False
    assert len(rec._active_modifiers) == 0


def test_pause_resume_clears_modifiers():
    rec = MacroRecorder(record_delays=False)
    rec.start()

    # Hold Shift
    rec.simulate_record_key(0x10, is_down=True)
    assert "SHIFT" in rec._active_modifiers

    # Pause clears stuck modifiers
    rec.pause()
    assert len(rec._active_modifiers) == 0

    # Resume keeps clean state
    rec.resume()
    assert len(rec._active_modifiers) == 0
    rec.stop()


def test_target_lost_callback():
    rec = MacroRecorder(record_delays=False)
    rec.is_recording = True
    rec.set_target(hwnd=10001, pid=5555)

    lost_called = []
    regained_called = []
    rec.on_target_lost = lambda: lost_called.append(True)
    rec.on_target_regained = lambda: regained_called.append(True)

    # Switch away from target
    rec.simulate_record_key(ord('A'), fg_hwnd=99999)
    assert len(lost_called) == 1

    # Switch back to target
    rec.simulate_record_key(ord('A'), fg_hwnd=10001)
    assert len(regained_called) == 1


def test_recorded_steps_replay_in_executor():
    inj = MockInputInjector()
    clip = MockClipboardManager()
    wm = MockWindowManager()
    tm = TargetManager(window_manager=wm)
    tm.update_active_window(12345)
    executor = ActionExecutor(injector=inj, clipboard_mgr=clip, target_mgr=tm)

    rec = MacroRecorder(record_delays=False)
    rec.is_recording = True
    rec.simulate_record_key(ord('H'))
    rec.simulate_record_key(ord('I'))
    rec.simulate_record_key(0x0D)  # ENTER
    rec.simulate_record_key(ord('S'), modifiers=["CTRL"])  # CTRL+S

    action = Action(id="recorded_act", label="录制重放动作", steps=rec.steps)
    ok, msg = executor.execute_sync(action)
    assert ok is True
    assert "hi" in inj.sent_texts
    assert "ENTER" in inj.sent_keys
    assert ["CTRL", "S"] in inj.sent_hotkeys
