# -*- coding: utf-8 -*-
"""Wizard dialog for creating a new layout with presets."""

from PyQt5 import QtWidgets
from domain.i18n import tr


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
