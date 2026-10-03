# -*- coding: utf-8 -*-
"""Pack store for importing, exporting, and validating .qipack packages."""

import os
import json
import zipfile
from typing import Dict, Any, List, Tuple, Optional

from domain.action import Action, VALID_STEP_TYPES
from domain.button import Button
from domain.layout import Layout


class PackValidationError(Exception):
    pass


class PackStore:
    """Manages .qipack file archive operations and strict security validations."""

    SUPPORTED_SCHEMA_VERSIONS = {1, 2}

    @classmethod
    def validate_pack_data(cls, manifest: Dict[str, Any], actions_data: Any, layouts_data: Any, buttons_data: Any) -> List[str]:
        errors = []

        # 1. Manifest validation
        if not isinstance(manifest, dict):
            errors.append("manifest.json must be a JSON object")
            return errors

        schema_ver = manifest.get("schema_version", 1)
        if schema_ver not in cls.SUPPORTED_SCHEMA_VERSIONS:
            errors.append(f"Unsupported schema_version: {schema_ver}. Supported: {sorted(cls.SUPPORTED_SCHEMA_VERSIONS)}")

        if not manifest.get("id"):
            errors.append("manifest.json missing required 'id'")
        if not manifest.get("name"):
            errors.append("manifest.json missing required 'name'")

        # 2. Actions validation
        action_ids = set()
        action_list = actions_data if isinstance(actions_data, list) else list(actions_data.values()) if isinstance(actions_data, dict) else []
        for a_dict in action_list:
            if not isinstance(a_dict, dict):
                errors.append("Action item must be a dictionary")
                continue
            act = Action.from_dict(a_dict)
            val_errs = act.validate()
            for ve in val_errs:
                errors.append(f"Action '{act.id}': {ve}")
            if act.id in action_ids:
                errors.append(f"Duplicate action ID in pack: '{act.id}'")
            action_ids.add(act.id)

            # Security check: check for dangerous commands or malformed steps
            for s in act.steps:
                if s.type not in VALID_STEP_TYPES:
                    errors.append(f"Action '{act.id}' contains unsupported step type '{s.type}'")

        # 3. Buttons validation
        button_ids = set()
        button_list = buttons_data if isinstance(buttons_data, list) else list(buttons_data.values()) if isinstance(buttons_data, dict) else []
        for b_dict in button_list:
            if not isinstance(b_dict, dict):
                continue
            btn = Button.from_dict(b_dict)
            val_errs = btn.validate()
            for ve in val_errs:
                errors.append(f"Button '{btn.id}': {ve}")
            if btn.id in button_ids:
                errors.append(f"Duplicate button ID in pack: '{btn.id}'")
            button_ids.add(btn.id)

        # 4. Layouts validation
        layout_ids = set()
        layout_list = layouts_data if isinstance(layouts_data, list) else list(layouts_data.values()) if isinstance(layouts_data, dict) else []
        for l_dict in layout_list:
            if not isinstance(l_dict, dict):
                continue
            layout = Layout.from_dict(l_dict)
            val_errs = layout.validate()
            for ve in val_errs:
                errors.append(f"Layout '{layout.id}': {ve}")
            if layout.id in layout_ids:
                errors.append(f"Duplicate layout ID in pack: '{layout.id}'")
            layout_ids.add(layout.id)

        return errors

    @classmethod
    def _migrate_pack_v1(cls, layouts: List[Layout], buttons: List[Button], actions: List[Action]):
        btn_map = {b.id: b for b in buttons}
        act_map = {a.id: a for a in actions}
        for lay in layouts:
            for slot in lay.buttons:
                btn = btn_map.get(slot.button_id)
                if btn:
                    if btn.auto_enter:
                        lay.settings.auto_enter_default = True
                    act = act_map.get(btn.action_id)
                    if act:
                        if act.confirm:
                            lay.settings.confirm_before_action = True
                        if act.auto_enter:
                            lay.settings.auto_enter_default = True

    @classmethod
    def export_pack(
        cls,
        output_file_path: str,
        manifest: Dict[str, Any],
        actions: List[Action],
        layouts: List[Layout],
        buttons: List[Button],
        readme_content: str = "",
        icon_files: Optional[Dict[str, str]] = None,
    ) -> bool:
        """Export actions, layouts, and buttons into a .qipack ZIP archive."""
        try:
            if not output_file_path.endswith(".qipack") and not output_file_path.endswith(".zip"):
                output_file_path += ".qipack"

            os.makedirs(os.path.dirname(os.path.abspath(output_file_path)), exist_ok=True)

            manifest_copy = dict(manifest)
            manifest_copy.setdefault("schema_version", 2)

            with zipfile.ZipFile(output_file_path, "w", zipfile.ZIP_DEFLATED) as zf:
                # manifest.json
                zf.writestr("manifest.json", json.dumps(manifest_copy, ensure_ascii=False, indent=2))
                # actions.json
                actions_data = [a.to_dict() for a in actions]
                zf.writestr("actions.json", json.dumps(actions_data, ensure_ascii=False, indent=2))
                # layouts.json
                layouts_data = [l.to_dict() for l in layouts]
                zf.writestr("layouts.json", json.dumps(layouts_data, ensure_ascii=False, indent=2))
                # buttons.json
                buttons_data = [b.to_dict() for b in buttons]
                zf.writestr("buttons.json", json.dumps(buttons_data, ensure_ascii=False, indent=2))
                # README.md
                if readme_content:
                    zf.writestr("README.md", readme_content)

                # Optional icons
                if icon_files:
                    for arcname, local_path in icon_files.items():
                        if os.path.exists(local_path):
                            clean_name = os.path.normpath(arcname).replace("\\", "/")
                            if not clean_name.startswith("../") and not clean_name.startswith("/"):
                                zf.write(local_path, f"icons/{clean_name}")

            return True
        except Exception as e:
            print(f"Export pack error: {e}")
            return False

    @classmethod
    def import_pack(cls, file_or_dir_path: str) -> Tuple[bool, str, Dict[str, Any]]:
        """
        Import and validate a .qipack archive or directory.
        Returns (success, message, pack_contents_dict).
        """
        if not os.path.exists(file_or_dir_path):
            return False, f"文件或目录不存在: {file_or_dir_path}", {}

        if os.path.isdir(file_or_dir_path):
            return cls._import_from_dir(file_or_dir_path)
        else:
            return cls._import_from_zip(file_or_dir_path)

    @classmethod
    def _import_from_dir(cls, dir_path: str) -> Tuple[bool, str, Dict[str, Any]]:
        manifest_path = os.path.join(dir_path, "manifest.json")
        actions_path = os.path.join(dir_path, "actions.json")
        layouts_path = os.path.join(dir_path, "layouts.json")
        buttons_path = os.path.join(dir_path, "buttons.json")

        if not os.path.exists(manifest_path):
            return False, "缺少 manifest.json", {}

        try:
            with open(manifest_path, "r", encoding="utf-8") as f:
                manifest = json.load(f)

            actions = []
            if os.path.exists(actions_path):
                with open(actions_path, "r", encoding="utf-8") as f:
                    actions = json.load(f)

            layouts = []
            if os.path.exists(layouts_path):
                with open(layouts_path, "r", encoding="utf-8") as f:
                    layouts = json.load(f)

            buttons = []
            if os.path.exists(buttons_path):
                with open(buttons_path, "r", encoding="utf-8") as f:
                    buttons = json.load(f)

            errors = cls.validate_pack_data(manifest, actions, layouts, buttons)
            if errors:
                return False, f"按钮包校验失败:\n" + "\n".join(errors[:5]), {}

            act_objs = [Action.from_dict(a) for a in actions]
            lay_objs = [Layout.from_dict(l) for l in layouts]
            btn_objs = [Button.from_dict(b) for b in buttons]

            if manifest.get("schema_version", 1) < 2:
                cls._migrate_pack_v1(lay_objs, btn_objs, act_objs)

            return True, "导入成功", {
                "manifest": manifest,
                "actions": act_objs,
                "layouts": lay_objs,
                "buttons": btn_objs,
            }
        except Exception as e:
            return False, f"读取按钮包失败: {e}", {}

    @classmethod
    def _import_from_zip(cls, zip_path: str) -> Tuple[bool, str, Dict[str, Any]]:
        try:
            with zipfile.ZipFile(zip_path, "r") as zf:
                # Security check for zip traversal
                for name in zf.namelist():
                    norm = os.path.normpath(name)
                    if norm.startswith("..") or os.path.isabs(norm):
                        return False, f"检测到不安全的压缩包文件路径: {name}", {}

                if "manifest.json" not in zf.namelist():
                    return False, "压缩包中缺少 manifest.json", {}

                manifest_raw = zf.read("manifest.json").decode("utf-8")
                manifest = json.loads(manifest_raw)

                actions_data = []
                if "actions.json" in zf.namelist():
                    actions_data = json.loads(zf.read("actions.json").decode("utf-8"))

                layouts_data = []
                if "layouts.json" in zf.namelist():
                    layouts_data = json.loads(zf.read("layouts.json").decode("utf-8"))

                buttons_data = []
                if "buttons.json" in zf.namelist():
                    buttons_data = json.loads(zf.read("buttons.json").decode("utf-8"))

                errors = cls.validate_pack_data(manifest, actions_data, layouts_data, buttons_data)
                if errors:
                    return False, f"按钮包校验失败:\n" + "\n".join(errors[:5]), {}

                act_objs = [Action.from_dict(a) for a in actions_data]
                lay_objs = [Layout.from_dict(l) for l in layouts_data]
                btn_objs = [Button.from_dict(b) for b in buttons_data]

                if manifest.get("schema_version", 1) < 2:
                    cls._migrate_pack_v1(lay_objs, btn_objs, act_objs)

                return True, "导入成功", {
                    "manifest": manifest,
                    "actions": act_objs,
                    "layouts": lay_objs,
                    "buttons": btn_objs,
                }

        except Exception as e:
            return False, f"解压按钮包失败: {e}", {}
