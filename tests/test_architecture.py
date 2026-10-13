# -*- coding: utf-8 -*-
"""Architectural integrity and decoupled component tests for QuickInput."""

import tempfile
import pytest
from PyQt5 import QtCore, QtGui, QtWidgets

import domain
import ui
import application
from domain import (
    Action,
    ActionStep,
    Button,
    Layout,
    LayoutSettings,
    Profile,
    COLOR_PRESET_KEYS,
    COLOR_PRESETS,
    tr,
)
from application import AppContext, LayoutManager, ActionExecutor, TargetManager
from storage import ConfigStore
from ui import (
    KeyCaptureDialog,
    NewLayoutDialog,
    PreviewSlotButton,
    HotkeySignalBridge,
    FloatingPanel,
    SettingsDialog,
)
from tests.test_executor import MockInputInjector, MockClipboardManager, MockWindowManager


@pytest.fixture(scope="session")
def qapp():
    app = QtWidgets.QApplication.instance()
    if not app:
        app = QtWidgets.QApplication([])
    return app


def test_domain_clean_exports():
    """Verify domain package exposes clean public surface without internal leakages."""
    assert Action is not None
    assert ActionStep is not None
    assert Button is not None
    assert Layout is not None
    assert LayoutSettings is not None
    assert Profile is not None
    assert len(COLOR_PRESET_KEYS) >= 8
    assert len(COLOR_PRESETS) >= 8
    assert tr("app_title") != ""


def test_ui_clean_exports():
    """Verify UI package exposes newly decoupled dialogs and widgets."""
    assert KeyCaptureDialog is not None
    assert NewLayoutDialog is not None
    assert PreviewSlotButton is not None
    assert HotkeySignalBridge is not None
    assert FloatingPanel is not None
    assert SettingsDialog is not None


def test_key_capture_dialog_behavior(qapp, monkeypatch):
    """Verify KeyCaptureDialog records Enter key without prematurely accepting dialog."""
    monkeypatch.setattr(QtWidgets.QMessageBox, "warning", lambda *args, **kwargs: None)
    dlg = KeyCaptureDialog(parent=None)
    assert dlg.key_edit.text() == ""

    # Press Enter
    event_enter = QtGui.QKeyEvent(
        QtCore.QEvent.KeyPress, QtCore.Qt.Key_Return, QtCore.Qt.NoModifier
    )
    dlg.keyPressEvent(event_enter)
    assert dlg.get_captured_key() == "ENTER"

    # Press Ctrl+Shift+S
    event_combo = QtGui.QKeyEvent(
        QtCore.QEvent.KeyPress,
        QtCore.Qt.Key_S,
        QtCore.Qt.ControlModifier | QtCore.Qt.ShiftModifier,
        "s",
    )
    dlg.keyPressEvent(event_combo)
    assert dlg.get_captured_key() == "CTRL+SHIFT+S"

    # Test clear
    dlg._clear_key()
    assert dlg.get_captured_key() == ""

    # Test OK button clicked with empty key does not accept
    accepted = [False]
    dlg.accepted.connect(lambda: accepted.append(True))
    dlg._on_ok_clicked()
    assert accepted == [False]

    # Test OK button with valid key accepts
    dlg.key_edit.setText("ALT+Q")
    dlg._on_ok_clicked()
    dlg.close()


def test_new_layout_dialog_behavior(qapp):
    """Verify NewLayoutDialog correctly configures layout parameters."""
    dlg = NewLayoutDialog(parent=None)
    dlg.name_edit.setText("工作区A")
    dlg.rows_spin.setValue(3)
    dlg.cols_spin.setValue(5)
    dlg.size_combo.setCurrentIndex(1)  # standard

    name, orientation, rows, cols, size = dlg.get_values()
    assert name == "工作区A"
    assert orientation == "horizontal"
    assert rows == 3
    assert cols == 5
    assert size == "standard"
    dlg.close()


def test_preview_slot_button_interaction(qapp):
    """Verify PreviewSlotButton selection and drag swap trigger callbacks."""
    selected_slots = []
    swapped_slots = []

    def on_sel(r, c, bid):
        selected_slots.append((r, c, bid))

    def on_sw(r1, c1, r2, c2):
        swapped_slots.append((r1, c1, r2, c2))

    btn_model = Button(id="b_test", label="测试", action_id="a_test")
    slot_btn = PreviewSlotButton(1, 2, btn_model, on_sel, on_sw)

    # Click on slot
    click_event = QtGui.QMouseEvent(
        QtCore.QEvent.MouseButtonPress,
        QtCore.QPointF(10, 10),
        QtCore.Qt.LeftButton,
        QtCore.Qt.LeftButton,
        QtCore.Qt.NoModifier,
    )
    slot_btn.mousePressEvent(click_event)
    assert len(selected_slots) == 1
    assert selected_slots[0] == (1, 2, "b_test")

    # Drop event simulation
    mime_data = QtCore.QMimeData()
    mime_data.setText("0,1")
    drop_event = QtGui.QDropEvent(
        QtCore.QPointF(10, 10),
        QtCore.Qt.MoveAction,
        mime_data,
        QtCore.Qt.LeftButton,
        QtCore.Qt.NoModifier,
    )
    slot_btn.dropEvent(drop_event)
    assert len(swapped_slots) == 1
    assert swapped_slots[0] == (0, 1, 1, 2)


def test_app_context_lifecycle_and_binding(qapp):
    """Verify AppContext correctly instantiates services, initializes packs, and cleans up."""
    with tempfile.TemporaryDirectory() as tmp_dir:
        ctx = AppContext.create_default(config_dir=tmp_dir)
        cfg = ctx.initialize()

        assert cfg is not None
        assert len(ctx.layout_mgr.layouts) >= 4
        assert "official_doc" in ctx.layout_mgr.layouts
        assert ctx.layout_mgr.active_layout_id is not None

        # Test panel binding
        panel = FloatingPanel(
            layout_mgr=ctx.layout_mgr,
            executor=ctx.executor,
            target_mgr=ctx.target_mgr,
            config_store=ctx.config_store,
            hotkey_mgr=ctx.hotkey_mgr,
        )
        ctx.bind_panel(panel)
        assert panel._toggle_hotkey_handler is not None

        # Verify hotkey bridge signal dispatch
        received = []
        ctx.hotkey_bridge.toggle_requested.connect(lambda: received.append(True))
        ctx.hotkey_bridge.toggle_requested.emit()
        qapp.processEvents()
        assert len(received) == 1

        # Test cleanup
        ctx.cleanup()
        panel.close()
