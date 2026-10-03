# -*- coding: utf-8 -*-
"""Comprehensive settings center with layout-first preview and contextual button editing."""

from typing import Optional, Dict, Tuple
from PyQt5 import QtCore, QtGui, QtWidgets

from domain.action import Action, ActionStep
from domain.button import Button, format_button_display_text
from domain.layout import Layout
from domain.profile import Profile
from application.layout_manager import LayoutManager
from application.action_executor import ActionExecutor
from application.target_manager import TargetManager
from storage.config_store import ConfigStore
from .macro_recorder_dialog import MacroRecorderDialog
from application.macro_recorder import MacroRecorder

COLOR_PRESETS = [
    ("#1976D2", "蓝色"),
    ("#E53935", "朱红"),
    ("#37474F", "深灰"),
    ("#2E7D32", "绿色"),
    ("#7B1FA2", "紫色"),
    ("#FB8C00", "橙色"),
    ("#0284C7", "青天蓝"),
    ("#4F46E5", "靛蓝"),
]


class NewLayoutDialog(QtWidgets.QDialog):
    """Wizard dialog for creating a new layout with presets."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("新建布局")
        self.setMinimumWidth(380)
        self.setStyleSheet("""
            QDialog {
                background-color: #1E1E20;
                color: #F5F5F7;
                font-family: -apple-system, "SF Pro Text", "PingFang SC", "Segoe UI Variable Text", "Segoe UI", sans-serif;
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
        self.name_edit.setText("新建布局")
        layout.addRow("布局名称", self.name_edit)

        self.rows_spin = QtWidgets.QSpinBox(self)
        self.rows_spin.setRange(1, 20)
        self.rows_spin.setValue(2)
        layout.addRow("行数", self.rows_spin)

        self.cols_spin = QtWidgets.QSpinBox(self)
        self.cols_spin.setRange(1, 20)
        self.cols_spin.setValue(4)
        layout.addRow("列数", self.cols_spin)

        self.size_combo = QtWidgets.QComboBox(self)
        self.size_combo.addItems(["紧凑", "标准", "触屏大按钮"])
        layout.addRow("默认按钮尺寸", self.size_combo)

        btn_box = QtWidgets.QDialogButtonBox(
            QtWidgets.QDialogButtonBox.Ok | QtWidgets.QDialogButtonBox.Cancel, self
        )
        btn_box.button(QtWidgets.QDialogButtonBox.Ok).setText("确认创建")
        btn_box.button(QtWidgets.QDialogButtonBox.Cancel).setText("取消")
        btn_box.accepted.connect(self.accept)
        btn_box.rejected.connect(self.reject)
        layout.addRow(btn_box)

    def get_values(self):
        size_key = ["compact", "standard", "touch"][self.size_combo.currentIndex()]
        return (
            self.name_edit.text().strip() or "新建布局",
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

        self.setWindowTitle("快捷输入工作台 · 设置与布局中心")
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
        target_w = min(1020, max(680, screen.width() - 80))
        target_h = min(720, max(460, screen.height() - 80))
        self.resize(target_w, target_h)

        self.setStyleSheet("""
            QDialog {
                background-color: #1E1E20;
                color: #F5F5F7;
                font-family: -apple-system, "SF Pro Text", "PingFang SC", "Segoe UI Variable Text", "Segoe UI", "Microsoft YaHei UI", sans-serif;
            }
            QWidget {
                font-family: -apple-system, "SF Pro Text", "PingFang SC", "Segoe UI Variable Text", "Segoe UI", "Microsoft YaHei UI", sans-serif;
                color: #F5F5F7;
            }
            QGroupBox {
                background-color: #252528;
                border: 1px solid rgba(255, 255, 255, 0.08);
                border-radius: 10px;
                margin-top: 12px;
                padding: 12px 14px 14px 14px;
                color: #F5F5F7;
            }
            QGroupBox::title {
                subcontrol-origin: margin;
                left: 12px;
                padding: 0 4px;
                color: #F5F5F7;
                font-weight: 600;
                font-size: 12px;
            }
            QLabel {
                color: #F5F5F7;
                font-size: 12px;
            }
            QLineEdit, QComboBox, QSpinBox, QTextEdit {
                background-color: #1C1C1E;
                color: #FFFFFF;
                border: 1px solid rgba(255, 255, 255, 0.12);
                border-radius: 6px;
                padding: 5px 8px;
                font-size: 12px;
            }
            QLineEdit:hover, QComboBox:hover, QSpinBox:hover, QTextEdit:hover {
                border-color: rgba(255, 255, 255, 0.22);
            }
            QLineEdit:focus, QComboBox:focus, QSpinBox:focus, QTextEdit:focus {
                border: 1.5px solid #0A84FF;
                background-color: #202023;
            }
            QComboBox::drop-down {
                subcontrol-origin: padding;
                subcontrol-position: top right;
                width: 18px;
                border-left-width: 0px;
            }
            QComboBox QAbstractItemView {
                background-color: #252528;
                color: #F5F5F7;
                border: 1px solid rgba(255, 255, 255, 0.14);
                border-radius: 8px;
                padding: 4px;
                selection-background-color: #0A84FF;
                selection-color: #FFFFFF;
                outline: none;
            }
            QTableWidget {
                background-color: #18181A;
                color: #F5F5F7;
                border: 1px solid rgba(255, 255, 255, 0.08);
                border-radius: 8px;
                gridline-color: rgba(255, 255, 255, 0.04);
                outline: none;
            }
            QTableWidget::item {
                padding: 4px 6px;
                border-bottom: 1px solid rgba(255, 255, 255, 0.04);
            }
            QTableWidget::item:selected {
                background-color: #0A84FF;
                color: #FFFFFF;
            }
            QHeaderView::section {
                background-color: #222225;
                color: #8E8E93;
                border: none;
                border-bottom: 1px solid rgba(255, 255, 255, 0.10);
                padding: 6px;
                font-size: 11px;
                font-weight: 600;
            }
            QPushButton {
                background-color: rgba(255, 255, 255, 0.08);
                color: #F5F5F7;
                border: 1px solid rgba(255, 255, 255, 0.10);
                border-radius: 6px;
                padding: 5px 12px;
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
            QPushButton:disabled {
                background-color: rgba(255, 255, 255, 0.03);
                color: #636366;
                border-color: rgba(255, 255, 255, 0.05);
            }
            QCheckBox {
                color: #F5F5F7;
                font-size: 12px;
                spacing: 6px;
            }
            QScrollBar:vertical {
                background: transparent;
                width: 8px;
                margin: 0px;
            }
            QScrollBar::handle:vertical {
                background: rgba(255, 255, 255, 0.18);
                border-radius: 4px;
                min-height: 24px;
            }
            QScrollBar::handle:vertical:hover {
                background: rgba(255, 255, 255, 0.32);
            }
            QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {
                height: 0px;
            }
            QScrollBar:horizontal {
                background: transparent;
                height: 8px;
                margin: 0px;
            }
            QScrollBar::handle:horizontal {
                background: rgba(255, 255, 255, 0.18);
                border-radius: 4px;
                min-width: 24px;
            }
            QScrollBar::handle:horizontal:hover {
                background: rgba(255, 255, 255, 0.32);
            }
            QScrollBar::add-line:horizontal, QScrollBar::sub-line:horizontal {
                width: 0px;
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
                border: 1px solid rgba(255, 255, 255, 0.08);
                border-radius: 10px;
                background-color: #202023;
            }
            QTabBar::tab {
                background-color: rgba(255, 255, 255, 0.05);
                color: #8E8E93;
                padding: 7px 20px;
                border-top-left-radius: 6px;
                border-top-right-radius: 6px;
                margin-right: 4px;
                font-size: 12px;
                font-weight: 500;
            }
            QTabBar::tab:selected {
                background-color: #202023;
                color: #FFFFFF;
                border: 1px solid rgba(255, 255, 255, 0.08);
                border-bottom: none;
                font-weight: 600;
            }
            QTabBar::tab:hover:!selected {
                background-color: rgba(255, 255, 255, 0.09);
                color: #F5F5F7;
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
        save = QtWidgets.QPushButton("保存并应用", self)
        save.setStyleSheet("""
            QPushButton {
                background-color: #0A84FF;
                color: #FFFFFF;
                font-weight: 600;
                padding: 8px 24px;
                border-radius: 6px;
                border: none;
                font-size: 13px;
            }
            QPushButton:hover {
                background-color: #0071E3;
            }
            QPushButton:pressed {
                background-color: #005BB5;
            }
        """)
        save.clicked.connect(self.save_and_close)
        bottom.addWidget(save)

        cancel = QtWidgets.QPushButton("关闭", self)
        cancel.setStyleSheet("""
            QPushButton {
                background-color: rgba(255, 255, 255, 0.08);
                color: #F5F5F7;
                font-weight: 500;
                padding: 8px 20px;
                border-radius: 6px;
                border: 1px solid rgba(255, 255, 255, 0.10);
                font-size: 13px;
            }
            QPushButton:hover {
                background-color: rgba(255, 255, 255, 0.14);
            }
        """)
        cancel.clicked.connect(self.reject)
        bottom.addWidget(cancel)
        root.addLayout(bottom)

    def _build_layout_and_buttons_tab(self):
        tab = QtWidgets.QWidget()
        tab_layout = QtWidgets.QVBoxLayout(tab)
        tab_layout.setContentsMargins(10, 10, 10, 10)
        tab_layout.setSpacing(8)

        # Top layout selector & actions
        top_bar = QtWidgets.QHBoxLayout()
        top_bar.addWidget(QtWidgets.QLabel("当前布局:", tab))
        self.layout_selector = QtWidgets.QComboBox(tab)
        self.layout_selector.setMinimumWidth(180)
        self.layout_selector.currentIndexChanged.connect(self._on_layout_selected)
        top_bar.addWidget(self.layout_selector, 1)

        self.new_layout_btn = QtWidgets.QPushButton("＋ 新建布局", tab)
        self.new_layout_btn.clicked.connect(self._new_layout)
        top_bar.addWidget(self.new_layout_btn)

        self.copy_layout_btn = QtWidgets.QPushButton("复制当前布局", tab)
        self.copy_layout_btn.clicked.connect(self._copy_layout)
        top_bar.addWidget(self.copy_layout_btn)

        self.rename_layout_btn = QtWidgets.QPushButton("重命名", tab)
        self.rename_layout_btn.clicked.connect(self._rename_layout)
        top_bar.addWidget(self.rename_layout_btn)

        self.delete_layout_btn = QtWidgets.QPushButton("删除布局", tab)
        self.delete_layout_btn.clicked.connect(self._delete_layout)
        top_bar.addWidget(self.delete_layout_btn)
        tab_layout.addLayout(top_bar)

        # Layout-level properties box (rows, cols, size, opacity, auto-enter, confirm)
        layout_box = QtWidgets.QGroupBox("布局属性与全局默认值 (当前布局)", tab)
        l_form = QtWidgets.QGridLayout(layout_box)
        l_form.setHorizontalSpacing(14)
        l_form.setVerticalSpacing(8)

        # Row 0: Rows, Columns, Button Size
        l_form.addWidget(QtWidgets.QLabel("行数:"), 0, 0)
        self.rows_spin = QtWidgets.QSpinBox(layout_box)
        self.rows_spin.setRange(1, 20)
        self.rows_spin.valueChanged.connect(self._layout_property_changed)
        l_form.addWidget(self.rows_spin, 0, 1)

        l_form.addWidget(QtWidgets.QLabel("列数:"), 0, 2)
        self.cols_spin = QtWidgets.QSpinBox(layout_box)
        self.cols_spin.setRange(1, 20)
        self.cols_spin.valueChanged.connect(self._layout_property_changed)
        l_form.addWidget(self.cols_spin, 0, 3)

        l_form.addWidget(QtWidgets.QLabel("按钮尺寸:"), 0, 4)
        self.size_combo = QtWidgets.QComboBox(layout_box)
        self.size_combo.addItems(["紧凑", "标准", "触屏大按钮"])
        self.size_combo.currentIndexChanged.connect(self._layout_property_changed)
        l_form.addWidget(self.size_combo, 0, 5)

        # Row 1: Opacity, Always On Top, Confirm, Auto-Enter
        l_form.addWidget(QtWidgets.QLabel("透明度:"), 1, 0)
        self.opacity_slider = QtWidgets.QSlider(QtCore.Qt.Horizontal, layout_box)
        self.opacity_slider.setRange(30, 100)
        self.opacity_slider.valueChanged.connect(self._layout_property_changed)
        l_form.addWidget(self.opacity_slider, 1, 1)

        self.always_on_top_chk = QtWidgets.QCheckBox("保持在顶层", layout_box)
        self.always_on_top_chk.stateChanged.connect(self._layout_property_changed)
        l_form.addWidget(self.always_on_top_chk, 1, 2)

        self.confirm_action_chk = QtWidgets.QCheckBox("执行前确认", layout_box)
        self.confirm_action_chk.setToolTip("开启后，点击当前布局内任何按钮执行动作前均弹出确认对话框")
        self.confirm_action_chk.stateChanged.connect(self._layout_property_changed)
        l_form.addWidget(self.confirm_action_chk, 1, 3)

        self.auto_enter_chk = QtWidgets.QCheckBox("动作结束后发送 Enter", layout_box)
        self.auto_enter_chk.setToolTip("开启后，当前布局所有动作执行完毕后自动追加一个 Enter 回车键")
        self.auto_enter_chk.stateChanged.connect(self._layout_property_changed)
        l_form.addWidget(self.auto_enter_chk, 1, 4, 1, 2)

        tab_layout.addWidget(layout_box)

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
        preview_lbl = QtWidgets.QLabel("布局预览:", left_widget)
        preview_lbl.setToolTip("点击按钮即可选中编辑；支持拖动按钮与其他槽位调换位置")
        top_preview_bar.addWidget(preview_lbl)
        preview_hint = QtWidgets.QLabel("（点击选中 / 拖动调换）", left_widget)
        preview_hint.setStyleSheet("color: #8E8E93; font-size: 11px;")
        top_preview_bar.addWidget(preview_hint)
        top_preview_bar.addStretch()

        self.transpose_btn = QtWidgets.QPushButton("⇄ 行列转换", left_widget)
        self.transpose_btn.setToolTip("转换行列（转置布局），行列数互换")
        self.transpose_btn.clicked.connect(self._transpose_layout)
        top_preview_bar.addWidget(self.transpose_btn)

        self.clear_slot_btn = QtWidgets.QPushButton("清空槽位", left_widget)
        self.clear_slot_btn.setToolTip("删除当前选中槽位的按钮并保留空槽位")
        self.clear_slot_btn.clicked.connect(self._clear_selected_slot)
        top_preview_bar.addWidget(self.clear_slot_btn)
        preview_header.addLayout(top_preview_bar)

        slot_nav_bar = QtWidgets.QHBoxLayout()
        slot_nav_bar.addWidget(QtWidgets.QLabel("槽位微调:", left_widget))
        self.move_up_btn = QtWidgets.QPushButton("▲ 上移", left_widget)
        self.move_up_btn.setToolTip("将选中按钮与上一行对应槽位交换")
        self.move_up_btn.clicked.connect(lambda: self._move_slot(-1, 0))
        slot_nav_bar.addWidget(self.move_up_btn)

        self.move_down_btn = QtWidgets.QPushButton("▼ 下移", left_widget)
        self.move_down_btn.setToolTip("将选中按钮与下一行对应槽位交换")
        self.move_down_btn.clicked.connect(lambda: self._move_slot(1, 0))
        slot_nav_bar.addWidget(self.move_down_btn)

        self.move_left_btn = QtWidgets.QPushButton("◀ 左移", left_widget)
        self.move_left_btn.setToolTip("将选中按钮与左侧槽位交换")
        self.move_left_btn.clicked.connect(lambda: self._move_slot(0, -1))
        slot_nav_bar.addWidget(self.move_left_btn)

        self.move_right_btn = QtWidgets.QPushButton("▶ 右移", left_widget)
        self.move_right_btn.setToolTip("将选中按钮与右侧槽位交换")
        self.move_right_btn.clicked.connect(lambda: self._move_slot(0, 1))
        slot_nav_bar.addWidget(self.move_right_btn)
        slot_nav_bar.addStretch()
        preview_header.addLayout(slot_nav_bar)

        left_layout.addLayout(preview_header)

        # Scroll area for the preview grid
        scroll = QtWidgets.QScrollArea(left_widget)
        scroll.setWidgetResizable(True)
        scroll.setStyleSheet("QScrollArea { border: 1px solid rgba(255, 255, 255, 0.08); border-radius: 8px; background-color: #18181A; }")
        self.preview_container = QtWidgets.QWidget()
        self.preview_grid = QtWidgets.QGridLayout(self.preview_container)
        self.preview_grid.setContentsMargins(10, 10, 10, 10)
        self.preview_grid.setSpacing(6)
        scroll.setWidget(self.preview_container)
        left_layout.addWidget(scroll, 1)

        splitter.addWidget(left_widget)

        # RIGHT: Selected Button Properties, Steps, and Bindings (inside scroll area to allow dialog shrinking)
        right_scroll = QtWidgets.QScrollArea(splitter)
        right_scroll.setWidgetResizable(True)
        right_scroll.setFrameShape(QtWidgets.QFrame.NoFrame)
        right_scroll.setStyleSheet("QScrollArea { border: none; background: transparent; }")

        right_widget = QtWidgets.QWidget()
        right_layout = QtWidgets.QVBoxLayout(right_widget)
        right_layout.setContentsMargins(4, 0, 4, 0)
        right_layout.setSpacing(6)

        # Button properties box
        btn_prop_box = QtWidgets.QGroupBox("选中按钮属性", right_widget)
        bp_grid = QtWidgets.QGridLayout(btn_prop_box)
        bp_grid.setSpacing(6)

        self.selected_info_label = QtWidgets.QLabel("未选中按钮（请在左侧预览中点击按钮）", btn_prop_box)
        self.selected_info_label.setStyleSheet("color: #0A84FF; font-weight: 600; font-size: 12px;")
        bp_grid.addWidget(QtWidgets.QLabel("槽位状态:"), 0, 0)
        bp_grid.addWidget(self.selected_info_label, 0, 1, 1, 3)

        bp_grid.addWidget(QtWidgets.QLabel("显示文字:"), 1, 0)
        self.btn_label_edit = QtWidgets.QLineEdit(btn_prop_box)
        self.btn_label_edit.textChanged.connect(self._button_property_changed)
        bp_grid.addWidget(self.btn_label_edit, 1, 1)

        bp_grid.addWidget(QtWidgets.QLabel("按钮颜色:"), 1, 2)
        self.btn_color_combo = QtWidgets.QComboBox(btn_prop_box)
        for hex_code, color_name in COLOR_PRESETS:
            self.btn_color_combo.addItem(color_name, hex_code)
        self.btn_color_combo.currentIndexChanged.connect(self._button_property_changed)
        bp_grid.addWidget(self.btn_color_combo, 1, 3)

        bp_grid.addWidget(QtWidgets.QLabel("悬浮提示:"), 2, 0)
        self.btn_tooltip_edit = QtWidgets.QLineEdit(btn_prop_box)
        self.btn_tooltip_edit.textChanged.connect(self._button_property_changed)
        bp_grid.addWidget(self.btn_tooltip_edit, 2, 1, 1, 3)

        right_layout.addWidget(btn_prop_box)

        # Macro steps box
        steps_box = QtWidgets.QGroupBox("宏步骤", right_widget)
        steps_layout = QtWidgets.QVBoxLayout(steps_box)
        steps_layout.setSpacing(6)

        self.steps_table = QtWidgets.QTableWidget(steps_box)
        self.steps_table.setMinimumHeight(110)
        self.steps_table.setColumnCount(3)
        self.steps_table.setHorizontalHeaderLabels(["步骤", "参数", "说明"])
        self.steps_table.horizontalHeader().setSectionResizeMode(0, QtWidgets.QHeaderView.ResizeToContents)
        self.steps_table.horizontalHeader().setSectionResizeMode(1, QtWidgets.QHeaderView.Stretch)
        self.steps_table.horizontalHeader().setSectionResizeMode(2, QtWidgets.QHeaderView.ResizeToContents)
        self.steps_table.setSelectionBehavior(QtWidgets.QAbstractItemView.SelectRows)
        self.steps_table.doubleClicked.connect(self._edit_step)
        steps_layout.addWidget(self.steps_table, 1)

        # Step toolbars - compact 2-row grid to prevent horizontal overflow
        step_grid = QtWidgets.QGridLayout()
        step_grid.setSpacing(4)

        self.record_macro_btn = QtWidgets.QPushButton("⏺ 录制宏…", steps_box)
        self.record_macro_btn.setStyleSheet(
            "QPushButton { background-color: #FF453A; color: #FFFFFF; font-weight: 600; border-radius: 6px; border: none; padding: 5px 12px; } QPushButton:hover { background-color: #D70015; }"
        )
        self.record_macro_btn.setToolTip("实时录制键盘与鼠标操作")
        self.record_macro_btn.clicked.connect(self._record_macro)
        step_grid.addWidget(self.record_macro_btn, 0, 0)

        for col_idx, (label, kind, tip) in enumerate([
            ("＋ 文本", "text", "添加文本输入步骤"),
            ("＋ 粘贴", "paste", "添加剪贴板粘贴步骤"),
            ("＋ 按键", "key", "添加单个按键动作"),
        ], start=1):
            b = QtWidgets.QPushButton(label, steps_box)
            b.setToolTip(tip)
            b.clicked.connect(lambda ch=False, k=kind: self._add_step(k))
            step_grid.addWidget(b, 0, col_idx)

        for col_idx, (label, kind, tip) in enumerate([
            ("＋ 组合键", "hotkey", "添加快捷键组合步骤"),
            ("＋ 等待", "delay", "添加延时等待毫秒步骤"),
        ], start=0):
            b = QtWidgets.QPushButton(label, steps_box)
            b.setToolTip(tip)
            b.clicked.connect(lambda ch=False, k=kind: self._add_step(k))
            step_grid.addWidget(b, 1, col_idx)

        edit_s = QtWidgets.QPushButton("编辑步骤", steps_box)
        edit_s.clicked.connect(self._edit_step)
        step_grid.addWidget(edit_s, 1, 2)

        del_s = QtWidgets.QPushButton("删除步骤", steps_box)
        del_s.clicked.connect(self._delete_step)
        step_grid.addWidget(del_s, 1, 3)

        steps_layout.addLayout(step_grid)

        step_nav = QtWidgets.QHBoxLayout()
        up_s = QtWidgets.QPushButton("▲ 上移", steps_box)
        up_s.setToolTip("将当前选中的宏步骤上移一位")
        up_s.clicked.connect(lambda: self._move_step(-1))
        step_nav.addWidget(up_s)

        dn_s = QtWidgets.QPushButton("▼ 下移", steps_box)
        dn_s.setToolTip("将当前选中的宏步骤下移一位")
        dn_s.clicked.connect(lambda: self._move_step(1))
        step_nav.addWidget(dn_s)
        step_nav.addStretch()
        steps_layout.addLayout(step_nav)

        right_layout.addWidget(steps_box, 1)

        # App binding box for current layout
        binding_box = QtWidgets.QGroupBox("应用绑定 (切到指定软件时自动启用当前布局)", right_widget)
        b_layout = QtWidgets.QVBoxLayout(binding_box)
        b_layout.setSpacing(6)

        self.profile_table = QtWidgets.QTableWidget(binding_box)
        self.profile_table.setMinimumHeight(90)
        self.profile_table.setColumnCount(2)
        self.profile_table.setHorizontalHeaderLabels(["目标进程名", "窗口标题包含"])
        self.profile_table.horizontalHeader().setSectionResizeMode(QtWidgets.QHeaderView.Stretch)
        self.profile_table.setSelectionBehavior(QtWidgets.QAbstractItemView.SelectRows)
        b_layout.addWidget(self.profile_table)

        b_btns1 = QtWidgets.QHBoxLayout()
        bind_curr = QtWidgets.QPushButton("🎯 绑定当前目标应用", binding_box)
        bind_curr.clicked.connect(self._add_current_target_profile)
        b_btns1.addWidget(bind_curr)

        bind_custom = QtWidgets.QPushButton("＋ 添加自定义绑定", binding_box)
        bind_custom.clicked.connect(self._add_custom_profile)
        b_btns1.addWidget(bind_custom)
        b_layout.addLayout(b_btns1)

        b_btns2 = QtWidgets.QHBoxLayout()
        bind_del = QtWidgets.QPushButton("删除选中绑定", binding_box)
        bind_del.clicked.connect(self._delete_profile)
        b_btns2.addWidget(bind_del)
        b_btns2.addStretch()
        b_layout.addLayout(b_btns2)

        right_layout.addWidget(binding_box)

        right_scroll.setWidget(right_widget)
        splitter.addWidget(right_scroll)
        splitter.setStretchFactor(0, 1)
        splitter.setStretchFactor(1, 1)
        splitter.setSizes([450, 540])
        tab_layout.addWidget(splitter, 1)
        tab_scroll = QtWidgets.QScrollArea(self.tabs)
        tab_scroll.setWidgetResizable(True)
        tab_scroll.setFrameShape(QtWidgets.QFrame.NoFrame)
        tab_scroll.setStyleSheet("QScrollArea { border: none; background: transparent; }")
        tab_scroll.setWidget(tab)
        self.tabs.addTab(tab_scroll, "布局与按钮")

    def _build_general_and_diag_tab(self):
        tab_scroll = QtWidgets.QScrollArea(self.tabs)
        tab_scroll.setWidgetResizable(True)
        tab_scroll.setFrameShape(QtWidgets.QFrame.NoFrame)
        tab_scroll.setStyleSheet("QScrollArea { border: none; background: transparent; }")

        tab = QtWidgets.QWidget()
        layout = QtWidgets.QVBoxLayout(tab)
        layout.setContentsMargins(14, 14, 14, 14)
        layout.setSpacing(12)

        # 1. Hotkeys & Global Options
        hotkey_box = QtWidgets.QGroupBox("全局快捷键与自动化", tab)
        hk_form = QtWidgets.QFormLayout(hotkey_box)
        hk_form.setSpacing(10)

        self.auto_profile_switch_chk = QtWidgets.QCheckBox("根据前台活动窗口自动切换布局", hotkey_box)
        hk_form.addRow("场景切换", self.auto_profile_switch_chk)

        self.toggle_hotkey_edit = QtWidgets.QLineEdit(hotkey_box)
        self.toggle_hotkey_edit.setPlaceholderText("例如 ALT+Q")
        hk_form.addRow("显示/隐藏工作台", self.toggle_hotkey_edit)

        self.stop_hotkey_edit = QtWidgets.QLineEdit(hotkey_box)
        self.stop_hotkey_edit.setPlaceholderText("例如 ESC")
        hk_form.addRow("紧急停止宏快捷键", self.stop_hotkey_edit)
        layout.addWidget(hotkey_box)

        # 2. Backup & Restore
        data_box = QtWidgets.QGroupBox("配置备份与恢复", tab)
        d_layout = QtWidgets.QHBoxLayout(data_box)
        backup_btn = QtWidgets.QPushButton("备份当前配置", data_box)
        backup_btn.clicked.connect(self._backup_config)
        d_layout.addWidget(backup_btn)
        d_layout.addStretch()
        layout.addWidget(data_box)

        # 3. Diagnostics
        diag_box = QtWidgets.QGroupBox("系统诊断与最近执行日志", tab)
        diag_layout = QtWidgets.QVBoxLayout(diag_box)

        self.target_info_label = QtWidgets.QLabel("目标检测: 未检测", diag_box)
        diag_layout.addWidget(self.target_info_label)

        self.log_table = QtWidgets.QTableWidget(diag_box)
        self.log_table.setMinimumHeight(100)
        self.log_table.setColumnCount(4)
        self.log_table.setHorizontalHeaderLabels(["时间", "动作 ID", "状态", "说明"])
        self.log_table.horizontalHeader().setSectionResizeMode(0, QtWidgets.QHeaderView.ResizeToContents)
        self.log_table.horizontalHeader().setSectionResizeMode(1, QtWidgets.QHeaderView.ResizeToContents)
        self.log_table.horizontalHeader().setSectionResizeMode(2, QtWidgets.QHeaderView.ResizeToContents)
        self.log_table.horizontalHeader().setSectionResizeMode(3, QtWidgets.QHeaderView.Stretch)
        diag_layout.addWidget(self.log_table, 1)

        refresh_diag_btn = QtWidgets.QPushButton("刷新诊断信息", diag_box)
        refresh_diag_btn.clicked.connect(self._refresh_diag)
        diag_layout.addWidget(refresh_diag_btn)

        layout.addWidget(diag_box, 1)
        tab_scroll.setWidget(tab)
        self.tabs.addTab(tab_scroll, "常规与诊断")

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
        self.target_info_label.setText(
            f"目标窗口: {info.get('title', '')} | 进程: {info.get('process_name', '')} | PID: {info.get('process_id', '')} | 句柄: {info.get('handle', '')} | 锁定: {info.get('is_locked', False)}"
        )
        logs = getattr(self.executor, "execution_logs", [])
        self.log_table.setRowCount(len(logs))
        for row, entry in enumerate(reversed(logs)):
            self.log_table.setItem(row, 0, QtWidgets.QTableWidgetItem(entry.get("timestamp", "")))
            self.log_table.setItem(row, 1, QtWidgets.QTableWidgetItem(entry.get("action_id", "")))
            ok_item = QtWidgets.QTableWidgetItem("成功" if entry.get("success") else "失败")
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

        layout.rows = self.rows_spin.value()
        layout.columns = self.cols_spin.value()
        layout.settings.button_size = ["compact", "standard", "touch"][self.size_combo.currentIndex()]
        layout.settings.opacity = self.opacity_slider.value() / 100.0
        layout.settings.always_on_top = self.always_on_top_chk.isChecked()
        layout.settings.confirm_before_action = self.confirm_action_chk.isChecked()
        layout.settings.auto_enter_default = self.auto_enter_chk.isChecked()

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
                    display_text = format_button_display_text(btn_model.icon, btn_model.label)
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
                            font-family: -apple-system, "SF Pro Text", "PingFang SC", "Segoe UI Variable Text", "Segoe UI", sans-serif;
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
                    empty_btn.setToolTip("点击创建此槽位按钮，或将其他按钮拖放到此处")
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
                self.selected_info_label.setText(f"第 {row + 1} 行，第 {col + 1} 列 (文字: {clean_lbl})")
            else:
                self.selected_info_label.setText(f"文字: {clean_lbl}")
            self.btn_label_edit.setEnabled(True)
            self.btn_label_edit.setText(button.label)
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
                        font-family: -apple-system, "SF Pro Text", "PingFang SC", "Segoe UI Variable Text", "Segoe UI", sans-serif;
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
        self.selected_info_label.setText("未选中按钮（请在左侧预览中点击按钮）")
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
        btn = self.layout_mgr.create_button_for_slot(
            layout.id, row, col, label=f"按钮 {len(layout.buttons) + 1}"
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
        button.label = self.btn_label_edit.text()
        button.tooltip = self.btn_tooltip_edit.text()
        button.color = self.btn_color_combo.currentData() or "#1976D2"
        if action:
            action.label = button.label

        if self.selected_row is not None and self.selected_col is not None:
            clean_lbl = button.label.replace("\n", " ")
            self.selected_info_label.setText(f"第 {self.selected_row + 1} 行，第 {self.selected_col + 1} 列 (文字: {clean_lbl})")

        # Update preview button widget directly in place without grid rebuild
        coord = (self.selected_row, self.selected_col)
        widget = self._preview_widgets.get(coord)
        if widget and hasattr(widget, "setText"):
            display_text = format_button_display_text(button.icon, button.label)
            widget.setText(display_text)
            widget.setToolTip(button.tooltip or button.label)
            border = "3px solid #00E676"
            widget.setStyleSheet(f"""
                QPushButton {{
                    background-color: {button.color};
                    color: #FFFFFF;
                    font-weight: 600;
                    font-family: -apple-system, "SF Pro Text", "PingFang SC", "Segoe UI Variable Text", "Segoe UI", sans-serif;
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
            type_item = QtWidgets.QTableWidgetItem(step.type)
            val_item = QtWidgets.QTableWidgetItem(str(value))
            desc_item = QtWidgets.QTableWidgetItem("宏步骤")
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
            QtWidgets.QMessageBox.information(self, "提示", "请先在预览中选择一个按钮。")
            return
        step = None
        if kind == "text":
            val, ok = QtWidgets.QInputDialog.getText(self, "添加文本步骤", "输入要输入的文本内容:")
            if ok and val:
                step = ActionStep(type="text", value=val)
        elif kind == "key":
            common_keys = [
                "ENTER", "TAB", "ESC", "SPACE", "BACKSPACE", "DELETE",
                "UP", "DOWN", "LEFT", "RIGHT", "PAGEUP", "PAGEDOWN", "HOME", "END",
                "F1", "F2", "F3", "F4", "F5", "F6", "F7", "F8", "F9", "F10", "F11", "F12"
            ]
            key, ok = QtWidgets.QInputDialog.getItem(self, "添加按键步骤", "选择或输入按键:", common_keys, 0, True)
            if ok and key:
                step = ActionStep(type="key", key=key.strip().upper())
        elif kind == "hotkey":
            val, ok = QtWidgets.QInputDialog.getText(self, "添加组合键步骤", "输入组合键 (例如 CTRL+S):")
            if ok and val:
                val = val.strip().upper()
                step = ActionStep(type="hotkey", hotkey=val, keys=[k.strip() for k in val.split("+") if k.strip()])
        elif kind == "delay":
            ms, ok = QtWidgets.QInputDialog.getInt(self, "添加等待步骤", "输入等待毫秒数 (ms):", 200, 10, 30000)
            if ok:
                step = ActionStep(type="delay", ms=ms)
        elif kind == "paste":
            val, ok = QtWidgets.QInputDialog.getMultiLineText(self, "添加粘贴步骤", "输入要通过剪贴板粘贴的文本:")
            if ok and val:
                step = ActionStep(type="paste", value=val)

        if step:
            action.steps.append(step)
            self._refresh_steps(action)

    def _edit_step(self):
        action = self._current_action()
        row = self.steps_table.currentRow()
        if not action or not (0 <= row < len(action.steps)):
            return
        step = action.steps[row]
        if step.type == "text":
            val, ok = QtWidgets.QInputDialog.getText(self, "编辑文本步骤", "文本内容:", text=step.value)
            if ok:
                step.value = val
        elif step.type == "key":
            val, ok = QtWidgets.QInputDialog.getText(self, "编辑按键步骤", "按键名称:", text=step.key)
            if ok and val:
                step.key = val.strip().upper()
        elif step.type == "hotkey":
            val, ok = QtWidgets.QInputDialog.getText(
                self, "编辑组合键步骤", "组合键 (例如 CTRL+S):", text=step.hotkey or "+".join(step.keys)
            )
            if ok and val:
                step.hotkey = val.strip().upper()
                step.keys = [k.strip() for k in step.hotkey.split("+") if k.strip()]
        elif step.type == "delay":
            ms, ok = QtWidgets.QInputDialog.getInt(self, "编辑等待步骤", "毫秒数:", value=step.ms, min=10, max=30000)
            if ok:
                step.ms = ms
        elif step.type == "paste":
            val, ok = QtWidgets.QInputDialog.getMultiLineText(self, "编辑粘贴步骤", "粘贴内容:", text=step.value)
            if ok:
                step.value = val
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
            QtWidgets.QMessageBox.information(self, "提示", "请先在左侧预览中选择一个按钮。")
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
            QtWidgets.QMessageBox.warning(self, "未检测到目标", "请先在目标软件窗口中点击一次，然后再尝试绑定。")
            return
        # Add profile
        p_id = f"profile_{len(self.layout_mgr.profiles) + 1}"
        profile = Profile(id=p_id, process=proc, layout_id=layout.id)
        self.layout_mgr.register_profile(profile)
        self._refresh_profiles_for_current_layout()
        QtWidgets.QMessageBox.information(self, "绑定成功", f"已成功将应用 {proc} 绑定到当前布局【{layout.name}】！")

    def _add_custom_profile(self):
        layout = self._current_layout()
        if not layout:
            return
        proc, ok1 = QtWidgets.QInputDialog.getText(self, "添加应用绑定", "目标进程名 (例如 notepad.exe):")
        if not ok1 or not proc.strip():
            return
        title, ok2 = QtWidgets.QInputDialog.getText(self, "添加应用绑定", "窗口标题包含字符 (可选，留空匹配所有):")
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
            self, "复制布局", "新布局名称:", text=source.name + " 副本"
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
            self, "重命名布局", "新布局名称:", text=layout.name
        )
        if ok and name.strip():
            layout.name = name.strip()
            self._refresh_layout_selector()
            self._load_active_layout()

    def _delete_layout(self):
        layout = self._current_layout()
        if not layout or len(self.layout_mgr.layouts) <= 1:
            QtWidgets.QMessageBox.warning(self, "无法删除", "系统至少必须保留一个布局。")
            return
        if QtWidgets.QMessageBox.question(
            self, "删除布局", f"确定删除布局“{layout.name}”吗？关联的独立按钮也将被清理。"
        ) != QtWidgets.QMessageBox.Yes:
            return
        self.layout_mgr.delete_layout(layout.id)
        self._refresh_layout_selector()
        self._load_active_layout()

    def _backup_config(self):
        path = self.config_store.create_backup()
        if path:
            QtWidgets.QMessageBox.information(self, "配置备份成功", f"配置已备份至：\n{path}")
        else:
            QtWidgets.QMessageBox.warning(self, "备份失败", "无法创建配置备份。")

    def save_and_close(self):
        cfg = self.config_store.load_config()
        cfg.setdefault("hotkeys", {})["toggle_visible"] = self.toggle_hotkey_edit.text().strip()
        cfg["hotkeys"]["emergency_stop"] = self.stop_hotkey_edit.text().strip()
        cfg.setdefault("settings", {})["auto_profile_switch"] = self.auto_profile_switch_chk.isChecked()

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
