# -*- coding: utf-8 -*-
"""Storage and corruption recovery tests."""

import os
import tempfile
from storage.config_store import ConfigStore


def test_config_store_save_and_load():
    with tempfile.TemporaryDirectory() as tmp_dir:
        store = ConfigStore(config_dir=tmp_dir)
        cfg = store.load_config()
        assert cfg["schema_version"] == 2
        assert "window" in cfg
        assert "hotkeys" in cfg

        # Modify and save
        cfg["window"]["opacity"] = 0.88
        cfg["window"]["x"] = 500
        ok = store.save_config(cfg)
        assert ok is True

        reloaded = store.load_config()
        assert reloaded["window"]["opacity"] == 0.88
        assert reloaded["window"]["x"] == 500


def test_config_store_corruption_recovery():
    with tempfile.TemporaryDirectory() as tmp_dir:
        store = ConfigStore(config_dir=tmp_dir)
        cfg = store.load_config()
        assert cfg is not None

        # Corrupt the config file with invalid JSON syntax
        with open(store.config_file, "w", encoding="utf-8") as f:
            f.write("{ invalid json content: 123,,,,,")

        # Loading corrupted config should not crash, but back up and restore default
        recovered = store.load_config()
        assert recovered is not None
        assert recovered["schema_version"] == 2
        assert recovered["window"]["opacity"] == 0.95

        # Check that backup file was created
        backups = os.listdir(store.backup_dir)
        corrupted_backups = [b for b in backups if "config_corrupted_" in b]
        assert len(corrupted_backups) == 1


def test_config_store_create_backup():
    with tempfile.TemporaryDirectory() as tmp_dir:
        store = ConfigStore(config_dir=tmp_dir)
        store.load_config()
        backup_path = store.create_backup()
        assert backup_path is not None
        assert os.path.exists(backup_path)


def test_config_store_v1_to_v2_migration():
    import json
    with tempfile.TemporaryDirectory() as tmp_dir:
        store = ConfigStore(config_dir=tmp_dir)
        v1_data = {
            "schema_version": 1,
            "window": {
                "opacity": 0.82,
                "auto_enter": True,
            },
            "active_layout_id": "lay_test",
            "layouts": {
                "lay_test": {
                    "name": "测试布局",
                    "rows": 1,
                    "columns": 2,
                    "settings": {
                        "button_size": "compact",
                    },
                    "buttons": [
                        {"button_id": "b1", "row": 0, "column": 0},
                        {"button_id": "b2", "row": 0, "column": 1},
                    ],
                }
            },
            "buttons": {
                "b1": {"id": "b1", "label": "B1", "action_id": "a1", "auto_enter": True},
                "b2": {"id": "b2", "label": "B2", "action_id": "a2"},
            },
            "actions": {
                "a1": {"id": "a1", "label": "A1", "confirm": True, "steps": []},
                "a2": {"id": "a2", "label": "A2", "steps": []},
            },
        }
        with open(store.config_file, "w", encoding="utf-8") as f:
            json.dump(v1_data, f)

        migrated = store.load_config()
        assert migrated["schema_version"] == 2
        lay = migrated["layouts"]["lay_test"]
        assert lay["settings"]["opacity"] == 0.82
        assert lay["settings"]["auto_enter_default"] is True
        assert lay["settings"]["confirm_before_action"] is True
