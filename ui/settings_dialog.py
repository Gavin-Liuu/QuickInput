# -*- coding: utf-8 -*-
"""Comprehensive settings center with layout-first preview and contextual button editing."""

from typing import Optional, Dict, Tuple
from PyQt5 import QtCore, QtGui, QtWidgets

import os
from domain.action import Action, ActionStep
from domain.button import Button
from domain.layout import Layout
from domain.profile import Profile
from domain.i18n import tr, get_current_language, set_current_language
from application.layout_manager import LayoutManager
from application.action_executor import ActionExecutor
from application.target_manager import TargetManager
from storage.config_store import ConfigStore
from storage.pack_store import PackStore
from .macro_recorder_dialog import MacroRecorderDialog
from application.macro_recorder import MacroRecorder

COLOR_PRESET_KEYS = [
    ("#1976D2", "color_blue"),
    ("#E53935", "color_red"),
    ("#37474F", "color_gray"),
    ("#2E7D32", "color_green"),
    ("#7B1FA2", "color_purple"),
    ("#FB8C00", "color_orange"),
    ("#0284C7", "color_sky"),
    ("#4F46E5", "color_indigo"),
]
COLOR_PRESETS = [("#1976D2", "蓝色"), ("#E53935", "朱红"), ("#37474F", "深灰"), ("#2E7D32", "绿色"), ("#7B1FA2", "紫色"), ("#FB8C00", "橙色"), ("#0284C7", "青天蓝"), ("#4F46E5", "靛蓝")]


class KeyCaptureDialog(QtWidgets.QDialog):
    """Dialog for capturing individual keypresses or hotkey combinations.

    CRITICAL: Pressing Enter/Return or Space does NOT close/accept the dialog!
    It is recorded as the key itself into the key capture display.
    Only explicitly clicking the OK button confirms and saves the key.
    """

    def __init__(self, initial_key: str = "", parent=None):
        super().__init__(parent)
        self.setWindowTitle(tr("key_capture_title"))
        self.setFixedSize(380, 160)
        self.setWindowFlags(self.windowFlags() & ~QtCore.Qt.WindowContextHelpButtonHint)
        self.setStyleSheet("""
            QDialog {
                background-color: #1A1A20;
                color: #F0F0F5;
                font-family: "Segoe UI Variable Text", "Segoe UI", "PingFang SC", "Microsoft YaHei UI", sans-serif;
            }
            QLabel {
                color: #D8D8E5;
                font-size: 12px;
            }
            QLineEdit {
                background: #141418;
                color: #00E676;
                font-family: "Consolas", "Segoe UI", monospace;
                font-size: 16px;
                font-weight: 700;
                border: 2px solid #0A84FF;
                border-radius: 6px;
                padding: 6px 10px;
            }
            QPushButton {
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1, stop:0 #2C2C36, stop:1 #22222A);
                color: #F0F0F5;
                border: 1px solid #3A3A48;
                border-radius: 5px;
                padding: 6px 16px;
                font-size: 12px;
                font-weight: 600;
            }
            QPushButton:hover {
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1, stop:0 #383846, stop:1 #2A2A34);
                border-color: #55556C;
                color: #FFFFFF;
            }
            QPushButton:pressed {
                background: #181820;
                padding-top: 7px;
                padding-left: 17px;
            }
            QPushButton#OkBtn {
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1, stop:0 #0A84FF, stop:1 #0066CC);
                border: 1px solid #0A84FF;
                color: #FFFFFF;
            }
            QPushButton#OkBtn:hover {
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1, stop:0 #2492FF, stop:1 #0A7AE5);
                border-color: #66B2FF;
            }
        """)

        layout = QtWidgets.QVBoxLayout(self)
        layout.setContentsMargins(18, 16, 18, 16)
        layout.setSpacing(12)

        info_label = QtWidgets.QLabel(tr("key_capture_instruction"), self)
        info_label.setWordWrap(True)
        layout.addWidget(info_label)

        self.key_edit = QtWidgets.QLineEdit(self)
        self.key_edit.setReadOnly(True)
        self.key_edit.setAlignment(QtCore.Qt.AlignCenter)
        self.key_edit.setPlaceholderText(tr("key_capture_input_placeholder"))
        self.key_edit.setText(initial_key)
        layout.addWidget(self.key_edit)

        btn_layout = QtWidgets.QHBoxLayout()
        btn_layout.setSpacing(10)

        self.clear_btn = QtWidgets.QPushButton(tr("btn_clear"), self)
        self.clear_btn.setAutoDefault(False)
        self.clear_btn.setDefault(False)
        self.clear_btn.setFocusPolicy(QtCore.Qt.NoFocus)
        self.clear_btn.clicked.connect(self._clear_key)
        btn_layout.addWidget(self.clear_btn)

        btn_layout.addStretch()

        self.cancel_btn = QtWidgets.QPushButton(tr("btn_cancel_settings"), self)
        self.cancel_btn.setAutoDefault(False)
        self.cancel_btn.setDefault(False)
        self.cancel_btn.setFocusPolicy(QtCore.Qt.NoFocus)
        self.cancel_btn.clicked.connect(self.reject)
        btn_layout.addWidget(self.cancel_btn)

        self.ok_btn = QtWidgets.QPushButton(tr("btn_ok"), self)
        self.ok_btn.setObjectName("OkBtn")
        self.ok_btn.setAutoDefault(False)
        self.ok_btn.setDefault(False)
        self.ok_btn.setFocusPolicy(QtCore.Qt.NoFocus)
        self.ok_btn.clicked.connect(self._on_ok_clicked)
        btn_layout.addWidget(self.ok_btn)

        layout.addLayout(btn_layout)
        self.setFocusPolicy(QtCore.Qt.StrongFocus)
        self.setFocus()

    def _clear_key(self):
        self.key_edit.clear()

    def _on_ok_clicked(self):
        if not self.key_edit.text().strip():
            QtWidgets.QMessageBox.warning(self, tr("prompt_notice"), tr("prompt_record_key_first"))
            return
        self.accept()

    def get_captured_key(self) -> str:
        return self.key_edit.text().strip().upper()

    def keyPressEvent(self, event: QtGui.QKeyEvent):
        key = event.key()

        # Pure modifier key pressed alone: do not treat as final key
        if key in (QtCore.Qt.Key_Control, QtCore.Qt.Key_Shift, QtCore.Qt.Key_Alt, QtCore.Qt.Key_Meta):
            event.accept()
            return

        mods = []
        modifiers = event.modifiers()
        if modifiers & QtCore.Qt.ControlModifier:
            mods.append("CTRL")
        if modifiers & QtCore.Qt.AltModifier:
            mods.append("ALT")
        if modifiers & QtCore.Qt.ShiftModifier:
            mods.append("SHIFT")
        if modifiers & QtCore.Qt.MetaModifier:
            mods.append("WIN")

        special_map = {
            QtCore.Qt.Key_Return: "ENTER",
            QtCore.Qt.Key_Enter: "ENTER",
            QtCore.Qt.Key_Tab: "TAB",
            QtCore.Qt.Key_Backtab: "TAB",
            QtCore.Qt.Key_Escape: "ESC",
            QtCore.Qt.Key_Space: "SPACE",
            QtCore.Qt.Key_Backspace: "BACKSPACE",
            QtCore.Qt.Key_Delete: "DELETE",
            QtCore.Qt.Key_Insert: "INSERT",
            QtCore.Qt.Key_Home: "HOME",
            QtCore.Qt.Key_End: "END",
            QtCore.Qt.Key_PageUp: "PAGEUP",
            QtCore.Qt.Key_PageDown: "PAGEDOWN",
            QtCore.Qt.Key_Left: "LEFT",
            QtCore.Qt.Key_Right: "RIGHT",
            QtCore.Qt.Key_Up: "UP",
            QtCore.Qt.Key_Down: "DOWN",
            QtCore.Qt.Key_F1: "F1", QtCore.Qt.Key_F2: "F2", QtCore.Qt.Key_F3: "F3", QtCore.Qt.Key_F4: "F4",
            QtCore.Qt.Key_F5: "F5", QtCore.Qt.Key_F6: "F6", QtCore.Qt.Key_F7: "F7", QtCore.Qt.Key_F8: "F8",
            QtCore.Qt.Key_F9: "F9", QtCore.Qt.Key_F10: "F10", QtCore.Qt.Key_F11: "F11", QtCore.Qt.Key_F12: "F12",
            QtCore.Qt.Key_Plus: "=",
            QtCore.Qt.Key_Equal: "=",
            QtCore.Qt.Key_Minus: "-",
            QtCore.Qt.Key_Asterisk: "*",
            QtCore.Qt.Key_Slash: "/",
        }

        key_name = ""
        if key in special_map:
            key_name = special_map[key]
        elif 0x20 <= key <= 0x7E:
            key_name = chr(key).upper()
        else:
            text = event.text().strip().upper()
            if text:
                key_name = text
            else:
                key_name = QtGui.QKeySequence(key).toString().upper()

        if not key_name:
            event.accept()
            return

        if key_name in mods:
            event.accept()
            return

        if mods:
            combo = "+".join(mods + [key_name])
        else:
            combo = key_name

        self.key_edit.setText(combo)
        event.accept()


class NewLayoutDialog(QtWidgets.QDialog):
    """Wizard dialog for creating a new layout with presets."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle(tr("prompt_new_layout_title"))
        self.setMinimumWidth(380)
        self.setStyleSheet("""
            QDialog {
                background-color: #1E1E20;
                color: #F5F5F7;
                font-family: "Segoe UI Variable Text", "Segoe UI", "PingFang SC", "Microsoft YaHei UI", sans-serif;
            }
            QLabel {
                color: #F5F5F7;
                font-size: 12px;
            }
            QLineEdit, QComboBox, QSpinBox {
                background-color: #1C1C1E;
                color: #FFFFFF;
                border: 1px solid rgba(255, 255, 255, 0.12);
                padding: 6px 10px;
                border-radius: 6px;
                font-size: 12px;
            }
            QLineEdit:focus, QComboBox:focus, QSpinBox:focus {
                border: 1.5px solid #0A84FF;
            }
            QPushButton {
                background-color: rgba(255, 255, 255, 0.08);
                color: #F5F5F7;
                border: 1px solid rgba(255, 255, 255, 0.10);
                padding: 6px 16px;
                border-radius: 6px;
                font-size: 12px;
                font-weight: 500;
            }
            QPushButton:hover {
                background-color: rgba(255, 255, 255, 0.14);
                border-color: rgba(255, 255, 255, 0.20);
            }
            QPushButton:pressed {
                background-color: rgba(255, 255, 255, 0.05);
            }
        """)

        layout = QtWidgets.QFormLayout(self)
        layout.setSpacing(10)
        layout.setContentsMargins(16, 16, 16, 16)

        self.name_edit = QtWidgets.QLineEdit(self)
        self.name_edit.setText(tr("prompt_new_layout_default"))
        layout.addRow(tr("layout_select_label"), self.name_edit)

        self.rows_spin = QtWidgets.QSpinBox(self)
        self.rows_spin.setRange(1, 20)
        self.rows_spin.setValue(2)
        layout.addRow(tr("rows_label"), self.rows_spin)

        self.cols_spin = QtWidgets.QSpinBox(self)
        self.cols_spin.setRange(1, 20)
        self.cols_spin.setValue(4)
        layout.addRow(tr("cols_label"), self.cols_spin)

        self.size_combo = QtWidgets.QComboBox(self)
        self.size_combo.addItems([tr("size_compact"), tr("size_standard"), tr("size_touch")])
        layout.addRow(tr("btn_size_label"), self.size_combo)

        btn_box = QtWidgets.QDialogButtonBox(
            QtWidgets.QDialogButtonBox.Ok | QtWidgets.QDialogButtonBox.Cancel, self
        )
        btn_box.button(QtWidgets.QDialogButtonBox.Ok).setText(tr("btn_ok"))
        btn_box.button(QtWidgets.QDialogButtonBox.Cancel).setText(tr("btn_cancel_settings"))
        btn_box.accepted.connect(self.accept)
        btn_box.rejected.connect(self.reject)
        layout.addRow(btn_box)

    def get_values(self):
        size_key = ["compact", "standard", "touch"][self.size_combo.currentIndex()]
        return (
            self.name_edit.text().strip() or tr("prompt_new_layout_default"),
            "horizontal",
            self.rows_spin.value(),
            self.cols_spin.value(),
            size_key,
        )


class PreviewSlotButton(QtWidgets.QPushButton):
    """Button widget for layout preview supporting click selection and drag-drop swapping."""

    def __init__(
        self,
        row: int,
        col: int,
        button_model: Optional[Button],
        on_select,
        on_swap,
        parent=None,
    ):
        super().__init__(parent)
        self.row = row
        self.col = col
        self.button_model = button_model
        self.on_select = on_select
        self.on_swap = on_swap
        self.setAcceptDrops(True)
        self._drag_start_pos = None

    def mousePressEvent(self, event):
        if event.button() == QtCore.Qt.LeftButton:
            self._drag_start_pos = event.pos()
            self.on_select(self.row, self.col, self.button_model.id if self.button_model else None)
        super().mousePressEvent(event)

    def mouseMoveEvent(self, event):
        if not (event.buttons() & QtCore.Qt.LeftButton) or not self._drag_start_pos or not self.button_model:
            return
        if (event.pos() - self._drag_start_pos).manhattanLength() < QtWidgets.QApplication.startDragDistance():
            return
        drag = QtGui.QDrag(self)
        mime = QtCore.QMimeData()
        mime.setText(f"{self.row},{self.col}")
        drag.setMimeData(mime)
        drag.exec_(QtCore.Qt.MoveAction)

    def dragEnterEvent(self, event):
        if event.mimeData().hasText():
            event.acceptProposedAction()

    def dropEvent(self, event):
        text = event.mimeData().text()
        try:
            parts = text.split(",")
            if len(parts) == 2:
                src_r, src_c = int(parts[0]), int(parts[1])
                if (src_r, src_c) != (self.row, self.col):
                    self.on_swap(src_r, src_c, self.row, self.col)
                    event.acceptProposedAction()
        except Exception:
            pass


class SettingsDialog(QtWidgets.QDialog):
    """Layout and button editor designed around the user's current layout."""

    def __init__(
        self,
        layout_mgr: LayoutManager,
        executor: ActionExecutor,
        target_mgr: TargetManager,
        config_store: ConfigStore,
        parent=None,
    ):
        super().__init__(parent)
        self.layout_mgr = layout_mgr
        self.executor = executor
        self.target_mgr = target_mgr
        self.config_store = config_store
        self._loading = False
        self._preview_widgets: Dict[Tuple[int, int], QtWidgets.QPushButton] = {}
        self._preview_font_size = 10
        self.selected_row: Optional[int] = None
        self.selected_col: Optional[int] = None
        self.selected_button_id: Optional[str] = None

        self.setWindowTitle(tr("settings_title"))
        flags = (
            QtCore.Qt.Window
            | QtCore.Qt.WindowTitleHint
            | QtCore.Qt.WindowSystemMenuHint
            | QtCore.Qt.WindowMinimizeButtonHint
            | QtCore.Qt.WindowMaximizeButtonHint
            | QtCore.Qt.WindowCloseButtonHint
        )
        self.setWindowFlags(flags)
        self.setMinimumSize(480, 320)
        screen = QtGui.QGuiApplication.primaryScreen().availableGeometry()
        target_w = min(1040, max(720, screen.width() - 80))
        target_h = min(740, max(500, screen.height() - 80))
        self.resize(target_w, target_h)

        self.setStyleSheet("""
            QDialog, QScrollArea, QScrollArea > QWidget > QWidget {
                background-color: #1A1A20;
                color: #F0F0F5;
                font-family: "Segoe UI Variable Text", "Segoe UI", "PingFang SC", "Microsoft YaHei UI", sans-serif;
            }
            QWidget {
                font-family: "Segoe UI Variable Text", "Segoe UI", "PingFang SC", "Microsoft YaHei UI", sans-serif;
                color: #F0F0F5;
            }
            QGroupBox {
                background-color: #202028;
                border: 1px solid #32323E;
                border-radius: 8px;
                margin-top: 14px;
                padding-top: 16px;
                padding-bottom: 12px;
                padding-left: 12px;
                padding-right: 12px;
                color: #F0F0F5;
                font-weight: 600;
            }
            QGroupBox::title {
                subcontrol-origin: margin;
                subcontrol-position: top left;
                left: 10px;
                top: 1px;
                padding: 1px 8px;
                background-color: #1A1A20;
                border: 1px solid #32323E;
                border-radius: 4px;
                color: #D8D8E5;
                font-weight: 600;
                font-size: 11px;
            }
            QLabel {
                color: #D8D8E5;
                font-size: 11px;
            }
            QLineEdit, QComboBox, QSpinBox, QTextEdit {
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1, stop:0 #141418, stop:1 #1C1C22);
                color: #F0F0F5;
                border: 1px solid #383846;
                border-radius: 5px;
                padding: 4px 8px;
                font-size: 11px;
            }
            QLineEdit:hover, QComboBox:hover, QSpinBox:hover, QTextEdit:hover {
                border-color: #55556C;
            }
            QLineEdit:focus, QComboBox:focus, QSpinBox:focus, QTextEdit:focus {
                border: 1.5px solid #0A84FF;
                background-color: #1E1E28;
            }
            QComboBox::drop-down {
                subcontrol-origin: padding;
                subcontrol-position: top right;
                width: 18px;
                border: none;
                background: transparent;
            }
            QComboBox QAbstractItemView {
                background-color: #202028;
                color: #F0F0F5;
                border: 1px solid #3E3E50;
                border-radius: 6px;
                padding: 4px;
                selection-background-color: #0A84FF;
                selection-color: #FFFFFF;
                outline: none;
                font-size: 11px;
            }
            QTableWidget {
                background-color: #141418;
                color: #F0F0F5;
                border: 1px solid #32323E;
                border-radius: 6px;
                gridline-color: #22222A;
                outline: none;
                font-size: 11px;
            }
            QTableWidget::item {
                padding: 3px 6px;
                border-bottom: 1px solid #1C1C24;
            }
            QTableWidget::item:selected {
                background-color: #0A84FF;
                color: #FFFFFF;
            }
            QHeaderView::section {
                background-color: #1E1E26;
                color: #9A9AB0;
                border: none;
                border-bottom: 1px solid #32323E;
                padding: 5px;
                font-size: 11px;
                font-weight: 600;
            }
            QTableCornerButton::section {
                background-color: #1E1E26;
                border: none;
                border-bottom: 1px solid #32323E;
            }
            QPushButton {
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1, stop:0 #2C2C36, stop:1 #22222A);
                color: #F0F0F5;
                border: 1px solid #3A3A48;
                border-radius: 5px;
                padding: 5px 12px;
                font-size: 11px;
                font-weight: 500;
            }
            QPushButton:hover {
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1, stop:0 #383846, stop:1 #2A2A34);
                border-color: #55556C;
                color: #FFFFFF;
            }
            QPushButton:pressed {
                background: #181820;
                border-color: #282834;
                padding-top: 6px;
                padding-left: 13px;
            }
            QPushButton:disabled {
                background: #181820;
                color: #585868;
                border-color: #282832;
            }
            QCheckBox {
                color: #F0F0F5;
                font-size: 11px;
                spacing: 6px;
            }
            QScrollBar:vertical {
                background: transparent;
                width: 6px;
                margin: 0px;
            }
            QScrollBar::handle:vertical {
                background: #383846;
                border-radius: 3px;
                min-height: 20px;
            }
            QScrollBar::handle:vertical:hover {
                background: #55556C;
            }
            QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical,
            QScrollBar::add-page:vertical, QScrollBar::sub-page:vertical {
                background: none;
                height: 0px;
            }
            QScrollBar:horizontal {
                background: transparent;
                height: 6px;
                margin: 0px;
            }
            QScrollBar::handle:horizontal {
                background: #383846;
                border-radius: 3px;
                min-width: 20px;
            }
            QScrollBar::handle:horizontal:hover {
                background: #55556C;
            }
            QScrollBar::add-line:horizontal, QScrollBar::sub-line:horizontal,
            QScrollBar::add-page:horizontal, QScrollBar::sub-page:horizontal {
                background: none;
                width: 0px;
            }
            QScrollBar::corner {
                background: transparent;
            }
        """)

        self._build_ui()
        self._refresh_layout_selector()
        self._load_active_layout()

    def showEvent(self, event):
        super().showEvent(event)
        try:
            import win32gui, win32con
            hwnd = int(self.winId())
            self.target_mgr.register_own_hwnd(hwnd)
            win32gui.SetWindowPos(
                hwnd,
                win32con.HWND_NOTOPMOST,
                0, 0, 0, 0,
                win32con.SWP_NOMOVE | win32con.SWP_NOSIZE | win32con.SWP_NOACTIVATE,
            )
        except Exception:
            pass
        if hasattr(self, "splitter") and not getattr(self, "_splitter_initialized", False):
            self._splitter_initialized = True
            self.splitter.setSizes([450, 540])

    def _build_ui(self):
        root = QtWidgets.QVBoxLayout(self)
        root.setContentsMargins(14, 12, 14, 12)
        root.setSpacing(10)

        # Tab widget with only 2 top-level tabs
        self.tabs = QtWidgets.QTabWidget(self)
        self.tabs.setStyleSheet("""
            QTabWidget::pane {
                border: 1px solid #32323E;
                background-color: #1A1A20;
                border-radius: 6px;
            }
            QTabBar::tab {
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1, stop:0 #25252E, stop:1 #1C1C22);
                color: #A0A0B2;
                border: 1px solid #32323E;
                border-bottom: none;
                border-top-left-radius: 6px;
                border-top-right-radius: 6px;
                padding: 6px 18px;
                margin-right: 3px;
                font-size: 11px;
                font-weight: 600;
            }
            QTabBar::tab:selected {
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1, stop:0 #2C2C38, stop:1 #202028);
                color: #FFFFFF;
                border-bottom: 2px solid #0A84FF;
            }
            QTabBar::tab:hover:!selected {
                background: #282832;
                color: #D8D8E5;
            }
        """)
        root.addWidget(self.tabs, 1)

        # 1. 布局与按钮
        self._build_layout_and_buttons_tab()

        # 2. 常规与诊断
        self._build_general_and_diag_tab()

        # Bottom actions
        bottom = QtWidgets.QHBoxLayout()
        bottom.addStretch()
        self.save_btn = QtWidgets.QPushButton(tr("btn_save_settings"), self)
        self.save_btn.setStyleSheet("""
            QPushButton {
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1, stop:0 #0A84FF, stop:1 #0066CC);
                color: #FFFFFF;
                font-weight: 600;
                padding: 6px 22px;
                border-radius: 5px;
                border: 1px solid #0A84FF;
                font-size: 12px;
            }
            QPushButton:hover {
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1, stop:0 #2492FF, stop:1 #0A7AE5);
                border-color: #66B2FF;
            }
            QPushButton:pressed {
                background: #005BB5;
                padding-top: 7px;
                padding-left: 23px;
            }
        """)
        self.save_btn.clicked.connect(self.save_and_close)
        bottom.addWidget(self.save_btn)

        self.cancel_btn = QtWidgets.QPushButton(tr("btn_cancel_settings"), self)
        self.cancel_btn.setStyleSheet("""
            QPushButton {
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1, stop:0 #2C2C36, stop:1 #22222A);
                color: #F0F0F5;
                font-weight: 500;
                padding: 6px 18px;
                border-radius: 5px;
                border: 1px solid #3A3A48;
                font-size: 12px;
            }
            QPushButton:hover {
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1, stop:0 #383846, stop:1 #2A2A34);
                border-color: #55556C;
                color: #FFFFFF;
            }
            QPushButton:pressed {
                background: #181820;
                padding-top: 7px;
                padding-left: 19px;
            }
        """)
        self.cancel_btn.clicked.connect(self.reject)
        bottom.addWidget(self.cancel_btn)
        root.addLayout(bottom)

    def _build_layout_and_buttons_tab(self):
        tab = QtWidgets.QWidget()
        tab_layout = QtWidgets.QVBoxLayout(tab)
        tab_layout.setContentsMargins(10, 10, 10, 10)
        tab_layout.setSpacing(8)

        # Top layout selector & actions
        top_bar = QtWidgets.QHBoxLayout()
        self.lbl_curr_layout = QtWidgets.QLabel(tr("layout_select_label"), tab)
        top_bar.addWidget(self.lbl_curr_layout)
        self.layout_selector = QtWidgets.QComboBox(tab)
        self.layout_selector.setMinimumWidth(180)
        self.layout_selector.currentIndexChanged.connect(self._on_layout_selected)
        top_bar.addWidget(self.layout_selector, 1)

        self.new_layout_btn = QtWidgets.QPushButton(tr("btn_new_layout"), tab)
        self.new_layout_btn.clicked.connect(self._new_layout)
        top_bar.addWidget(self.new_layout_btn)

        self.copy_layout_btn = QtWidgets.QPushButton(tr("btn_copy_layout"), tab)
        self.copy_layout_btn.clicked.connect(self._copy_layout)
        top_bar.addWidget(self.copy_layout_btn)

        self.rename_layout_btn = QtWidgets.QPushButton(tr("btn_rename_layout"), tab)
        self.rename_layout_btn.clicked.connect(self._rename_layout)
        top_bar.addWidget(self.rename_layout_btn)

        self.delete_layout_btn = QtWidgets.QPushButton(tr("btn_del_layout"), tab)
        self.delete_layout_btn.clicked.connect(self._delete_layout)
        top_bar.addWidget(self.delete_layout_btn)

        self.reset_layout_btn = QtWidgets.QPushButton(tr("btn_reset_preset"), tab)
        self.reset_layout_btn.setToolTip(tr("btn_reset_preset_tip"))
        self.reset_layout_btn.clicked.connect(self._reset_current_layout_to_preset)
        top_bar.addWidget(self.reset_layout_btn)
        tab_layout.addLayout(top_bar)

        # Layout-level properties box (rows, cols, size, opacity, auto-enter, confirm)
        self.layout_box = QtWidgets.QGroupBox(tr("layout_props_title"), tab)
        l_form = QtWidgets.QGridLayout(self.layout_box)
        l_form.setHorizontalSpacing(14)
        l_form.setVerticalSpacing(8)

        # Row 0: Rows, Columns, Button Size
        self.lbl_rows = QtWidgets.QLabel(tr("rows_label"))
        l_form.addWidget(self.lbl_rows, 0, 0)
        self.rows_spin = QtWidgets.QSpinBox(self.layout_box)
        self.rows_spin.setRange(1, 20)
        self.rows_spin.valueChanged.connect(self._layout_property_changed)
        l_form.addWidget(self.rows_spin, 0, 1)

        self.lbl_cols = QtWidgets.QLabel(tr("cols_label"))
        l_form.addWidget(self.lbl_cols, 0, 2)
        self.cols_spin = QtWidgets.QSpinBox(self.layout_box)
        self.cols_spin.setRange(1, 20)
        self.cols_spin.valueChanged.connect(self._layout_property_changed)
        l_form.addWidget(self.cols_spin, 0, 3)

        self.lbl_btn_size = QtWidgets.QLabel(tr("btn_size_label"))
        l_form.addWidget(self.lbl_btn_size, 0, 4)
        self.size_combo = QtWidgets.QComboBox(self.layout_box)
        self.size_combo.addItems([tr("size_compact"), tr("size_standard"), tr("size_touch")])
        self.size_combo.currentIndexChanged.connect(self._layout_property_changed)
        l_form.addWidget(self.size_combo, 0, 5)

        # Row 1: Opacity, Always On Top, Confirm, Auto-Enter
        self.lbl_opacity = QtWidgets.QLabel(tr("opacity_slider_label"))
        l_form.addWidget(self.lbl_opacity, 1, 0)
        self.opacity_slider = QtWidgets.QSlider(QtCore.Qt.Horizontal, self.layout_box)
        self.opacity_slider.setRange(30, 100)
        self.opacity_slider.valueChanged.connect(self._layout_property_changed)
        l_form.addWidget(self.opacity_slider, 1, 1)

        self.always_on_top_chk = QtWidgets.QCheckBox(tr("always_on_top_chk"), self.layout_box)
        self.always_on_top_chk.stateChanged.connect(self._layout_property_changed)
        l_form.addWidget(self.always_on_top_chk, 1, 2)

        self.confirm_action_chk = QtWidgets.QCheckBox(tr("confirm_action_chk"), self.layout_box)
        self.confirm_action_chk.setToolTip(tr("confirm_action_tip"))
        self.confirm_action_chk.stateChanged.connect(self._layout_property_changed)
        l_form.addWidget(self.confirm_action_chk, 1, 3)

        self.auto_enter_chk = QtWidgets.QCheckBox(tr("auto_enter_chk"), self.layout_box)
        self.auto_enter_chk.setToolTip(tr("auto_enter_tip"))
        self.auto_enter_chk.stateChanged.connect(self._layout_property_changed)
        l_form.addWidget(self.auto_enter_chk, 1, 4, 1, 2)

        tab_layout.addWidget(self.layout_box)

        # Main Splitter: Left Preview vs Right Button & Action Editor
        splitter = QtWidgets.QSplitter(QtCore.Qt.Horizontal, tab)
        self.splitter = splitter
        splitter.setStyleSheet("QSplitter::handle { background: rgba(255, 255, 255, 0.08); width: 3px; border-radius: 1.5px; } QSplitter::handle:hover { background: #0A84FF; }")
        splitter.setChildrenCollapsible(False)

        # LEFT: Layout Preview
        left_widget = QtWidgets.QWidget(splitter)
        left_layout = QtWidgets.QVBoxLayout(left_widget)
        left_layout.setContentsMargins(0, 0, 4, 0)
        left_layout.setSpacing(6)

        preview_header = QtWidgets.QVBoxLayout()
        preview_header.setSpacing(4)

        top_preview_bar = QtWidgets.QHBoxLayout()
        self.preview_lbl = QtWidgets.QLabel(tr("preview_lbl"), left_widget)
        self.preview_lbl.setToolTip(tr("preview_tip"))
        top_preview_bar.addWidget(self.preview_lbl)
        self.preview_hint = QtWidgets.QLabel(tr("preview_hint"), left_widget)
        self.preview_hint.setStyleSheet("color: #8E8E93; font-size: 11px;")
        top_preview_bar.addWidget(self.preview_hint)
        top_preview_bar.addStretch()

        self.transpose_btn = QtWidgets.QPushButton(tr("btn_transpose"), left_widget)
        self.transpose_btn.setToolTip(tr("btn_transpose_tip"))
        self.transpose_btn.clicked.connect(self._transpose_layout)
        top_preview_bar.addWidget(self.transpose_btn)

        self.clear_slot_btn = QtWidgets.QPushButton(tr("btn_clear_slot"), left_widget)
        self.clear_slot_btn.setToolTip(tr("btn_clear_slot_tip"))
        self.clear_slot_btn.clicked.connect(self._clear_selected_slot)
        top_preview_bar.addWidget(self.clear_slot_btn)
        preview_header.addLayout(top_preview_bar)

        slot_nav_bar = QtWidgets.QHBoxLayout()
        self.lbl_slot_adjust = QtWidgets.QLabel(tr("slot_adjust_label"), left_widget)
        slot_nav_bar.addWidget(self.lbl_slot_adjust)
        self.slot_up_btn = QtWidgets.QPushButton(tr("btn_slot_up"), left_widget)
        self.slot_up_btn.clicked.connect(lambda: self._move_slot(-1, 0))
        slot_nav_bar.addWidget(self.slot_up_btn)

        self.slot_down_btn = QtWidgets.QPushButton(tr("btn_slot_down"), left_widget)
        self.slot_down_btn.clicked.connect(lambda: self._move_slot(1, 0))
        slot_nav_bar.addWidget(self.slot_down_btn)

        self.slot_left_btn = QtWidgets.QPushButton(tr("btn_slot_left"), left_widget)
        self.slot_left_btn.clicked.connect(lambda: self._move_slot(0, -1))
        slot_nav_bar.addWidget(self.slot_left_btn)

        self.slot_right_btn = QtWidgets.QPushButton(tr("btn_slot_right"), left_widget)
        self.slot_right_btn.clicked.connect(lambda: self._move_slot(0, 1))
        slot_nav_bar.addWidget(self.slot_right_btn)
        slot_nav_bar.addStretch()
        preview_header.addLayout(slot_nav_bar)

        left_layout.addLayout(preview_header)

        # Scroll area for the preview grid
        scroll = QtWidgets.QScrollArea(left_widget)
        scroll.setWidgetResizable(True)
        scroll.setStyleSheet("QScrollArea { border: 1px solid rgba(255, 255, 255, 0.08); border-radius: 8px; background-color: #18181A; }")
        scroll.viewport().setStyleSheet("background-color: #18181A;")
        self.preview_container = QtWidgets.QWidget()
        self.preview_container.setStyleSheet("background-color: #18181A;")
        self.preview_grid = QtWidgets.QGridLayout(self.preview_container)
        self.preview_grid.setContentsMargins(12, 12, 12, 12)
        self.preview_grid.setSpacing(6)
        scroll.setWidget(self.preview_container)
        left_layout.addWidget(scroll, 1)

        splitter.addWidget(left_widget)

        # RIGHT: Selected Button Properties, Steps, and Bindings (inside scroll area to allow dialog shrinking)
        right_scroll = QtWidgets.QScrollArea(splitter)
        right_scroll.setWidgetResizable(True)
        right_scroll.setFrameShape(QtWidgets.QFrame.NoFrame)
        right_scroll.setStyleSheet("QScrollArea { border: none; background-color: #1E1E20; }")
        right_scroll.viewport().setStyleSheet("background-color: #1E1E20;")

        right_widget = QtWidgets.QWidget()
        right_widget.setStyleSheet("background-color: #1E1E20;")
        right_layout = QtWidgets.QVBoxLayout(right_widget)
        right_layout.setContentsMargins(4, 0, 8, 0)
        right_layout.setSpacing(6)

        # Button properties box
        self.btn_prop_box = QtWidgets.QGroupBox(tr("btn_props_title"), right_widget)
        bp_grid = QtWidgets.QGridLayout(self.btn_prop_box)
        bp_grid.setSpacing(6)

        self.selected_info_label = QtWidgets.QLabel(tr("no_btn_selected"), self.btn_prop_box)
        self.selected_info_label.setStyleSheet("color: #0A84FF; font-weight: 600; font-size: 12px;")
        self.lbl_slot_status = QtWidgets.QLabel(tr("slot_status_label"))
        bp_grid.addWidget(self.lbl_slot_status, 0, 0)
        bp_grid.addWidget(self.selected_info_label, 0, 1, 1, 3)

        self.lbl_display_text = QtWidgets.QLabel(tr("btn_text_label"))
        bp_grid.addWidget(self.lbl_display_text, 1, 0)
        self.btn_label_edit = QtWidgets.QLineEdit(self.btn_prop_box)
        self.btn_label_edit.setPlaceholderText(tr("btn_text_placeholder"))
        self.btn_label_edit.setToolTip(tr("btn_text_tip"))
        self.btn_label_edit.textChanged.connect(self._button_property_changed)
        bp_grid.addWidget(self.btn_label_edit, 1, 1)

        self.lbl_btn_color = QtWidgets.QLabel(tr("btn_color_label"))
        bp_grid.addWidget(self.lbl_btn_color, 1, 2)
        self.btn_color_combo = QtWidgets.QComboBox(self.btn_prop_box)
        for hex_code, color_key in COLOR_PRESET_KEYS:
            self.btn_color_combo.addItem(tr(color_key), hex_code)
        self.btn_color_combo.currentIndexChanged.connect(self._button_property_changed)
        bp_grid.addWidget(self.btn_color_combo, 1, 3)

        self.lbl_btn_tooltip = QtWidgets.QLabel(tr("btn_tooltip_label"))
        bp_grid.addWidget(self.lbl_btn_tooltip, 2, 0)
        self.btn_tooltip_edit = QtWidgets.QLineEdit(self.btn_prop_box)
        self.btn_tooltip_edit.textChanged.connect(self._button_property_changed)
        bp_grid.addWidget(self.btn_tooltip_edit, 2, 1, 1, 3)

        right_layout.addWidget(self.btn_prop_box)

        # Macro steps box
        self.steps_box = QtWidgets.QGroupBox(tr("action_steps_title"), right_widget)
        steps_layout = QtWidgets.QVBoxLayout(self.steps_box)
        steps_layout.setSpacing(6)

        self.steps_table = QtWidgets.QTableWidget(self.steps_box)
        self.steps_table.setMinimumHeight(190)
        self.steps_table.setColumnCount(3)
        self.steps_table.setHorizontalHeaderLabels([tr("step_col_type"), tr("step_col_param"), tr("step_col_desc")])
        self.steps_table.horizontalHeader().setSectionResizeMode(0, QtWidgets.QHeaderView.ResizeToContents)
        self.steps_table.horizontalHeader().setSectionResizeMode(1, QtWidgets.QHeaderView.Stretch)
        self.steps_table.horizontalHeader().setSectionResizeMode(2, QtWidgets.QHeaderView.ResizeToContents)
        self.steps_table.setSelectionBehavior(QtWidgets.QAbstractItemView.SelectRows)
        self.steps_table.doubleClicked.connect(self._edit_step)
        steps_layout.addWidget(self.steps_table, 2)

        # Step toolbars - clean 2x4 grid
        step_grid = QtWidgets.QGridLayout()
        step_grid.setSpacing(5)

        self.record_macro_btn = QtWidgets.QPushButton(tr("btn_record_macro"), self.steps_box)
        self.record_macro_btn.setStyleSheet(
            "QPushButton { background: qlineargradient(x1:0, y1:0, x2:0, y2:1, stop:0 #FF453A, stop:1 #D70015); color: #FFFFFF; font-weight: 600; border-radius: 5px; border: 1px solid #B00010; padding: 5px 10px; } QPushButton:hover { background: #FF5B52; }"
        )
        self.record_macro_btn.setToolTip(tr("btn_record_macro_tip"))
        self.record_macro_btn.clicked.connect(self._record_macro)
        step_grid.addWidget(self.record_macro_btn, 0, 0)

        self.add_text_btn = QtWidgets.QPushButton(tr("btn_add_text"), self.steps_box)
        self.add_text_btn.setToolTip(tr("btn_add_text_tip"))
        self.add_text_btn.clicked.connect(lambda: self._add_step("paste"))
        step_grid.addWidget(self.add_text_btn, 0, 1)

        self.add_key_btn = QtWidgets.QPushButton(tr("btn_add_key"), self.steps_box)
        self.add_key_btn.setToolTip(tr("btn_add_key_tip"))
        self.add_key_btn.clicked.connect(lambda: self._add_step("key_capture"))
        step_grid.addWidget(self.add_key_btn, 0, 2)

        self.add_delay_btn = QtWidgets.QPushButton(tr("btn_add_delay"), self.steps_box)
        self.add_delay_btn.setToolTip(tr("btn_add_delay_tip"))
        self.add_delay_btn.clicked.connect(lambda: self._add_step("delay"))
        step_grid.addWidget(self.add_delay_btn, 0, 3)

        self.edit_step_btn = QtWidgets.QPushButton(tr("btn_edit_step"), self.steps_box)
        self.edit_step_btn.clicked.connect(self._edit_step)
        step_grid.addWidget(self.edit_step_btn, 1, 0)

        self.del_step_btn = QtWidgets.QPushButton(tr("btn_del_step"), self.steps_box)
        self.del_step_btn.clicked.connect(self._delete_step)
        step_grid.addWidget(self.del_step_btn, 1, 1)

        self.move_up_btn = QtWidgets.QPushButton(tr("btn_move_up"), self.steps_box)
        self.move_up_btn.setToolTip(tr("btn_move_up_tip"))
        self.move_up_btn.clicked.connect(lambda: self._move_step(-1))
        step_grid.addWidget(self.move_up_btn, 1, 2)

        self.move_down_btn = QtWidgets.QPushButton(tr("btn_move_down"), self.steps_box)
        self.move_down_btn.setToolTip(tr("btn_move_down_tip"))
        self.move_down_btn.clicked.connect(lambda: self._move_step(1))
        step_grid.addWidget(self.move_down_btn, 1, 3)

        steps_layout.addLayout(step_grid)
        right_layout.addWidget(self.steps_box, 2)

        # App binding box for current layout
        self.binding_box = QtWidgets.QGroupBox(tr("app_binding_title"), right_widget)
        b_layout = QtWidgets.QVBoxLayout(self.binding_box)
        b_layout.setSpacing(6)

        self.profile_table = QtWidgets.QTableWidget(self.binding_box)
        self.profile_table.setMinimumHeight(90)
        self.profile_table.setColumnCount(2)
        self.profile_table.setHorizontalHeaderLabels([tr("bind_col_process"), tr("bind_col_title")])
        self.profile_table.horizontalHeader().setSectionResizeMode(QtWidgets.QHeaderView.Stretch)
        self.profile_table.setSelectionBehavior(QtWidgets.QAbstractItemView.SelectRows)
        b_layout.addWidget(self.profile_table)

        b_btns1 = QtWidgets.QHBoxLayout()
        self.bind_curr_btn = QtWidgets.QPushButton(tr("btn_bind_current"), self.binding_box)
        self.bind_curr_btn.setToolTip(tr("btn_bind_current_tip"))
        self.bind_curr_btn.clicked.connect(self._add_current_target_profile)
        b_btns1.addWidget(self.bind_curr_btn)

        self.bind_pick_btn = QtWidgets.QPushButton(tr("btn_bind_pick"), self.binding_box)
        self.bind_pick_btn.setToolTip(tr("btn_bind_pick_tip"))
        self.bind_pick_btn.clicked.connect(self._add_from_running_windows)
        b_btns1.addWidget(self.bind_pick_btn)

        self.bind_custom_btn = QtWidgets.QPushButton(tr("btn_bind_custom"), self.binding_box)
        self.bind_custom_btn.clicked.connect(self._add_custom_profile)
        b_btns1.addWidget(self.bind_custom_btn)
        b_layout.addLayout(b_btns1)

        b_btns2 = QtWidgets.QHBoxLayout()
        self.bind_del_btn = QtWidgets.QPushButton(tr("btn_bind_delete"), self.binding_box)
        self.bind_del_btn.clicked.connect(self._delete_profile)
        b_btns2.addWidget(self.bind_del_btn)
        b_btns2.addStretch()
        b_layout.addLayout(b_btns2)

        right_layout.addWidget(self.binding_box)

        right_scroll.setWidget(right_widget)
        splitter.addWidget(right_scroll)
        splitter.setStretchFactor(0, 1)
        splitter.setStretchFactor(1, 1)
        splitter.setSizes([450, 540])
        tab_layout.addWidget(splitter, 1)
        tab_scroll = QtWidgets.QScrollArea(self.tabs)
        tab_scroll.setWidgetResizable(True)
        tab_scroll.setFrameShape(QtWidgets.QFrame.NoFrame)
        tab_scroll.setStyleSheet("QScrollArea { border: none; background-color: #1E1E20; }")
        tab_scroll.viewport().setStyleSheet("background-color: #1E1E20;")
        tab.setStyleSheet("background-color: #1E1E20;")
        tab_scroll.setWidget(tab)
        self.tabs.addTab(tab_scroll, tr("tab_layouts"))

    def _build_general_and_diag_tab(self):
        tab_scroll = QtWidgets.QScrollArea(self.tabs)
        tab_scroll.setWidgetResizable(True)
        tab_scroll.setFrameShape(QtWidgets.QFrame.NoFrame)
        tab_scroll.setStyleSheet("QScrollArea { border: none; background-color: #1E1E20; }")
        tab_scroll.viewport().setStyleSheet("background-color: #1E1E20;")

        tab = QtWidgets.QWidget()
        tab.setStyleSheet("background-color: #1E1E20;")
        layout = QtWidgets.QVBoxLayout(tab)
        layout.setContentsMargins(14, 14, 14, 14)
        layout.setSpacing(12)

        # 1. Interface Language
        self.lang_box = QtWidgets.QGroupBox(tr("language_group_title"), tab)
        lang_form = QtWidgets.QFormLayout(self.lang_box)
        lang_form.setSpacing(10)

        self.language_combo = QtWidgets.QComboBox(self.lang_box)
        self.language_combo.addItem(tr("lang_zh"), "zh")
        self.language_combo.addItem(tr("lang_en"), "en")
        curr_lang = get_current_language()
        idx = self.language_combo.findData(curr_lang)
        if idx >= 0:
            self.language_combo.setCurrentIndex(idx)
        self.language_combo.currentIndexChanged.connect(self._on_language_changed)
        self.lbl_language = QtWidgets.QLabel(tr("language_label"))
        lang_form.addRow(self.lbl_language, self.language_combo)
        layout.addWidget(self.lang_box)

        # 2. Hotkeys & Global Options
        self.hotkey_box = QtWidgets.QGroupBox(tr("hotkey_group_title"), tab)
        hk_form = QtWidgets.QFormLayout(self.hotkey_box)
        hk_form.setSpacing(10)

        self.auto_profile_switch_chk = QtWidgets.QCheckBox(tr("auto_profile_switch_chk"), self.hotkey_box)
        self.lbl_auto_profile = QtWidgets.QLabel(tr("auto_profile_switch_label"))
        hk_form.addRow(self.lbl_auto_profile, self.auto_profile_switch_chk)

        self.toggle_hotkey_edit = QtWidgets.QLineEdit(self.hotkey_box)
        self.toggle_hotkey_edit.setPlaceholderText(tr("toggle_hotkey_placeholder"))
        self.lbl_toggle_hotkey = QtWidgets.QLabel(tr("toggle_hotkey_label"))
        hk_form.addRow(self.lbl_toggle_hotkey, self.toggle_hotkey_edit)

        self.stop_hotkey_edit = QtWidgets.QLineEdit(self.hotkey_box)
        self.stop_hotkey_edit.setPlaceholderText(tr("stop_hotkey_placeholder"))
        self.lbl_stop_hotkey = QtWidgets.QLabel(tr("stop_hotkey_label"))
        hk_form.addRow(self.lbl_stop_hotkey, self.stop_hotkey_edit)
        layout.addWidget(self.hotkey_box)

        # 3. Backup & Restore
        self.data_box = QtWidgets.QGroupBox(tr("backup_group_title"), tab)
        d_layout = QtWidgets.QHBoxLayout(self.data_box)
        self.backup_btn = QtWidgets.QPushButton(tr("btn_backup"), self.data_box)
        self.backup_btn.clicked.connect(self._backup_config)
        d_layout.addWidget(self.backup_btn)
        d_layout.addStretch()
        layout.addWidget(self.data_box)

        # 4. Diagnostics
        self.diag_box = QtWidgets.QGroupBox(tr("diag_group_title"), tab)
        diag_layout = QtWidgets.QVBoxLayout(self.diag_box)

        self.target_info_label = QtWidgets.QLabel(tr("target_info_prefix", info=tr("target_undetected")), self.diag_box)
        diag_layout.addWidget(self.target_info_label)

        self.log_table = QtWidgets.QTableWidget(self.diag_box)
        self.log_table.setMinimumHeight(100)
        self.log_table.setColumnCount(4)
        self.log_table.setHorizontalHeaderLabels([tr("log_col_time"), tr("log_col_action"), tr("log_col_status"), tr("log_col_desc")])
        self.log_table.horizontalHeader().setSectionResizeMode(0, QtWidgets.QHeaderView.ResizeToContents)
        self.log_table.horizontalHeader().setSectionResizeMode(1, QtWidgets.QHeaderView.ResizeToContents)
        self.log_table.horizontalHeader().setSectionResizeMode(2, QtWidgets.QHeaderView.ResizeToContents)
        self.log_table.horizontalHeader().setSectionResizeMode(3, QtWidgets.QHeaderView.Stretch)
        diag_layout.addWidget(self.log_table, 1)

        self.refresh_diag_btn = QtWidgets.QPushButton(tr("btn_refresh_diag"), self.diag_box)
        self.refresh_diag_btn.clicked.connect(self._refresh_diag)
        diag_layout.addWidget(self.refresh_diag_btn)

        layout.addWidget(self.diag_box, 1)
        tab_scroll.setWidget(tab)
        self.tabs.addTab(tab_scroll, tr("tab_general"))

        # Load global settings
        cfg = self.config_store.load_config()
        self.auto_profile_switch_chk.setChecked(
            cfg.get("settings", {}).get("auto_profile_switch", True)
        )
        self.toggle_hotkey_edit.setText(
            cfg.get("hotkeys", {}).get("toggle_visible", "ALT+Q")
        )
        self.stop_hotkey_edit.setText(
            cfg.get("hotkeys", {}).get("emergency_stop", "ESC")
        )
        self._refresh_diag()

    def _refresh_diag(self):
        info = self.target_mgr.get_target_info()
        is_en = get_current_language() == "en"
        target_str = "Target" if is_en else "目标窗口"
        proc_str = "Process" if is_en else "进程"
        handle_str = "Handle" if is_en else "句柄"
        locked_str = "Locked" if is_en else "锁定"
        self.target_info_label.setText(
            f"{target_str}: {info.get('title', '')} | {proc_str}: {info.get('process_name', '')} | PID: {info.get('process_id', '')} | {handle_str}: {info.get('handle', '')} | {locked_str}: {info.get('is_locked', False)}"
        )
        logs = getattr(self.executor, "execution_logs", [])
        self.log_table.setRowCount(len(logs))
        for row, entry in enumerate(reversed(logs)):
            self.log_table.setItem(row, 0, QtWidgets.QTableWidgetItem(entry.get("timestamp", "")))
            self.log_table.setItem(row, 1, QtWidgets.QTableWidgetItem(entry.get("action_id", "")))
            status_text = ("Success" if is_en else "成功") if entry.get("success") else ("Failed" if is_en else "失败")
            ok_item = QtWidgets.QTableWidgetItem(status_text)
            ok_item.setForeground(QtGui.QColor("#10B981" if entry.get("success") else "#EF4444"))
            self.log_table.setItem(row, 2, ok_item)
            self.log_table.setItem(row, 3, QtWidgets.QTableWidgetItem(entry.get("message", "")))

    def _current_layout(self) -> Optional[Layout]:
        lid = self.layout_selector.currentData()
        return self.layout_mgr.layouts.get(lid) if lid else None

    def _refresh_layout_selector(self):
        self.layout_selector.blockSignals(True)
        self.layout_selector.clear()
        for lid, layout in self.layout_mgr.layouts.items():
            self.layout_selector.addItem(layout.name, lid)
        index = self.layout_selector.findData(self.layout_mgr.active_layout_id)
        if index >= 0:
            self.layout_selector.setCurrentIndex(index)
        self.layout_selector.blockSignals(False)

    def _on_layout_selected(self, index):
        lid = self.layout_selector.itemData(index)
        if lid:
            self.layout_mgr.set_active_layout(lid)
        self._load_active_layout()

    def _load_active_layout(self):
        layout = self._current_layout()
        if not layout:
            return
        self._loading = True

        self.rows_spin.setValue(layout.rows)
        self.cols_spin.setValue(layout.columns)
        self.size_combo.setCurrentIndex(
            {"compact": 0, "standard": 1, "touch": 2}.get(layout.settings.button_size, 0)
        )
        self.opacity_slider.setValue(int(layout.settings.opacity * 100))
        self.always_on_top_chk.setChecked(layout.settings.always_on_top)
        self.confirm_action_chk.setChecked(layout.settings.confirm_before_action)
        self.auto_enter_chk.setChecked(layout.settings.auto_enter_default)

        self._loading = False

        target_slot = None
        if layout.buttons:
            if self.selected_button_id:
                target_slot = next((s for s in layout.buttons if s.button_id == self.selected_button_id), None)
            if not target_slot:
                target_slot = layout.buttons[0]
            self.selected_row = target_slot.row
            self.selected_col = target_slot.column
            self.selected_button_id = target_slot.button_id
        else:
            self.selected_row = None
            self.selected_col = None
            self.selected_button_id = None

        self._render_preview_grid()
        self._refresh_profiles_for_current_layout()

        if target_slot:
            self._select_slot(target_slot.row, target_slot.column, target_slot.button_id, update_grid_borders=True)
        else:
            self._clear_selection()

    def _transpose_layout(self):
        """Transpose the current layout's rows and columns, update spinboxes and preview."""
        layout = self._current_layout()
        if not layout:
            return
        layout.transpose()
        self._loading = True
        self.rows_spin.setValue(layout.rows)
        self.cols_spin.setValue(layout.columns)
        if self.selected_row is not None and self.selected_col is not None:
            self.selected_row, self.selected_col = self.selected_col, self.selected_row
        elif self.selected_button_id:
            slot = next((s for s in layout.buttons if s.button_id == self.selected_button_id), None)
            if slot:
                self.selected_row, self.selected_col = slot.row, slot.column
        self._loading = False
        self._render_preview_grid()
        if self.selected_button_id:
            self._select_slot(self.selected_row, self.selected_col, self.selected_button_id)

    def _layout_property_changed(self):
        if self._loading:
            return
        layout = self._current_layout()
        if not layout:
            return

        old_rows = layout.rows
        old_cols = layout.columns
        new_rows = self.rows_spin.value()
        new_cols = self.cols_spin.value()
        grid_changed = (new_rows != old_rows or new_cols != old_cols)

        layout.rows = new_rows
        layout.columns = new_cols
        layout.settings.button_size = ["compact", "standard", "touch"][self.size_combo.currentIndex()]
        layout.settings.opacity = self.opacity_slider.value() / 100.0
        layout.settings.always_on_top = self.always_on_top_chk.isChecked()
        layout.settings.confirm_before_action = self.confirm_action_chk.isChecked()
        layout.settings.auto_enter_default = self.auto_enter_chk.isChecked()

        if grid_changed:
            layout.sanitize_slots()
            layout.settings.window_width = None
            layout.settings.window_height = None
            layout.settings.saved_rows = new_rows
            layout.settings.saved_columns = new_cols
            if self.selected_row is not None and self.selected_row >= new_rows:
                self.selected_row = None
            if self.selected_col is not None and self.selected_col >= new_cols:
                self.selected_col = None
            if self.selected_button_id and not any(s.button_id == self.selected_button_id for s in layout.buttons):
                self.selected_button_id = None
                self._clear_selection()

        # Re-render preview grid
        self._render_preview_grid()

    def _render_preview_grid(self):
        """Render layout preview reusing ActionButtonWidget-like styling with slot management."""
        layout = self._current_layout()
        if not layout:
            return

        self._preview_widgets.clear()

        # Clear existing preview grid items
        while self.preview_grid.count():
            item = self.preview_grid.takeAt(0)
            widget = item.widget()
            if widget:
                widget.hide()
                widget.setParent(None)
                widget.deleteLater()

        rows = layout.rows
        cols = layout.columns
        slot_map = {}
        for slot in layout.buttons:
            slot_map[(slot.row, slot.column)] = slot.button_id

        # Determine scale factor from button_size
        scale = {"compact": 1.0, "standard": 1.25, "touch": 1.6}.get(
            layout.settings.button_size, 1.0
        )
        width = int(64 * scale)
        height = int(36 * scale)
        font_size = int(10 * scale)
        self._preview_font_size = font_size

        found_selected = False

        for r in range(rows):
            for c in range(cols):
                btn_id = slot_map.get((r, c))
                btn_model = self.layout_mgr.get_button(btn_id) if btn_id else None

                if btn_model:
                    display_text = btn_model.display_text
                    btn = PreviewSlotButton(
                        r, c, btn_model, self._select_slot, self._on_slot_drag_swap, self.preview_container
                    )
                    btn.setText(display_text)
                    btn.setFixedSize(width, height)
                    btn.setToolTip(btn_model.tooltip or btn_model.label)
                    color = btn_model.color or "#0A84FF"
                    is_sel = (self.selected_button_id == btn_model.id)
                    border = "3px solid #00E676" if is_sel else "1px solid rgba(255,255,255,0.18)"
                    btn.setStyleSheet(f"""
                        QPushButton {{
                            background-color: {color};
                            color: #FFFFFF;
                            font-weight: 600;
                            font-family: "Segoe UI Variable Text", "Segoe UI", "PingFang SC", "Microsoft YaHei UI", sans-serif;
                            font-size: {font_size}px;
                            border: {border};
                            border-radius: 6px;
                            padding: 2px;
                        }}
                        QPushButton:hover {{
                            border: 2px solid rgba(255, 255, 255, 0.85);
                        }}
                    """)
                    self.preview_grid.addWidget(btn, r, c)
                    self._preview_widgets[(r, c)] = btn
                    if is_sel:
                        found_selected = True
                else:
                    # Empty slot button
                    empty_btn = PreviewSlotButton(
                        r, c, None,
                        lambda row, col, _: self._create_slot_button(row, col),
                        self._on_slot_drag_swap,
                        self.preview_container,
                    )
                    empty_btn.setText("＋")
                    empty_btn.setFixedSize(width, height)
                    empty_btn.setToolTip("点击创建此槽位按钮，或将其他按钮拖放到此处" if get_current_language() == "zh" else "Click to create button here, or drag another button here")
                    empty_btn.setStyleSheet("""
                        QPushButton {
                            background-color: rgba(255, 255, 255, 0.02);
                            color: #6E6E73;
                            border: 1.5px dashed rgba(255, 255, 255, 0.18);
                            border-radius: 6px;
                            font-size: 14px;
                            font-weight: 400;
                        }
                        QPushButton:hover {
                            border-color: #0A84FF;
                            color: #0A84FF;
                            background-color: rgba(10, 132, 255, 0.08);
                        }
                    """)
                    self.preview_grid.addWidget(empty_btn, r, c)
                    self._preview_widgets[(r, c)] = empty_btn

        # If a button was previously selected but no longer exists, select first available button
        if self.selected_button_id is not None and not found_selected and layout.buttons:
            first_slot = layout.buttons[0]
            self._select_slot(first_slot.row, first_slot.column, first_slot.button_id, update_grid_borders=True)
        elif not layout.buttons or self.selected_button_id is None:
            self._clear_selection()

    def _select_slot(self, row: Optional[int], col: Optional[int], button_id: Optional[str], update_grid_borders: bool = True):
        self.selected_row = row
        self.selected_col = col
        self.selected_button_id = button_id
        button = self.layout_mgr.get_button(button_id) if button_id else None
        action = self.layout_mgr.get_action_for_button(button_id) if button_id else None

        self._loading = True
        if button:
            clean_lbl = button.label.replace("\n", " ")
            if row is not None and col is not None:
                self.selected_info_label.setText(
                    tr("slot_info_occupied", row=row + 1, col=col + 1, id=clean_lbl)
                )
            else:
                self.selected_info_label.setText(f"ID: {clean_lbl}")
            self.btn_label_edit.setEnabled(True)
            self.btn_label_edit.setText(button.label.replace("\n", "\\n"))
            self.btn_tooltip_edit.setEnabled(True)
            self.btn_tooltip_edit.setText(button.tooltip)
            self.btn_color_combo.setEnabled(True)
            idx = self.btn_color_combo.findData(button.color)
            if idx >= 0:
                self.btn_color_combo.setCurrentIndex(idx)
            else:
                self.btn_color_combo.setCurrentIndex(0)
            self._refresh_steps(action)
        else:
            self._clear_selection()

        self._loading = False

        if update_grid_borders:
            self._update_preview_borders()

    def _update_preview_borders(self):
        """Update selected border styling on preview widgets without destroying them."""
        for (r, c), widget in self._preview_widgets.items():
            slot_button = getattr(widget, "button_model", None)
            if slot_button:
                is_sel = (self.selected_row == r and self.selected_col == c)
                border = "3px solid #00E676" if is_sel else "1px solid rgba(255,255,255,0.18)"
                color = slot_button.color or "#0A84FF"
                widget.setStyleSheet(f"""
                    QPushButton {{
                        background-color: {color};
                        color: #FFFFFF;
                        font-weight: 600;
                        font-family: "Segoe UI Variable Text", "Segoe UI", "PingFang SC", "Microsoft YaHei UI", sans-serif;
                        font-size: {self._preview_font_size}px;
                        border: {border};
                        border-radius: 6px;
                        padding: 2px;
                    }}
                    QPushButton:hover {{
                        border: 2px solid rgba(255, 255, 255, 0.85);
                    }}
                """)

    def _clear_selection(self):
        self.selected_row = None
        self.selected_col = None
        self.selected_button_id = None
        self.selected_info_label.setText(tr("no_btn_selected"))
        self.btn_label_edit.setEnabled(False)
        self.btn_label_edit.clear()
        self.btn_tooltip_edit.setEnabled(False)
        self.btn_tooltip_edit.clear()
        self.btn_color_combo.setEnabled(False)
        self.steps_table.setRowCount(0)
        self._update_preview_borders()

    def _create_slot_button(self, row: int, col: int):
        layout = self._current_layout()
        if not layout:
            return
        lbl_prefix = "Btn" if get_current_language() == "en" else "按钮"
        btn = self.layout_mgr.create_button_for_slot(
            layout.id, row, col, label=f"{lbl_prefix} {len(layout.buttons) + 1}"
        )
        if btn:
            self.selected_row = row
            self.selected_col = col
            self.selected_button_id = btn.id
            self._render_preview_grid()
            self._select_slot(row, col, btn.id)

    def _clear_selected_slot(self):
        layout = self._current_layout()
        if not layout or self.selected_row is None or self.selected_col is None:
            return
        self.layout_mgr.remove_button_from_slot(layout.id, self.selected_row, self.selected_col)
        self.selected_button_id = None
        self._clear_selection()
        self._render_preview_grid()

    def _move_slot(self, dr: int, dc: int):
        """Move the selected slot by swapping it in the layout grid."""
        layout = self._current_layout()
        if not layout or self.selected_row is None or self.selected_col is None:
            return
        r, c = self.selected_row, self.selected_col
        nr, nc = r + dr, c + dc
        if 0 <= nr < layout.rows and 0 <= nc < layout.columns:
            layout.swap_slots(r, c, nr, nc)
            slot = layout.get_slot_at(nr, nc)
            btn_id = slot.button_id if slot else None
            self._render_preview_grid()
            self._select_slot(nr, nc, btn_id)

    def _on_slot_drag_swap(self, src_r: int, src_c: int, dst_r: int, dst_c: int):
        """Callback when user drags and drops a button onto another slot."""
        layout = self._current_layout()
        if not layout:
            return
        layout.swap_slots(src_r, src_c, dst_r, dst_c)
        slot = layout.get_slot_at(dst_r, dst_c)
        btn_id = slot.button_id if slot else None
        self._render_preview_grid()
        self._select_slot(dst_r, dst_c, btn_id)

    def _button_property_changed(self):
        if self._loading or not self.selected_button_id:
            return
        button = self.layout_mgr.get_button(self.selected_button_id)
        action = self.layout_mgr.get_action_for_button(self.selected_button_id)
        if not button:
            return
        button.label = self.btn_label_edit.text().replace("\\n", "\n")
        button.tooltip = self.btn_tooltip_edit.text()
        button.color = self.btn_color_combo.currentData() or "#0A84FF"
        if action:
            action.label = button.label

        if self.selected_row is not None and self.selected_col is not None:
            clean_lbl = button.label.replace("\n", " ")
            self.selected_info_label.setText(
                tr("slot_info_occupied", row=self.selected_row + 1, col=self.selected_col + 1, id=clean_lbl)
            )

        # Update preview button widget directly in place without grid rebuild
        coord = (self.selected_row, self.selected_col)
        widget = self._preview_widgets.get(coord)
        if widget and hasattr(widget, "setText"):
            display_text = button.display_text
            widget.setText(display_text)
            widget.setToolTip(button.tooltip or button.label)
            border = "3px solid #00E676"
            widget.setStyleSheet(f"""
                QPushButton {{
                    background-color: {button.color};
                    color: #FFFFFF;
                    font-weight: 600;
                    font-family: "Segoe UI Variable Text", "Segoe UI", "PingFang SC", "Microsoft YaHei UI", sans-serif;
                    font-size: {self._preview_font_size}px;
                    border: {border};
                    border-radius: 6px;
                    padding: 2px;
                }}
                QPushButton:hover {{
                    border: 2px solid rgba(255, 255, 255, 0.85);
                }}
            """)
        else:
            self._render_preview_grid()

    def _refresh_steps(self, action: Optional[Action]):
        self.steps_table.setRowCount(0)
        if not action:
            return
        self.steps_table.setRowCount(len(action.steps))
        for row, step in enumerate(action.steps):
            value = (
                step.value
                if step.type in ("text", "paste")
                else step.key
                if step.type == "key"
                else (step.hotkey or "+".join(step.keys))
                if step.type == "hotkey"
                else f"{step.ms} ms"
                if step.type == "delay"
                else step.name
            )
            type_display = {
                "paste": tr("step_type_paste"),
                "text": tr("step_type_paste"),
                "key": tr("step_type_key"),
                "hotkey": tr("step_type_hotkey"),
                "delay": tr("step_type_delay"),
            }.get(step.type, step.type)
            type_item = QtWidgets.QTableWidgetItem(type_display)
            val_item = QtWidgets.QTableWidgetItem(str(value))
            desc_text = {
                "paste": tr("step_desc_paste"),
                "text": tr("step_desc_paste"),
                "key": tr("step_desc_key"),
                "hotkey": tr("step_desc_hotkey"),
                "delay": tr("step_desc_delay"),
            }.get(step.type, tr("action_steps_title"))
            desc_item = QtWidgets.QTableWidgetItem(desc_text)
            self.steps_table.setItem(row, 0, type_item)
            self.steps_table.setItem(row, 1, val_item)
            self.steps_table.setItem(row, 2, desc_item)

    def _current_action(self) -> Optional[Action]:
        if not self.selected_button_id:
            return None
        return self.layout_mgr.get_action_for_button(self.selected_button_id)

    def _add_step(self, kind: str):
        action = self._current_action()
        if not action:
            QtWidgets.QMessageBox.information(self, tr("prompt_notice"), tr("no_btn_selected"))
            return
        step = None
        if kind == "paste":
            val, ok = QtWidgets.QInputDialog.getMultiLineText(
                self, tr("btn_add_text"), "输入文本内容 (剪贴板无损粘贴):" if get_current_language() == "zh" else "Enter text content (Lossless clipboard paste):"
            )
            if ok and val:
                step = ActionStep(type="paste", value=val)
        elif kind == "key_capture":
            dlg = KeyCaptureDialog(parent=self)
            if dlg.exec_() == QtWidgets.QDialog.Accepted:
                val = dlg.get_captured_key()
                if val:
                    if "+" in val:
                        step = ActionStep(
                            type="hotkey",
                            hotkey=val,
                            keys=[k.strip() for k in val.split("+") if k.strip()],
                        )
                    else:
                        step = ActionStep(type="key", key=val)
        elif kind == "delay":
            ms, ok = QtWidgets.QInputDialog.getInt(
                self, tr("btn_add_delay"), "输入等待毫秒数 (ms):" if get_current_language() == "zh" else "Enter delay in milliseconds (ms):", 200, 10, 30000
            )
            if ok:
                step = ActionStep(type="delay", ms=ms)

        if step:
            action.steps.append(step)
            self._refresh_steps(action)

    def _edit_step(self):
        action = self._current_action()
        row = self.steps_table.currentRow()
        if not action or not (0 <= row < len(action.steps)):
            return
        step = action.steps[row]
        if step.type in ("key", "hotkey"):
            curr_str = step.hotkey or (step.key if step.type == "key" else "+".join(step.keys))
            dlg = KeyCaptureDialog(initial_key=curr_str, parent=self)
            if dlg.exec_() == QtWidgets.QDialog.Accepted:
                val = dlg.get_captured_key()
                if val:
                    if "+" in val:
                        step.type = "hotkey"
                        step.hotkey = val
                        step.keys = [k.strip() for k in val.split("+") if k.strip()]
                    else:
                        step.type = "key"
                        step.key = val
                        step.hotkey = ""
                        step.keys = []
        elif step.type in ("paste", "text"):
            val, ok = QtWidgets.QInputDialog.getMultiLineText(
                self, tr("btn_edit_step"), "文本内容:" if get_current_language() == "zh" else "Text content:", text=step.value
            )
            if ok:
                step.value = val
                step.type = "paste"
        elif step.type == "delay":
            ms, ok = QtWidgets.QInputDialog.getInt(
                self, tr("btn_edit_step"), "毫秒数:" if get_current_language() == "zh" else "Milliseconds:", value=step.ms, min=10, max=30000
            )
            if ok:
                step.ms = ms
        self._refresh_steps(action)

    def _delete_step(self):
        action = self._current_action()
        row = self.steps_table.currentRow()
        if action and 0 <= row < len(action.steps):
            del action.steps[row]
            self._refresh_steps(action)

    def _move_step(self, delta: int):
        action = self._current_action()
        row = self.steps_table.currentRow()
        new_row = row + delta
        if action and (0 <= new_row < len(action.steps)):
            action.steps[row], action.steps[new_row] = action.steps[new_row], action.steps[row]
            self._refresh_steps(action)
            self.steps_table.selectRow(new_row)

    def _record_macro(self):
        action = self._current_action()
        if not action:
            QtWidgets.QMessageBox.information(self, tr("prompt_notice"), tr("no_btn_selected"))
            return
        dialog = MacroRecorderDialog(
            MacroRecorder(), executor=self.executor, target_mgr=self.target_mgr, parent=self
        )
        if dialog.exec_() == QtWidgets.QDialog.Accepted and dialog.recorded_steps:
            action.steps = list(dialog.recorded_steps)
            self._refresh_steps(action)

    def _refresh_profiles_for_current_layout(self):
        layout = self._current_layout()
        if not layout:
            self.profile_table.setRowCount(0)
            return
        matched = [p for p in self.layout_mgr.profiles if p.layout_id == layout.id]
        self.profile_table.setRowCount(len(matched))
        for row, prof in enumerate(matched):
            self.profile_table.setItem(row, 0, QtWidgets.QTableWidgetItem(prof.process))
            self.profile_table.setItem(row, 1, QtWidgets.QTableWidgetItem(prof.window_title_contains))

    def _add_current_target_profile(self):
        layout = self._current_layout()
        if not layout:
            return
        info = self.target_mgr.get_target_info()
        proc = info.get("process_name", "")
        if not proc:
            QtWidgets.QMessageBox.warning(
                self,
                tr("prompt_warning"),
                "当前未捕获到外部目标应用！\n\n请在外部软件窗口中点击一次，或从运行中的窗口列表中直接选择。"
                if get_current_language() == "zh" else
                "No external target application detected!\n\nPlease focus an external window first or pick from running windows.",
            )
            return
        title = info.get("title", "")
        res = QtWidgets.QMessageBox.question(
            self,
            tr("prompt_confirm"),
            f"检测到最近使用的外部应用：\n\n• 进程名：{proc}\n• 窗口标题：{title or '(无标题)'}\n\n是否将该应用绑定到当前布局【{layout.name}】？"
            if get_current_language() == "zh" else
            f"Detected recent external application:\n\n• Process: {proc}\n• Title: {title or '(No title)'}\n\nBind this app to layout [{layout.name}]?",
            QtWidgets.QMessageBox.Yes | QtWidgets.QMessageBox.No,
            QtWidgets.QMessageBox.Yes,
        )
        if res != QtWidgets.QMessageBox.Yes:
            return
        p_id = f"profile_{len(self.layout_mgr.profiles) + 1}"
        profile = Profile(id=p_id, process=proc, layout_id=layout.id)
        self.layout_mgr.register_profile(profile)
        self._refresh_profiles_for_current_layout()
        QtWidgets.QMessageBox.information(
            self, tr("prompt_notice"), f"已成功将应用 {proc} 绑定到当前布局【{layout.name}】！" if get_current_language() == "zh" else f"Successfully bound {proc} to layout [{layout.name}]!"
        )

    def _add_from_running_windows(self):
        layout = self._current_layout()
        if not layout:
            return
        windows_list = []
        my_pid = os.getpid()

        try:
            import win32gui
            def enum_win(hwnd, extra):
                if win32gui.IsWindowVisible(hwnd):
                    title = win32gui.GetWindowText(hwnd).strip()
                    if title:
                        info = self.target_mgr.window_manager.get_window_info(hwnd)
                        pid = info.get("process_id", 0)
                        proc = info.get("process_name", "")
                        if pid != my_pid and proc and proc.lower() not in (
                            "shellexperiencehost.exe",
                            "searchhost.exe",
                            "startmenuexperiencehost.exe",
                            "textinputhost.exe",
                        ) and not (proc.lower() == "explorer.exe" and title.lower() in ("program manager", "")):
                            windows_list.append((proc, title))
                return True

            win32gui.EnumWindows(enum_win, None)
        except Exception:
            pass

        if not windows_list:
            QtWidgets.QMessageBox.information(self, tr("prompt_notice"), "未找到可绑定的运行中外部窗口。" if get_current_language() == "zh" else "No running external windows found to bind.")
            return

        seen = set()
        unique_windows = []
        for proc, title in windows_list:
            display_str = f"{proc} — {title[:50]}"
            if display_str not in seen:
                seen.add(display_str)
                unique_windows.append((proc, title, display_str))

        items = [disp for _, _, disp in unique_windows]
        chosen, ok = QtWidgets.QInputDialog.getItem(
            self, tr("btn_bind_pick"), "请从当前打开的应用列表中选择：" if get_current_language() == "zh" else "Select from open applications:", items, 0, False
        )
        if not ok or not chosen:
            return

        idx = items.index(chosen)
        proc, title, _ = unique_windows[idx]
        p_id = f"profile_{len(self.layout_mgr.profiles) + 1}"
        profile = Profile(id=p_id, process=proc, layout_id=layout.id)
        self.layout_mgr.register_profile(profile)
        self._refresh_profiles_for_current_layout()
        QtWidgets.QMessageBox.information(
            self, tr("prompt_notice"), f"已成功将应用 {proc} 绑定到当前布局【{layout.name}】！" if get_current_language() == "zh" else f"Successfully bound {proc} to layout [{layout.name}]!"
        )

    def _add_custom_profile(self):
        layout = self._current_layout()
        if not layout:
            return
        proc, ok1 = QtWidgets.QInputDialog.getText(
            self, tr("btn_bind_custom"), "目标进程名 (例如 notepad.exe):" if get_current_language() == "zh" else "Process name (e.g. notepad.exe):"
        )
        if not ok1 or not proc.strip():
            return
        title, ok2 = QtWidgets.QInputDialog.getText(
            self, tr("btn_bind_custom"), "窗口标题包含字符 (可选，留空匹配所有):" if get_current_language() == "zh" else "Window title filter (Optional, leave blank to match all):"
        )
        p_id = f"profile_{len(self.layout_mgr.profiles) + 1}"
        profile = Profile(
            id=p_id,
            process=proc.strip(),
            window_title_contains=title.strip() if ok2 else "",
            layout_id=layout.id,
        )
        self.layout_mgr.register_profile(profile)
        self._refresh_profiles_for_current_layout()

    def _delete_profile(self):
        layout = self._current_layout()
        row = self.profile_table.currentRow()
        if not layout or row < 0:
            return
        matched = [p for p in self.layout_mgr.profiles if p.layout_id == layout.id]
        if 0 <= row < len(matched):
            prof_to_remove = matched[row]
            self.layout_mgr.profiles.remove(prof_to_remove)
            self._refresh_profiles_for_current_layout()

    def _new_layout(self):
        dlg = NewLayoutDialog(self)
        if dlg.exec_() == QtWidgets.QDialog.Accepted:
            name, orientation, rows, cols, size = dlg.get_values()
            idx = 1
            lid = f"layout_{idx}"
            while lid in self.layout_mgr.layouts:
                idx += 1
                lid = f"layout_{idx}"
            self.layout_mgr.create_layout_with_presets(
                layout_id=lid,
                name=name,
                orientation=orientation,
                rows=rows,
                columns=cols,
                button_size=size,
            )
            self._refresh_layout_selector()
            self.layout_selector.setCurrentIndex(self.layout_selector.findData(lid))
            self._load_active_layout()

    def _copy_layout(self):
        source = self._current_layout()
        if not source:
            return
        name, ok = QtWidgets.QInputDialog.getText(
            self, tr("prompt_copy_layout_title"), tr("prompt_new_layout_label"), text=source.name + tr("prompt_copy_layout_suffix")
        )
        if not ok or not name.strip():
            return
        lid = source.id + "_copy"
        idx = 2
        while lid in self.layout_mgr.layouts:
            idx += 1
            lid = f"{source.id}_copy{idx}"
        self.layout_mgr.duplicate_layout(source.id, lid, name.strip())
        self._refresh_layout_selector()
        self.layout_selector.setCurrentIndex(self.layout_selector.findData(lid))
        self._load_active_layout()

    def _rename_layout(self):
        layout = self._current_layout()
        if not layout:
            return
        name, ok = QtWidgets.QInputDialog.getText(
            self, tr("prompt_rename_layout_title"), tr("prompt_new_layout_label"), text=layout.name
        )
        if ok and name.strip():
            layout.name = name.strip()
            self._refresh_layout_selector()
            self._load_active_layout()

    def _delete_layout(self):
        layout = self._current_layout()
        if not layout or len(self.layout_mgr.layouts) <= 1:
            QtWidgets.QMessageBox.warning(self, tr("prompt_warning"), tr("prompt_del_layout_min"))
            return
        if QtWidgets.QMessageBox.question(
            self, tr("prompt_confirm"), tr("prompt_del_layout_confirm", name=layout.name),
            QtWidgets.QMessageBox.Yes | QtWidgets.QMessageBox.No,
        ) != QtWidgets.QMessageBox.Yes:
            return
        self.layout_mgr.delete_layout(layout.id)
        self._refresh_layout_selector()
        self._load_active_layout()

    def _reset_current_layout_to_preset(self):
        """Reset the current layout to its default preset pack state."""
        layout = self._current_layout()
        if not layout:
            return
        base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        packs_dir = os.path.join(base_dir, "packs")
        found_data = None
        found_layout = None
        for p_name in ["word", "annotation", "customer_service", "programmer"]:
            p_dir = os.path.join(packs_dir, p_name)
            if os.path.isdir(p_dir):
                ok, _, p_data = PackStore.import_pack(p_dir)
                if ok:
                    for l in p_data.get("layouts", []):
                        if l.id == layout.id:
                            found_data = p_data
                            found_layout = l
                            break
            if found_layout:
                break

        if not found_layout:
            QtWidgets.QMessageBox.information(
                self, tr("prompt_notice"), tr("prompt_reset_preset_nonpreset")
            )
            return

        res = QtWidgets.QMessageBox.question(
            self,
            tr("prompt_confirm"),
            tr("prompt_reset_preset_confirm", name=layout.name),
            QtWidgets.QMessageBox.Yes | QtWidgets.QMessageBox.No,
            QtWidgets.QMessageBox.No,
        )
        if res != QtWidgets.QMessageBox.Yes:
            return

        for a in found_data.get("actions", []):
            self.layout_mgr.register_action(a)
        for b in found_data.get("buttons", []):
            self.layout_mgr.register_button(b)
        self.layout_mgr.register_layout(found_layout)

        self._refresh_layout_selector()
        idx = self.layout_selector.findData(layout.id)
        if idx >= 0:
            self.layout_selector.setCurrentIndex(idx)
        self._load_active_layout()
        QtWidgets.QMessageBox.information(self, tr("prompt_notice"), f"已成功将“{layout.name}”恢复为官方预设！" if get_current_language() == "zh" else f"Layout [{layout.name}] successfully reset to presets!")

    def _backup_config(self):
        path = self.config_store.create_backup()
        if path:
            QtWidgets.QMessageBox.information(self, tr("prompt_notice"), tr("prompt_backup_success", path=path))
        else:
            QtWidgets.QMessageBox.warning(self, tr("prompt_warning"), "无法创建配置备份。" if get_current_language() == "zh" else "Failed to create configuration backup.")

    def _on_language_changed(self, index):
        new_lang = self.language_combo.itemData(index)
        if new_lang and new_lang != get_current_language():
            set_current_language(new_lang)
            cfg = self.config_store.load_config()
            cfg.setdefault("settings", {})["language"] = new_lang
            self.config_store.save_config(cfg)
            self.retranslate_ui()
            if self.parent() and hasattr(self.parent(), "retranslate_ui"):
                self.parent().retranslate_ui()

    def retranslate_ui(self):
        self.setWindowTitle(tr("settings_title"))
        self.tabs.setTabText(0, tr("tab_layouts"))
        self.tabs.setTabText(1, tr("tab_general"))

        # Top bar
        if hasattr(self, "lbl_curr_layout"):
            self.lbl_curr_layout.setText(tr("layout_select_label"))
        if hasattr(self, "new_layout_btn"):
            self.new_layout_btn.setText(tr("btn_new_layout"))
        if hasattr(self, "copy_layout_btn"):
            self.copy_layout_btn.setText(tr("btn_copy_layout"))
        if hasattr(self, "rename_layout_btn"):
            self.rename_layout_btn.setText(tr("btn_rename_layout"))
        if hasattr(self, "delete_layout_btn"):
            self.delete_layout_btn.setText(tr("btn_del_layout"))
        if hasattr(self, "reset_layout_btn"):
            self.reset_layout_btn.setText(tr("btn_reset_preset"))
            self.reset_layout_btn.setToolTip(tr("btn_reset_preset_tip"))

        # Layout Properties
        if hasattr(self, "layout_box"):
            self.layout_box.setTitle(tr("layout_props_title"))
        if hasattr(self, "lbl_rows"):
            self.lbl_rows.setText(tr("rows_label"))
        if hasattr(self, "lbl_cols"):
            self.lbl_cols.setText(tr("cols_label"))
        if hasattr(self, "lbl_btn_size"):
            self.lbl_btn_size.setText(tr("btn_size_label"))
        if hasattr(self, "size_combo"):
            idx = self.size_combo.currentIndex()
            self.size_combo.blockSignals(True)
            self.size_combo.clear()
            self.size_combo.addItems([tr("size_compact"), tr("size_standard"), tr("size_touch")])
            if idx >= 0:
                self.size_combo.setCurrentIndex(idx)
            self.size_combo.blockSignals(False)
        if hasattr(self, "lbl_opacity"):
            self.lbl_opacity.setText(tr("opacity_slider_label"))
        if hasattr(self, "always_on_top_chk"):
            self.always_on_top_chk.setText(tr("always_on_top_chk"))
        if hasattr(self, "confirm_action_chk"):
            self.confirm_action_chk.setText(tr("confirm_action_chk"))
            self.confirm_action_chk.setToolTip(tr("confirm_action_tip"))
        if hasattr(self, "auto_enter_chk"):
            self.auto_enter_chk.setText(tr("auto_enter_chk"))
            self.auto_enter_chk.setToolTip(tr("auto_enter_tip"))

        # Preview Header
        if hasattr(self, "preview_lbl"):
            self.preview_lbl.setText(tr("preview_lbl"))
            self.preview_lbl.setToolTip(tr("preview_tip"))
        if hasattr(self, "preview_hint"):
            self.preview_hint.setText(tr("preview_hint"))
        if hasattr(self, "transpose_btn"):
            self.transpose_btn.setText(tr("btn_transpose"))
            self.transpose_btn.setToolTip(tr("btn_transpose_tip"))
        if hasattr(self, "clear_slot_btn"):
            self.clear_slot_btn.setText(tr("btn_clear_slot"))
            self.clear_slot_btn.setToolTip(tr("btn_clear_slot_tip"))
        if hasattr(self, "lbl_slot_adjust"):
            self.lbl_slot_adjust.setText(tr("slot_adjust_label"))
        if hasattr(self, "slot_up_btn"):
            self.slot_up_btn.setText(tr("btn_slot_up"))
        if hasattr(self, "slot_down_btn"):
            self.slot_down_btn.setText(tr("btn_slot_down"))
        if hasattr(self, "slot_left_btn"):
            self.slot_left_btn.setText(tr("btn_slot_left"))
        if hasattr(self, "slot_right_btn"):
            self.slot_right_btn.setText(tr("btn_slot_right"))

        # Button Properties
        if hasattr(self, "btn_prop_box"):
            self.btn_prop_box.setTitle(tr("btn_props_title"))
        if hasattr(self, "lbl_slot_status"):
            self.lbl_slot_status.setText(tr("slot_status_label"))
        if hasattr(self, "lbl_display_text"):
            self.lbl_display_text.setText(tr("btn_text_label"))
        if hasattr(self, "btn_label_edit"):
            self.btn_label_edit.setPlaceholderText(tr("btn_text_placeholder"))
            self.btn_label_edit.setToolTip(tr("btn_text_tip"))
        if hasattr(self, "lbl_btn_color"):
            self.lbl_btn_color.setText(tr("btn_color_label"))
        if hasattr(self, "btn_color_combo"):
            c_idx = self.btn_color_combo.currentIndex()
            self.btn_color_combo.blockSignals(True)
            self.btn_color_combo.clear()
            for hex_code, color_key in COLOR_PRESET_KEYS:
                self.btn_color_combo.addItem(tr(color_key), hex_code)
            if c_idx >= 0:
                self.btn_color_combo.setCurrentIndex(c_idx)
            self.btn_color_combo.blockSignals(False)
        if hasattr(self, "lbl_btn_tooltip"):
            self.lbl_btn_tooltip.setText(tr("btn_tooltip_label"))

        # Action Steps
        if hasattr(self, "steps_box"):
            self.steps_box.setTitle(tr("action_steps_title"))
        if hasattr(self, "steps_table"):
            self.steps_table.setHorizontalHeaderLabels([tr("step_col_type"), tr("step_col_param"), tr("step_col_desc")])
        if hasattr(self, "record_macro_btn"):
            self.record_macro_btn.setText(tr("btn_record_macro"))
            self.record_macro_btn.setToolTip(tr("btn_record_macro_tip"))
        if hasattr(self, "add_text_btn"):
            self.add_text_btn.setText(tr("btn_add_text"))
            self.add_text_btn.setToolTip(tr("btn_add_text_tip"))
        if hasattr(self, "add_key_btn"):
            self.add_key_btn.setText(tr("btn_add_key"))
            self.add_key_btn.setToolTip(tr("btn_add_key_tip"))
        if hasattr(self, "add_delay_btn"):
            self.add_delay_btn.setText(tr("btn_add_delay"))
            self.add_delay_btn.setToolTip(tr("btn_add_delay_tip"))
        if hasattr(self, "edit_step_btn"):
            self.edit_step_btn.setText(tr("btn_edit_step"))
        if hasattr(self, "del_step_btn"):
            self.del_step_btn.setText(tr("btn_del_step"))
        if hasattr(self, "move_up_btn"):
            self.move_up_btn.setText(tr("btn_move_up"))
            self.move_up_btn.setToolTip(tr("btn_move_up_tip"))
        if hasattr(self, "move_down_btn"):
            self.move_down_btn.setText(tr("btn_move_down"))
            self.move_down_btn.setToolTip(tr("btn_move_down_tip"))

        # App Binding
        if hasattr(self, "binding_box"):
            self.binding_box.setTitle(tr("app_binding_title"))
        if hasattr(self, "profile_table"):
            self.profile_table.setHorizontalHeaderLabels([tr("bind_col_process"), tr("bind_col_title")])
        if hasattr(self, "bind_curr_btn"):
            self.bind_curr_btn.setText(tr("btn_bind_current"))
            self.bind_curr_btn.setToolTip(tr("btn_bind_current_tip"))
        if hasattr(self, "bind_pick_btn"):
            self.bind_pick_btn.setText(tr("btn_bind_pick"))
            self.bind_pick_btn.setToolTip(tr("btn_bind_pick_tip"))
        if hasattr(self, "bind_custom_btn"):
            self.bind_custom_btn.setText(tr("btn_bind_custom"))
        if hasattr(self, "bind_del_btn"):
            self.bind_del_btn.setText(tr("btn_bind_delete"))

        # General & Diagnostics
        if hasattr(self, "lang_box"):
            self.lang_box.setTitle(tr("language_group_title"))
        if hasattr(self, "lbl_language"):
            self.lbl_language.setText(tr("language_label"))
        if hasattr(self, "hotkey_box"):
            self.hotkey_box.setTitle(tr("hotkey_group_title"))
        if hasattr(self, "lbl_auto_profile"):
            self.lbl_auto_profile.setText(tr("auto_profile_switch_label"))
        if hasattr(self, "auto_profile_switch_chk"):
            self.auto_profile_switch_chk.setText(tr("auto_profile_switch_chk"))
        if hasattr(self, "lbl_toggle_hotkey"):
            self.lbl_toggle_hotkey.setText(tr("toggle_hotkey_label"))
        if hasattr(self, "toggle_hotkey_edit"):
            self.toggle_hotkey_edit.setPlaceholderText(tr("toggle_hotkey_placeholder"))
        if hasattr(self, "lbl_stop_hotkey"):
            self.lbl_stop_hotkey.setText(tr("stop_hotkey_label"))
        if hasattr(self, "stop_hotkey_edit"):
            self.stop_hotkey_edit.setPlaceholderText(tr("stop_hotkey_placeholder"))
        if hasattr(self, "data_box"):
            self.data_box.setTitle(tr("backup_group_title"))
        if hasattr(self, "backup_btn"):
            self.backup_btn.setText(tr("btn_backup"))
        if hasattr(self, "diag_box"):
            self.diag_box.setTitle(tr("diag_group_title"))
        if hasattr(self, "log_table"):
            self.log_table.setHorizontalHeaderLabels([tr("log_col_time"), tr("log_col_action"), tr("log_col_status"), tr("log_col_desc")])
        if hasattr(self, "refresh_diag_btn"):
            self.refresh_diag_btn.setText(tr("btn_refresh_diag"))

        # Bottom buttons
        if hasattr(self, "save_btn"):
            self.save_btn.setText(tr("btn_save_settings"))
        if hasattr(self, "cancel_btn"):
            self.cancel_btn.setText(tr("btn_cancel_settings"))

        # Refresh step table & selection status info
        if hasattr(self, "steps_table"):
            self._refresh_steps(self._current_action())
        if hasattr(self, "selected_info_label"):
            button = self.layout_mgr.get_button(self.selected_button_id) if self.selected_button_id else None
            if button:
                clean_lbl = button.label.replace("\n", " ")
                if self.selected_row is not None and self.selected_col is not None:
                    self.selected_info_label.setText(
                        tr("slot_info_occupied", row=self.selected_row + 1, col=self.selected_col + 1, id=clean_lbl)
                    )
                else:
                    self.selected_info_label.setText(f"ID: {clean_lbl}")
            else:
                self.selected_info_label.setText(tr("no_btn_selected"))

    def save_and_close(self):
        cfg = self.config_store.load_config()
        cfg.setdefault("hotkeys", {})["toggle_visible"] = self.toggle_hotkey_edit.text().strip()
        cfg["hotkeys"]["emergency_stop"] = self.stop_hotkey_edit.text().strip()
        cfg.setdefault("settings", {})["auto_profile_switch"] = self.auto_profile_switch_chk.isChecked()
        cfg.setdefault("settings", {})["language"] = get_current_language()

        cfg["layouts"] = {lid: layout.to_dict() for lid, layout in self.layout_mgr.layouts.items()}
        cfg["buttons"] = {bid: button.to_dict() for bid, button in self.layout_mgr.buttons.items()}
        cfg["actions"] = {aid: action.to_dict() for aid, action in self.layout_mgr.actions.items()}
        cfg["profiles"] = [profile.to_dict() for profile in self.layout_mgr.profiles]
        cfg["active_layout_id"] = self.layout_mgr.active_layout_id

        curr = self._current_layout()
        if curr:
            cfg.setdefault("window", {})["opacity"] = curr.settings.opacity
            cfg["window"]["always_on_top"] = curr.settings.always_on_top

        self.config_store.save_config(cfg)
        self.accept()

    def showEvent(self, event):
        super().showEvent(event)
        try:
            from ui.floating_panel import set_window_dark_titlebar
            set_window_dark_titlebar(int(self.winId()))
        except Exception:
            pass
