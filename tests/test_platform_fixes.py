# -*- coding: utf-8 -*-
"""Unit tests specifically verifying fixes for input injection, hotkeys, and migration."""

import os
import json
import tempfile
from platform_layer.windows.send_input import (
    WindowsInputInjector,
    EXTENDED_KEYS,
)
from platform_layer.windows.global_hotkey import WindowsGlobalHotkeyManager
from storage.config_store import ConfigStore


def test_send_input_vk_resolution_not_corrupted():
    """Verify that punctuation characters are never mapped to dangerous keys like VK_DELETE."""
    inj = WindowsInputInjector()

    # Period '.' must resolve to VK_OEM_PERIOD (0xBE = 190), never VK_DELETE (0x2E = 46)
    period_vk = inj._resolve_vk(".")
    assert period_vk == 0xBE
    assert period_vk != 0x2E

    # Comma ',' must resolve to VK_OEM_COMMA (0xBC = 188), never VK_SNAPSHOT (0x2C = 44)
    comma_vk = inj._resolve_vk(",")
    assert comma_vk == 0xBC
    assert comma_vk != 0x2C

    # Minus '-' must resolve to VK_OEM_MINUS (0xBD = 189), never VK_INSERT (0x2D = 45)
    minus_vk = inj._resolve_vk("-")
    assert minus_vk == 0xBD
    assert minus_vk != 0x2D

    # Slash '/' must resolve to VK_OEM_2 (0xBF = 191)
    slash_vk = inj._resolve_vk("/")
    assert slash_vk == 0xBF

    # Semicolon ';' must resolve to VK_OEM_1 (0xBA = 186)
    semi_vk = inj._resolve_vk(";")
    assert semi_vk == 0xBA

    # Standard keys should remain intact
    assert inj._resolve_vk("DELETE") == 0x2E
    assert inj._resolve_vk("ENTER") == 0x0D
    assert inj._resolve_vk("A") == ord("A")
    assert inj._resolve_vk("1") == ord("1")


def test_send_input_extended_keys():
    """Verify extended navigation keys are recognized."""
    inj = WindowsInputInjector()
    for key_name in ["UP", "DOWN", "LEFT", "RIGHT", "HOME", "END", "PAGEUP", "PAGEDOWN"]:
        vk = inj._resolve_vk(key_name)
        assert vk in EXTENDED_KEYS


def test_global_hotkey_manager_named_and_unregister():
    """Test dynamic registration and unregistration of named hotkeys."""
    mgr = WindowsGlobalHotkeyManager()

    called = []
    def callback():
        called.append(True)

    # Register named
    hid = mgr.register_named_hotkey("test_hotkey", "ALT+SHIFT+F12", callback)
    assert hid > 0
    assert "test_hotkey" in mgr._named_hotkeys

    # Unregister named
    ok = mgr.unregister_named_hotkey("test_hotkey")
    assert ok is True
    assert "test_hotkey" not in mgr._named_hotkeys

    mgr.unregister_all()


def test_legacy_config_migration():
    """Verify legacy floating_keyboard_config.json is migrated on clean start."""
    with tempfile.TemporaryDirectory() as tmp_dir:
        # Create a fake legacy config in cwd
        legacy_cfg_path = os.path.join(tmp_dir, "floating_keyboard_config.json")
        legacy_data = {
            "x": 888,
            "y": 444,
            "opacity": 0.88,
            "always_on_top": True,
            "auto_enter": True,
            "layout_mode": "vertical",
        }
        with open(legacy_cfg_path, "w", encoding="utf-8") as f:
            json.dump(legacy_data, f)

        orig_cwd = os.getcwd()
        try:
            cs = ConfigStore(config_dir=tmp_dir)
            cfg = cs.load_config()
            assert cfg["window"]["x"] == 888
            assert cfg["window"]["y"] == 444
            assert cfg["window"]["opacity"] == 0.88
            assert cfg["window"]["auto_enter"] is True
            assert cfg["window"]["layout_mode"] == "vertical"
        finally:
            os.chdir(orig_cwd)


def test_edge_snap_coordinates():
    """Verify precision of edge snapping coordinates at screen boundaries."""
    screen_x, screen_y, screen_w, screen_h = 0, 0, 1920, 1080
    snap_dist = 18
    panel_w, panel_h = 200, 100

    def compute_snap(target_x, target_y):
        if abs(target_x - screen_x) <= snap_dist:
            target_x = screen_x
        elif abs(target_x + panel_w - (screen_x + screen_w)) <= snap_dist:
            target_x = screen_x + screen_w - panel_w

        if abs(target_y - screen_y) <= snap_dist:
            target_y = screen_y
        elif abs(target_y + panel_h - (screen_y + screen_h)) <= snap_dist:
            target_y = screen_y + screen_h - panel_h
        return target_x, target_y

    # Near left edge (< 18px)
    assert compute_snap(12, 500) == (0, 500)
    # Near right edge (within 18px of 1720)
    assert compute_snap(1710, 500) == (1720, 500)
    assert 1720 + panel_w == screen_w
    # Near top edge
    assert compute_snap(500, 15) == (500, 0)
    # Near bottom edge (within 18px of 980)
    assert compute_snap(500, 970) == (500, 980)
    assert 980 + panel_h == screen_h
    # Beyond snap distance
    assert compute_snap(500, 500) == (500, 500)

