# -*- coding: utf-8 -*-
"""Pack store tests for exporting, importing, and validating .qipack packages."""

import os
import tempfile
from storage.pack_store import PackStore
from domain.action import Action, ActionStep
from domain.button import Button
from domain.layout import Layout, LayoutButtonSlot


def test_export_and_import_pack():
    with tempfile.TemporaryDirectory() as tmp_dir:
        pack_file = os.path.join(tmp_dir, "test_pack.qipack")

        manifest = {
            "id": "my_test_pack",
            "name": "测试工具包",
            "version": "1.0.0",
            "schema_version": 1,
            "description": "单元测试包",
        }
        actions = [
            Action(id="act_1", label="动作1", steps=[ActionStep(type="text", value="abc")]),
            Action(id="act_2", label="动作2", steps=[ActionStep(type="key", key="ENTER")]),
        ]
        buttons = [
            Button(id="btn_1", label="按钮1", action_id="act_1"),
            Button(id="btn_2", label="按钮2", action_id="act_2"),
        ]
        layouts = [
            Layout(
                id="lay_1",
                name="布局1",
                rows=1,
                columns=2,
                buttons=[
                    LayoutButtonSlot(button_id="btn_1", row=0, column=0),
                    LayoutButtonSlot(button_id="btn_2", row=0, column=1),
                ],
            )
        ]

        ok = PackStore.export_pack(
            output_file_path=pack_file,
            manifest=manifest,
            actions=actions,
            layouts=layouts,
            buttons=buttons,
            readme_content="# Readme\nTest pack readme.",
        )
        assert ok is True
        assert os.path.exists(pack_file)

        # Import
        imp_ok, msg, data = PackStore.import_pack(pack_file)
        assert imp_ok is True
        assert data["manifest"]["id"] == "my_test_pack"
        assert len(data["actions"]) == 2
        assert len(data["buttons"]) == 2
        assert len(data["layouts"]) == 1
        assert data["layouts"][0].id == "lay_1"


def test_builtin_packs_valid():
    """Verify that all 4 built-in packs (chess, annotation, customer_service, programmer) are valid."""
    base_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
    packs_dir = os.path.join(base_dir, "packs")

    for p in ["chess", "annotation", "customer_service", "programmer"]:
        p_path = os.path.join(packs_dir, p)
        assert os.path.isdir(p_path), f"Builtin pack {p} missing"
        ok, msg, data = PackStore.import_pack(p_path)
        assert ok is True, f"Builtin pack {p} failed validation: {msg}"
        assert len(data["actions"]) > 0
        assert len(data["buttons"]) > 0
        assert len(data["layouts"]) > 0


def test_pack_validation_duplicate_ids():
    manifest = {"id": "p", "name": "p", "schema_version": 1}
    actions = [
        {"id": "duplicate_id", "label": "A", "steps": []},
        {"id": "duplicate_id", "label": "B", "steps": []},
    ]
    errs = PackStore.validate_pack_data(manifest, actions, [], [])
    assert any("Duplicate action ID" in e for e in errs)
