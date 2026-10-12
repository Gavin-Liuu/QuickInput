# -*- coding: utf-8 -*-
"""Dialog for capturing individual keypresses or hotkey combinations."""

from PyQt5 import QtCore, QtGui, QtWidgets
from domain.i18n import tr


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
