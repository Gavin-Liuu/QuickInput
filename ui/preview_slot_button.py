# -*- coding: utf-8 -*-
"""Preview slot button widget supporting click selection and drag-drop swapping."""

from typing import Optional
from PyQt5 import QtCore, QtGui, QtWidgets
from domain.button import Button


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
