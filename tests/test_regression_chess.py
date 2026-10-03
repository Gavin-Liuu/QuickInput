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
