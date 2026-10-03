# -*- coding: utf-8 -*-
"""Configuration storage with schema versioning, atomic writes, and corrupt recovery."""

import os
import json
import shutil
import tempfile
import datetime
from typing import Dict, Any, Optional

DEFAULT_SCHEMA_VERSION = 2


def get_default_appdata_dir() -> str:
    """Return standard AppData directory or fallback to local directory."""
    appdata = os.getenv("APPDATA")
    if appdata:
        path = os.path.join(appdata, "QuickInput")
    else:
        path = os.path.join(os.path.expanduser("~"), ".quickinput")
    try:
        os.makedirs(path, exist_ok=True)
        os.makedirs(os.path.join(path, "backups"), exist_ok=True)
        os.makedirs(os.path.join(path, "logs"), exist_ok=True)
        os.makedirs(os.path.join(path, "packs"), exist_ok=True)
        return path
    except Exception:
        # Fallback to current directory
        local_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "data")
        os.makedirs(local_dir, exist_ok=True)
        return local_dir


class ConfigStore:
    """Handles persistent configuration reading, atomic writing, and corruption recovery."""

    def __init__(self, config_dir: Optional[str] = None):
        self._is_custom_dir = bool(config_dir)
        self.config_dir = config_dir or get_default_appdata_dir()
        self.config_file = os.path.join(self.config_dir, "config.json")
        self.backup_dir = os.path.join(self.config_dir, "backups")
        os.makedirs(self.backup_dir, exist_ok=True)

    def get_default_config(self) -> Dict[str, Any]:
        cfg = {
            "schema_version": DEFAULT_SCHEMA_VERSION,
            "window": {
                "x": 350,
                "y": 250,
                "opacity": 0.95,
                "always_on_top": True,
                "auto_enter": False,
                "layout_mode": "horizontal",
                "button_size": "compact",
                "collapsed": False,
            },
            "active_layout_id": "chess",
            "hotkeys": {
                "toggle_visible": "ALT+Q",
                "emergency_stop": "ESC",
            },
            "settings": {
                "auto_profile_switch": True,
                "target_mode": "auto",
                "record_delays": True,
            },
            "layouts": {},
            "buttons": {},
            "actions": {},
            "profiles": [],
        }

        # Check for legacy demo config migration
        legacy_paths = []
        if self._is_custom_dir:
            legacy_paths.append(os.path.join(self.config_dir, "floating_keyboard_config.json"))
        else:
            legacy_paths.extend([
                os.path.join(self.config_dir, "floating_keyboard_config.json"),
                os.path.join(os.getcwd(), "floating_keyboard_config.json"),
                os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "floating_keyboard_config.json"),
            ])
        for lp in legacy_paths:
            if os.path.exists(lp):
                try:
                    with open(lp, "r", encoding="utf-8") as lf:
                        legacy = json.load(lf)
                    if isinstance(legacy, dict):
                        for k in ["x", "y", "opacity", "always_on_top", "auto_enter", "layout_mode"]:
                            if k in legacy:
                                cfg["window"][k] = legacy[k]
                    break
                except Exception:
                    pass

        return cfg

    def load_config(self) -> Dict[str, Any]:
        """Loads configuration from JSON file. Auto-recovers on corruption."""
        if not os.path.exists(self.config_file):
            default_cfg = self.get_default_config()
            self.save_config(default_cfg)
            return default_cfg

        try:
            with open(self.config_file, "r", encoding="utf-8") as f:
                data = json.load(f)

            if not isinstance(data, dict):
                raise ValueError("Config root is not a JSON object")

            # Check schema version and run migrations
            version = data.get("schema_version", 1)
            if version < 2:
                data = self._migrate_v1_to_v2(data)

            # Merge with default structure to prevent missing keys
            merged = self.get_default_config()
            self._deep_update(merged, data)
            merged["schema_version"] = DEFAULT_SCHEMA_VERSION

            # Clean up redundant duplicate icons from stored buttons
            for bid, b_dict in merged.get("buttons", {}).items():
                if isinstance(b_dict, dict):
                    icon = str(b_dict.get("icon", "")).strip()
                    label = str(b_dict.get("label", ""))
                    if icon and (label.startswith(icon) or (label.split() and label.split()[0] == icon)):
                        b_dict["icon"] = ""

            return merged

        except Exception as e:
            # Corrupted configuration: back up corrupted file and restore default
            self._handle_corrupted_config(e)
            default_cfg = self.get_default_config()
            self.save_config(default_cfg)
            return default_cfg

    def _migrate_v1_to_v2(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Migrate configuration from schema version 1 to 2."""
        window = data.get("window", {})
        global_opacity = float(window.get("opacity", 0.95))
        global_auto_enter = bool(window.get("auto_enter", False))
        active_layout_id = data.get("active_layout_id", "")
        layouts = data.get("layouts", {})
        buttons = data.get("buttons", {})
        actions = data.get("actions", {})

        for lid, lay in layouts.items():
            if not isinstance(lay, dict):
                continue
            settings = lay.setdefault("settings", {})
            if "opacity" not in settings:
                settings["opacity"] = global_opacity
            if "auto_enter_default" not in settings:
                settings["auto_enter_default"] = global_auto_enter if lid == active_layout_id else False
            if "confirm_before_action" not in settings:
                settings["confirm_before_action"] = False

            # Migrate button/action-level settings into layout settings
            slots = lay.get("buttons", [])
            for slot in slots:
                if not isinstance(slot, dict):
                    continue
                bid = slot.get("button_id")
                if bid and bid in buttons:
                    btn = buttons[bid]
                    if isinstance(btn, dict):
                        if btn.get("auto_enter"):
                            settings["auto_enter_default"] = True
                        aid = btn.get("action_id")
                        if aid and aid in actions:
                            act = actions[aid]
                            if isinstance(act, dict):
                                if act.get("confirm"):
                                    settings["confirm_before_action"] = True
                                if act.get("auto_enter"):
                                    settings["auto_enter_default"] = True

        data["schema_version"] = 2
        return data

    def save_config(self, config_data: Dict[str, Any]) -> bool:
        """Atomic configuration save using a temporary file and os.replace."""
        try:
            config_data["schema_version"] = DEFAULT_SCHEMA_VERSION
            fd, tmp_path = tempfile.mkstemp(
                dir=self.config_dir, prefix="cfg_tmp_", suffix=".json"
            )
            with os.fdopen(fd, "w", encoding="utf-8") as f:
                json.dump(config_data, f, ensure_ascii=False, indent=2)

            # Atomic replace
            os.replace(tmp_path, self.config_file)
            return True
        except Exception as e:
            if 'tmp_path' in locals() and os.path.exists(tmp_path):
                try:
                    os.remove(tmp_path)
                except Exception:
                    pass
            print(f"Error saving config: {e}")
            return False

    def create_backup(self) -> Optional[str]:
        """Create a timestamped backup of current config file."""
        if not os.path.exists(self.config_file):
            return None
        timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
        backup_name = f"config_backup_{timestamp}.json"
        dest = os.path.join(self.backup_dir, backup_name)
        try:
            shutil.copy2(self.config_file, dest)
            return dest
        except Exception:
            return None

    def _handle_corrupted_config(self, exc: Exception):
        timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
        corrupted_name = f"config_corrupted_{timestamp}.json"
        dest = os.path.join(self.backup_dir, corrupted_name)
        try:
            if os.path.exists(self.config_file):
                shutil.move(self.config_file, dest)
                print(f"[QuickInput] Config corrupted ({exc}), backed up to {dest} and restored default.")
        except Exception as err:
            print(f"[QuickInput] Failed to back up corrupted config: {err}")

    def _deep_update(self, base: Dict[str, Any], update: Dict[str, Any]):
        for k, v in update.items():
            if isinstance(v, dict) and k in base and isinstance(base[k], dict):
                self._deep_update(base[k], v)
            else:
                base[k] = v
