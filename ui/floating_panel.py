# -*- coding: utf-8 -*-
"""Floating action panel with zero-focus normal operation, native frame, and editable search."""

from ctypes import wintypes
from typing import Optional, List

from PyQt5 import QtCore, QtGui, QtWidgets, sip
import win32gui
import win32con

from domain.button import Button
from domain.layout import Layout
from application.layout_manager import LayoutManager
from application.action_executor import ActionExecutor
from application.target_manager import TargetManager
from storage.config_store import ConfigStore
from .settings_dialog import SettingsDialog
from .qt_signals import ExecutorSignals

WM_MOUSEACTIVATE = 0x0021
MA_NOACTIVATE = 3
WS_EX_NOACTIVATE = 0x08000000


def get_action_button_style(color_hex: str, font_size: int = 9) -> str:
    """Generate high-tactile linear gradient stylesheet matching floating_keyboard."""
    c = QtGui.QColor(color_hex or "#1976D2")
    r, g, b = c.red(), c.green(), c.blue()
    # Red chess pieces & variants
    if r > 160 and g < 100 and b < 100:
        return f"""
            QPushButton {{
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1, stop:0 #E53935, stop:1 #C62828);
                color: #FFFFFF;
                font-family: "Segoe UI", "Microsoft YaHei", sans-serif;
                font-size: {font_size}px;
                font-weight: bold;
                border: 1px solid #B71C1C;
                border-radius: 4px;
                padding: 1px;
            }}
            QPushButton:hover {{
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1, stop:0 #EF5350, stop:1 #D32F2F);
                border: 1px solid #FF8A80;
            }}
            QPushButton:pressed {{
                background: #9A0007;
                border: 1px solid #600000;
                padding-top: 2px;
                padding-left: 1px;
            }}
        """
    # Black / Obsidian chess pieces & dark variants
    elif r < 90 and g < 100 and b < 110 and abs(r - g) < 30 and abs(g - b) < 30:
        return f"""
            QPushButton {{
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1, stop:0 #37474F, stop:1 #212121);
                color: #ECEFF1;
                font-family: "Segoe UI", "Microsoft YaHei", sans-serif;
                font-size: {font_size}px;
                font-weight: bold;
                border: 1px solid #263238;
                border-radius: 4px;
                padding: 1px;
            }}
            QPushButton:hover {{
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1, stop:0 #455A64, stop:1 #2C383F);
                border: 1px solid #90A4AE;
            }}
            QPushButton:pressed {{
                background: #101518;
                border: 1px solid #000000;
                padding-top: 2px;
                padding-left: 1px;
            }}
        """
    else:
        # Dynamic bevel gradient for arbitrary colors
        top = c.lighter(115).name()
        bottom = c.darker(118).name()
        border = c.darker(135).name()
        hover_top = c.lighter(130).name()
        hover_bottom = c.lighter(105).name()
        hover_border = c.lighter(140).name()
        pressed_bg = c.darker(140).name()
        pressed_border = c.darker(165).name()
        return f"""
            QPushButton {{
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1, stop:0 {top}, stop:1 {bottom});
                color: #FFFFFF;
                font-family: "Segoe UI", "Microsoft YaHei", sans-serif;
                font-size: {font_size}px;
                font-weight: bold;
                border: 1px solid {border};
                border-radius: 4px;
                padding: 1px;
            }}
            QPushButton:hover {{
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1, stop:0 {hover_top}, stop:1 {hover_bottom});
                border: 1px solid {hover_border};
            }}
            QPushButton:pressed {{
                background: {pressed_bg};
                border: 1px solid {pressed_border};
                padding-top: 2px;
                padding-left: 1px;
            }}
        """


class ActionButtonWidget(QtWidgets.QPushButton):
    """A button that never accepts keyboard focus during panel operation."""

    def __init__(self, button_model: Button, parent=None):
        super().__init__(parent)
        self.button_model = button_model
        self.setFocusPolicy(QtCore.Qt.NoFocus)
        self.setCursor(QtGui.QCursor(QtCore.Qt.PointingHandCursor))
        self.setText(button_model.display_text)
        self.setToolTip(button_model.tooltip or button_model.label)
        self.apply_scale(1.0)

    def apply_scale(self, scale: float):
        width, height, font_size = 36, 30, 9
        width = max(32, min(140, int(width * scale)))
        height = max(28, min(90, int(height * scale)))
        font = max(9, min(16, int(font_size * scale)))
        self.setFixedSize(width, height)
        self.setStyleSheet(get_action_button_style(self.button_model.color, font))

    def flash_feedback(self):
        original = self.styleSheet()
        self.setStyleSheet(original + "QPushButton { border: 2px solid #00E676; }")
        QtCore.QTimer.singleShot(150, lambda: self.setStyleSheet(original))


class FloatingPanel(QtWidgets.QWidget):
    """Always-on-top, resizable, and configurable action panel."""

    def __init__(
        self,
        layout_mgr: LayoutManager,
        executor: ActionExecutor,
        target_mgr: TargetManager,
        config_store: ConfigStore,
        hotkey_mgr=None,
        parent=None,
    ):
        super().__init__(parent)
        self.layout_mgr = layout_mgr
        self.executor = executor
        self.target_mgr = target_mgr
        self.config_store = config_store
        self.hotkey_mgr = hotkey_mgr
        self.config = self.config_store.load_config()
        self._drag_pos: Optional[QtCore.QPoint] = None
        self._auto_sizing = False
        self._search_interactive = False
        self._allow_close = False
        self._current_layout_id: Optional[str] = self.layout_mgr.active_layout_id
        self.buttons_widgets: List[ActionButtonWidget] = []

        self.signals = ExecutorSignals()
        self.signals.started.connect(self._on_exec_started)
        self.signals.step_progress.connect(self._on_exec_step)
        self.signals.finished.connect(self._on_exec_finished)
        self.executor.on_start = lambda aid, total: self.signals.started.emit(aid, total)
        self.executor.on_step = lambda step, total, desc: self.signals.step_progress.emit(step, total, desc)
        self.executor.on_finish = lambda aid, ok, msg: self.signals.finished.emit(aid, ok, msg)

        self.init_window_flags()
        self.init_ui()
        self.apply_config()
        self.layout_mgr.add_layout_changed_listener(self.on_layout_changed_event)

        self.focus_monitor_timer = QtCore.QTimer(self)
        self.focus_monitor_timer.timeout.connect(self._on_monitor_tick)
        self.focus_monitor_timer.start(100)

    def init_window_flags(self):
        flags = (
            QtCore.Qt.FramelessWindowHint
            | QtCore.Qt.WindowStaysOnTopHint
            | QtCore.Qt.Tool
            | QtCore.Qt.WindowDoesNotAcceptFocus
        )
        self.setWindowFlags(flags)
        self.setAttribute(QtCore.Qt.WA_TranslucentBackground, True)
        self.setAttribute(QtCore.Qt.WA_ShowWithoutActivating, True)
        self.setMinimumSize(80, 40)
        self.setWindowTitle("快捷输入工作台")

    def showEvent(self, event):
        super().showEvent(event)
        try:
            hwnd = int(self.winId())
            self.target_mgr.register_own_hwnd(hwnd)
            ex_style = win32gui.GetWindowLong(hwnd, win32con.GWL_EXSTYLE)
            active_layout = self.layout_mgr.get_active_layout()
            keep_top = bool(active_layout.settings.always_on_top) if active_layout else True
            ex_style |= win32con.WS_EX_NOACTIVATE | win32con.WS_EX_TOOLWINDOW
            if keep_top:
                ex_style |= win32con.WS_EX_TOPMOST
            else:
                ex_style &= ~win32con.WS_EX_TOPMOST
            win32gui.SetWindowLong(hwnd, win32con.GWL_EXSTYLE, ex_style)
            win32gui.SetWindowPos(
                hwnd,
                win32con.HWND_TOPMOST if keep_top else win32con.HWND_NOTOPMOST,
                0, 0, 0, 0,
                win32con.SWP_NOMOVE | win32con.SWP_NOSIZE | win32con.SWP_NOACTIVATE,
            )
        except Exception as exc:
            print("SetWindowLong error:", exc)

    def nativeEvent(self, event_type, message):
        try:
            msg = wintypes.MSG.from_address(int(message))
            if msg.message == WM_MOUSEACTIVATE and not self._search_interactive:
                return True, MA_NOACTIVATE
        except Exception:
            pass
        return super().nativeEvent(event_type, message)

    def _on_monitor_tick(self):
        try:
            fg = win32gui.GetForegroundWindow()
            if fg and fg != int(self.winId()):
                self.target_mgr.update_active_window(fg)
                if not self._search_interactive and self.config.get("settings", {}).get("auto_profile_switch", True):
                    info = self.target_mgr.get_target_info()
                    if self.layout_mgr.check_and_apply_profile(
                        info.get("process_name", ""), info.get("title", "")
                    ):
                        self.update_layout_combo_selection()
        except Exception:
            pass
        self.update_target_pill()

    def update_target_pill(self):
        info = self.target_mgr.get_target_info()
        proc = info.get("process_name") or info.get("title") or "未检测"
        if len(proc) > 16:
            proc = proc[:15] + "…"
        locked = info.get("is_locked", False)
        self.target_lock_btn.setText(("🔒 " if locked else "🎯 ") + proc)
        self.target_lock_btn.setToolTip(
            f"目标：{info.get('title', '')} ({info.get('process_name', '')})\n"
            f"状态：{'已锁定' if locked else '自动跟随'}\n点击切换锁定状态"
        )

    def init_ui(self):
        self.main_container = QtWidgets.QFrame(self)
        self.main_container.setObjectName("MainContainer")
        self.main_container.setStyleSheet("""
            QFrame#MainContainer {
                background-color: #181820;
                border: 1px solid #363644;
                border-radius: 8px;
            }
            QLabel {
                color: #ECECF0;
                font-family: "Segoe UI", "Microsoft YaHei", sans-serif;
            }
        """)

        # Drop shadow effect matching floating_keyboard
        shadow = QtWidgets.QGraphicsDropShadowEffect(self)
        shadow.setBlurRadius(8)
        shadow.setColor(QtGui.QColor(0, 0, 0, 160))
        shadow.setOffset(0, 2)
        self.main_container.setGraphicsEffect(shadow)

        self.container_layout = QtWidgets.QVBoxLayout(self.main_container)
        self.container_layout.setContentsMargins(5, 3, 5, 3)
        self.container_layout.setSpacing(2)

        # 1. Header (Search, layout selector, orientation, auto-enter, settings, collapse, close)
        self.init_header(self.container_layout)

        # 2. Button Grid Area
        self.button_grid_widget = QtWidgets.QWidget(self)
        self.button_grid_layout = QtWidgets.QGridLayout(self.button_grid_widget)
        self.button_grid_layout.setContentsMargins(0, 1, 0, 1)
        self.button_grid_layout.setSpacing(2)
        self.container_layout.addWidget(self.button_grid_widget)

        # 3. Footer (Status, opacity slider, target lock pill)
        self.init_footer(self.container_layout)

        root = QtWidgets.QVBoxLayout(self)
        root.setContentsMargins(3, 3, 3, 3)
        root.addWidget(self.main_container)
        self.setLayout(root)
        self.rebuild_buttons()

    def init_header(self, parent_layout):
        self.header_widget = QtWidgets.QWidget(self)
        layout = QtWidgets.QHBoxLayout(self.header_widget)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(3)

        # 1. Search toggle button
        self.search_toggle_btn = QtWidgets.QPushButton("🔍", self.header_widget)
        self.search_toggle_btn.setToolTip("搜索按钮 (点击展开/退出搜索)")
        self.search_toggle_btn.setFixedSize(26, 24)
        self.search_toggle_btn.setFocusPolicy(QtCore.Qt.NoFocus)
        self.search_toggle_btn.setStyleSheet(self.get_tool_btn_style())
        self.search_toggle_btn.clicked.connect(self.toggle_search_box)
        layout.addWidget(self.search_toggle_btn)

        # Inline search input
        self.search_input = QtWidgets.QLineEdit(self.header_widget)
        self.search_input.setFixedHeight(24)
        self.search_input.setPlaceholderText("全局搜索所有布局按钮… (Esc 退出)")
        self.search_input.setClearButtonEnabled(True)
        self.search_input.setStyleSheet("""
            QLineEdit {
                background-color: #20202A;
                color: #ECECF0;
                border: 1px solid #3F3F52;
                padding: 2px 8px;
                border-radius: 4px;
                font-family: "Segoe UI", "Microsoft YaHei", sans-serif;
                font-size: 10px;
            }
            QLineEdit:focus {
                border: 1px solid #5C6BC0;
                background-color: #272736;
            }
        """)
        self.search_input.textChanged.connect(self.filter_buttons)
        self.search_input.installEventFilter(self)
        self.search_input.hide()
        layout.addWidget(self.search_input, 1)

        # Layout selector dropdown
        self.layout_combo = QtWidgets.QComboBox(self.header_widget)
        self.layout_combo.setFixedHeight(24)
        self.layout_combo.setFocusPolicy(QtCore.Qt.NoFocus)
        self.layout_combo.setStyleSheet("""
            QComboBox {
                background-color: #272734;
                color: #ECECF0;
                border: 1px solid #3F3F52;
                padding: 2px 6px;
                border-radius: 4px;
                font-family: "Segoe UI", "Microsoft YaHei", sans-serif;
                font-size: 10px;
                font-weight: 500;
            }
            QComboBox:hover {
                background-color: #38384A;
                color: #FFFFFF;
                border-color: #5C6BC0;
            }
            QComboBox::drop-down {
                subcontrol-origin: padding;
                subcontrol-position: center right;
                width: 14px;
                border-left-width: 0px;
            }
            QComboBox::down-arrow {
                image: none;
                border-left: 3px solid transparent;
                border-right: 3px solid transparent;
                border-top: 4px solid #8E8EA0;
                margin-right: 3px;
            }
            QComboBox QAbstractItemView {
                background-color: #20202C;
                color: #ECECF0;
                border: 1px solid #3F3F52;
                border-radius: 4px;
                padding: 4px;
                selection-background-color: #5C6BC0;
                selection-color: #FFFFFF;
                outline: none;
                font-size: 10px;
            }
        """)
        self.refresh_layout_combo()
        self.layout_combo.currentIndexChanged.connect(self._on_layout_combo_selected)
        layout.addWidget(self.layout_combo, 1)

        # Quick layout orientation toggle button (⇄)
        self.layout_toggle_btn = QtWidgets.QPushButton("⇄竖", self.header_widget)
        self.layout_toggle_btn.setToolTip("快捷切换 横排 / 竖排 象棋布局")
        self.layout_toggle_btn.setFixedSize(26, 24)
        self.layout_toggle_btn.setFocusPolicy(QtCore.Qt.NoFocus)
        self.layout_toggle_btn.setStyleSheet(self.get_tool_btn_style())
        self.layout_toggle_btn.clicked.connect(self.toggle_layout_orientation)
        layout.addWidget(self.layout_toggle_btn)

        # Auto enter checkbox
        self.auto_enter_cb = QtWidgets.QCheckBox("⏎回车", self.header_widget)
        self.auto_enter_cb.setToolTip("开启后，点击按钮输入字符后自动发送回车键 (Enter)")
        self.auto_enter_cb.setFocusPolicy(QtCore.Qt.NoFocus)
        self.auto_enter_cb.setFixedHeight(24)
        self.auto_enter_cb.setStyleSheet("""
            QCheckBox {
                color: #A0A0B2;
                font-family: "Segoe UI", "Microsoft YaHei", sans-serif;
                font-size: 9px;
            }
            QCheckBox::indicator {
                width: 10px;
                height: 10px;
                border-radius: 2px;
                border: 1px solid #555566;
                background: #252530;
            }
            QCheckBox::indicator:checked {
                background: #43A047;
                border: 1px solid #66BB6A;
            }
        """)
        active_lay = self.layout_mgr.get_active_layout()
        self.auto_enter_cb.setChecked(bool(active_lay.settings.auto_enter_default) if active_lay else False)
        self.auto_enter_cb.stateChanged.connect(self.on_auto_enter_changed)
        layout.addWidget(self.auto_enter_cb)

        # Settings button
        self.settings_btn = QtWidgets.QPushButton("⚙", self.header_widget)
        self.settings_btn.setToolTip("设置与布局中心")
        self.settings_btn.setFixedSize(26, 24)
        self.settings_btn.setFocusPolicy(QtCore.Qt.NoFocus)
        self.settings_btn.setStyleSheet(self.get_tool_btn_style())
        self.settings_btn.clicked.connect(self.open_settings)
        layout.addWidget(self.settings_btn)

        # Collapse / expand button
        self.collapse_btn = QtWidgets.QPushButton("一", self.header_widget)
        self.collapse_btn.setToolTip("折叠/展开键盘")
        self.collapse_btn.setFocusPolicy(QtCore.Qt.NoFocus)
        self.collapse_btn.setFixedSize(18, 24)
        self.collapse_btn.setStyleSheet(self.get_tool_btn_style())
        self.collapse_btn.clicked.connect(self.toggle_collapse)
        layout.addWidget(self.collapse_btn)

        # Close button (hide to tray)
        self.close_btn = QtWidgets.QPushButton("✕", self.header_widget)
        self.close_btn.setToolTip("隐藏到系统托盘")
        self.close_btn.setFixedSize(18, 24)
        self.close_btn.setFocusPolicy(QtCore.Qt.NoFocus)
        self.close_btn.setStyleSheet("""
            QPushButton {
                background-color: transparent;
                color: #8E8EA0;
                font-family: "Microsoft YaHei", sans-serif;
                font-size: 9px;
                border-radius: 3px;
                border: none;
            }
            QPushButton:hover {
                background-color: #E53935;
                color: #FFFFFF;
            }
        """)
        self.close_btn.clicked.connect(self.hide_to_tray)
        layout.addWidget(self.close_btn)

        parent_layout.addWidget(self.header_widget)

    def init_footer(self, parent_layout):
        self.footer_widget = QtWidgets.QWidget(self)
        layout = QtWidgets.QHBoxLayout(self.footer_widget)
        layout.setContentsMargins(0, 1, 0, 0)
        layout.setSpacing(4)

        # Status text (turns green when keys injected: "已输入: 兵→rb")
        self.status_label = QtWidgets.QLabel("就绪", self.footer_widget)
        self.status_label.setStyleSheet("""
            QLabel {
                color: #7E7E94;
                font-family: "Segoe UI", "Microsoft YaHei", sans-serif;
                font-size: 9px;
            }
        """)
        layout.addWidget(self.status_label)

        # Temporary stop button shown only during macro execution
        self.stop_exec_btn = QtWidgets.QPushButton("⏹ 停止", self.footer_widget)
        self.stop_exec_btn.setFocusPolicy(QtCore.Qt.NoFocus)
        self.stop_exec_btn.setStyleSheet("""
            QPushButton {
                background-color: #FF453A;
                color: #FFFFFF;
                border: none;
                border-radius: 3px;
                padding: 1px 6px;
                font-weight: 600;
                font-size: 9px;
            }
            QPushButton:hover {
                background-color: #D70015;
            }
        """)
        self.stop_exec_btn.clicked.connect(self.executor.cancel_current)
        self.stop_exec_btn.hide()
        layout.addWidget(self.stop_exec_btn)

        layout.addStretch()

        # Opacity slider
        self.opacity_label = QtWidgets.QLabel("透:", self.footer_widget)
        self.opacity_label.setStyleSheet("color: #7E7E94; font-size: 8px;")
        layout.addWidget(self.opacity_label)

        self.opacity_slider = QtWidgets.QSlider(QtCore.Qt.Horizontal, self.footer_widget)
        self.opacity_slider.setRange(30, 100)
        self.opacity_slider.setFixedWidth(38)
        self.opacity_slider.setFocusPolicy(QtCore.Qt.NoFocus)
        self.opacity_slider.setStyleSheet("""
            QSlider::groove:horizontal {
                height: 2px;
                background: #383848;
                border-radius: 1px;
            }
            QSlider::sub-page:horizontal {
                background: #5C6BC0;
                border-radius: 1px;
            }
            QSlider::handle:horizontal {
                background: #D0D0FF;
                width: 6px;
                margin-top: -3px;
                margin-bottom: -3px;
                border-radius: 3px;
            }
            QSlider::handle:horizontal:hover {
                background: #FFFFFF;
            }
        """)
        layout_obj = self.layout_mgr.get_active_layout()
        curr_op = int((layout_obj.settings.opacity if layout_obj else 0.95) * 100)
        self.opacity_slider.setValue(curr_op)
        self.opacity_slider.setToolTip(f"透明度: {curr_op}%")
        self.opacity_slider.valueChanged.connect(self._on_opacity_slider_changed)
        self.opacity_slider.sliderReleased.connect(self.save_window_config)
        layout.addWidget(self.opacity_slider)

        # Target window pill and lock toggle
        self.target_lock_btn = QtWidgets.QPushButton("🎯 未检测", self.footer_widget)
        self.target_lock_btn.setFocusPolicy(QtCore.Qt.NoFocus)
        self.target_lock_btn.setFixedHeight(18)
        self.target_lock_btn.setStyleSheet("""
            QPushButton {
                background-color: #272734;
                color: #8E8EA0;
                border: 1px solid #3F3F52;
                border-radius: 8px;
                padding: 1px 6px;
                font-family: "Segoe UI", "Microsoft YaHei", sans-serif;
                font-size: 8.5px;
            }
            QPushButton:hover {
                background-color: #38384A;
                color: #ECECF0;
                border: 1px solid #5C6BC0;
            }
        """)
        self.target_lock_btn.clicked.connect(self.target_mgr.toggle_lock)
        layout.addWidget(self.target_lock_btn)

        parent_layout.addWidget(self.footer_widget)

    @staticmethod
    def get_tool_btn_style():
        return """
            QPushButton {
                background-color: #272734;
                color: #B0B0C0;
                font-family: "Segoe UI", "Microsoft YaHei", sans-serif;
                font-size: 10px;
                border: 1px solid #3F3F52;
                border-radius: 4px;
                padding: 0px;
            }
            QPushButton:hover {
                background-color: #38384A;
                color: #FFFFFF;
                border: 1px solid #5C6BC0;
            }
            QPushButton:pressed {
                background-color: #1E1E28;
            }
        """

    def _on_opacity_slider_changed(self, val):
        opacity = max(0.3, min(1.0, val / 100.0))
        self.setWindowOpacity(opacity)
        self.opacity_slider.setToolTip(f"透明度: {val}%")
        layout = self.layout_mgr.get_active_layout()
        if layout:
            layout.settings.opacity = opacity

    def refresh_layout_combo(self):
        self.layout_combo.blockSignals(True)
        self.layout_combo.clear()
        for lid, lay in self.layout_mgr.layouts.items():
            name = lay.name
            if lid == "chess":
                name = "♟ 象棋"
            elif lid == "chess_vertical":
                name = "♟ 象棋 (竖)"
            self.layout_combo.addItem(name, lid)
        self.update_layout_combo_selection()
        self.layout_combo.blockSignals(False)

    def update_layout_combo_selection(self):
        idx = self.layout_combo.findData(self.layout_mgr.active_layout_id)
        if idx >= 0:
            self.layout_combo.blockSignals(True)
            self.layout_combo.setCurrentIndex(idx)
            self.layout_combo.blockSignals(False)

    def _on_layout_combo_selected(self, index):
        lid = self.layout_combo.itemData(index)
        if lid and lid != self.layout_mgr.active_layout_id:
            curr_lay = self.layout_mgr.get_active_layout()
            if curr_lay and not self._auto_sizing:
                curr_lay.settings.window_width = self.width()
                curr_lay.settings.window_height = self.height()
            self.layout_mgr.set_active_layout(lid)
            self.save_window_config()

    def on_layout_changed_event(self, layout: Layout):
        if hasattr(self, "_current_layout_id") and self._current_layout_id and self._current_layout_id != layout.id:
            old_lay = self.layout_mgr.layouts.get(self._current_layout_id)
            if old_lay and not self._auto_sizing:
                old_lay.settings.window_width = self.width()
                old_lay.settings.window_height = self.height()
        self._current_layout_id = layout.id

        self.update_layout_combo_selection()

        # Update layout orientation & auto_enter labels matching floating_keyboard
        if hasattr(self, "layout_toggle_btn"):
            if layout.id == "chess" or (layout.columns == 7 and layout.rows == 2):
                self.layout_toggle_btn.setText("⇄竖")
                self.layout_toggle_btn.setToolTip("快捷切换至竖排(2x7)布局")
                if hasattr(self, "auto_enter_cb"):
                    self.auto_enter_cb.setText("⏎回车")
                if hasattr(self, "opacity_label"):
                    self.opacity_label.show()
                    self.opacity_slider.show()
            elif layout.id == "chess_vertical" or (layout.columns == 2 and layout.rows == 7):
                self.layout_toggle_btn.setText("⇄横")
                self.layout_toggle_btn.setToolTip("快捷切换至横排(7x2)布局")
                if hasattr(self, "auto_enter_cb"):
                    self.auto_enter_cb.setText("⏎")
                if hasattr(self, "opacity_label"):
                    self.opacity_label.hide()
                    self.opacity_slider.hide()
            else:
                self.layout_toggle_btn.setText("⇄")
                self.layout_toggle_btn.setToolTip("切换布局")
                if hasattr(self, "auto_enter_cb"):
                    self.auto_enter_cb.setText("⏎回车")
                if hasattr(self, "opacity_label"):
                    self.opacity_label.show()
                    self.opacity_slider.show()

        op_val = int(float(layout.settings.opacity) * 100)
        self.opacity_slider.blockSignals(True)
        self.opacity_slider.setValue(op_val)
        self.opacity_slider.setToolTip(f"透明度: {op_val}%")
        self.opacity_slider.blockSignals(False)
        if hasattr(self, "auto_enter_cb"):
            self.auto_enter_cb.blockSignals(True)
            self.auto_enter_cb.setChecked(bool(layout.settings.auto_enter_default))
            self.auto_enter_cb.blockSignals(False)
        self.setWindowOpacity(float(layout.settings.opacity))
        self._apply_topmost_setting()
        self.rebuild_buttons()
        self.save_window_config()

    def rebuild_buttons(self):
        for widget in self.buttons_widgets:
            widget.setParent(None)
            widget.deleteLater()
        self.buttons_widgets.clear()
        if self.button_grid_layout is not None:
            sip.delete(self.button_grid_layout)
        self.button_grid_layout = QtWidgets.QGridLayout(self.button_grid_widget)
        self.button_grid_layout.setContentsMargins(0, 1, 0, 1)
        self.button_grid_layout.setSpacing(2)

        layout = self.layout_mgr.get_active_layout()
        if not layout:
            return
        self.setWindowOpacity(float(layout.settings.opacity))
        for slot in layout.buttons:
            model = self.layout_mgr.get_button(slot.button_id)
            if not model:
                continue
            widget = ActionButtonWidget(model, self.button_grid_widget)
            widget.clicked.connect(
                lambda checked=False, bm=model, bw=widget: self.on_action_button_clicked(bm, bw)
            )
            self.button_grid_layout.addWidget(widget, slot.row, slot.column)
            self.buttons_widgets.append(widget)

        self._auto_sizing = True
        base_scale = {"compact": 1.0, "standard": 1.25, "touch": 1.5}.get(layout.settings.button_size, 1.0)
        bw = int(40 * base_scale)
        bh = int(30 * base_scale)
        calc_w = max(220, layout.columns * (bw + 2) + 24)
        calc_h = max(60, layout.rows * (bh + 2) + 72)

        sw = layout.settings.window_width
        sh = layout.settings.window_height
        # Sanitize bloated dimensions (e.g. 1280x667 from earlier builds)
        if sw and sh and sw < 900:
            w = max(220, int(sw))
            h = max(60, int(sh))
        else:
            w, h = calc_w, calc_h
            layout.settings.window_width = w
            layout.settings.window_height = h
        self.resize(w, h)
        self._auto_sizing = False
        self._apply_button_scale()

    def _apply_button_scale(self):
        layout = self.layout_mgr.get_active_layout()
        if not layout or not self.buttons_widgets:
            return
        base_scale = {"compact": 1.0, "standard": 1.25, "touch": 1.5}.get(layout.settings.button_size, 1.0)
        scale_x = (self.width() - 24) / max(1, layout.columns * 42)
        scale_y = (self.height() - 72) / max(1, layout.rows * 32)
        scale = max(0.8, min(2.0, min(scale_x, scale_y) * base_scale if scale_y > 0 else scale_x * base_scale))
        for widget in self.buttons_widgets:
            widget.apply_scale(scale)

    def resize(self, *args):
        super().resize(*args)
        if hasattr(self, "_auto_sizing") and not self._auto_sizing:
            layout = self.layout_mgr.get_active_layout()
            if layout:
                layout.settings.window_width = self.width()
                layout.settings.window_height = self.height()
            self._apply_button_scale()

    def resizeEvent(self, event):
        super().resizeEvent(event)
        if not self._auto_sizing:
            layout = self.layout_mgr.get_active_layout()
            if layout:
                layout.settings.window_width = self.width()
                layout.settings.window_height = self.height()
            self._apply_button_scale()

    def on_action_button_clicked(self, btn_model, btn_widget):
        if self.executor.is_running:
            return
        layout = self.layout_mgr.get_active_layout()
        if not layout:
            return
        btn_widget.flash_feedback()
        action = self.layout_mgr.get_action_for_button(btn_model.id)
        if not action:
            return

        # Visual feedback in status_label matching floating_keyboard
        clean_text = btn_model.label.replace("\n", "→")
        auto_enter = self.auto_enter_cb.isChecked() if hasattr(self, "auto_enter_cb") else bool(layout.settings.auto_enter_default)
        if hasattr(self, "status_label"):
            self.status_label.setText(f"已输入: {clean_text}" + ("+⏎" if auto_enter else ""))
            self.status_label.setStyleSheet("color: #81C784; font-family: 'Segoe UI', 'Microsoft YaHei', sans-serif; font-size: 9px; font-weight: bold;")
            QtCore.QTimer.singleShot(1500, self._reset_status)

        # Layout-level confirmation
        if layout.settings.confirm_before_action:
            result = QtWidgets.QMessageBox.question(
                self,
                "确认执行",
                f"确定执行“{btn_model.label}”吗？",
                QtWidgets.QMessageBox.Yes | QtWidgets.QMessageBox.No,
            )
            if result != QtWidgets.QMessageBox.Yes:
                return

        self.executor.execute_async(action, auto_enter_override=auto_enter)

    def _reset_status(self):
        if hasattr(self, "status_label"):
            self.status_label.setText("就绪")
            self.status_label.setStyleSheet("color: #7E7E94; font-family: 'Segoe UI', 'Microsoft YaHei', sans-serif; font-size: 9px;")

    def toggle_collapse(self):
        self._is_collapsed = not getattr(self, "_is_collapsed", False)
        if self._is_collapsed:
            self.button_grid_widget.hide()
            self.footer_widget.hide()
            self.collapse_btn.setText("十")
            self.collapse_btn.setToolTip("展开键盘")
        else:
            self.button_grid_widget.show()
            self.footer_widget.show()
            self.collapse_btn.setText("一")
            self.collapse_btn.setToolTip("折叠键盘")
        self.adjustSize()

    def toggle_layout_orientation(self):
        curr_id = self.layout_mgr.active_layout_id
        if curr_id == "chess":
            if "chess_vertical" in self.layout_mgr.layouts:
                self.layout_mgr.set_active_layout("chess_vertical")
                return
        elif curr_id == "chess_vertical":
            if "chess" in self.layout_mgr.layouts:
                self.layout_mgr.set_active_layout("chess")
                return
        # Fallback: cycle layouts
        lids = list(self.layout_mgr.layouts.keys())
        if lids:
            idx = lids.index(curr_id) if curr_id in lids else 0
            next_lid = lids[(idx + 1) % len(lids)]
            self.layout_mgr.set_active_layout(next_lid)

    def on_auto_enter_changed(self, state):
        layout = self.layout_mgr.get_active_layout()
        if layout:
            layout.settings.auto_enter_default = (state == QtCore.Qt.Checked)
            self.save_window_config()

    def _on_exec_started(self, action_id, total_steps):
        self.stop_exec_btn.setText(f"⏹ 停止 ({total_steps})")
        self.stop_exec_btn.show()
        if self.hotkey_mgr:
            self.hotkey_mgr.register_named_hotkey(
                "emergency_stop",
                self.config.get("hotkeys", {}).get("emergency_stop", "ESC"),
                self.executor.cancel_current,
            )

    def _on_exec_step(self, step_idx, total_steps, desc):
        self.stop_exec_btn.setText(f"⏹ 停止 ({step_idx}/{total_steps})")

    def _on_exec_finished(self, action_id, success, message):
        if self.hotkey_mgr:
            self.hotkey_mgr.unregister_named_hotkey("emergency_stop")
        # Hide stop button; no persistent "执行完成" text
        self.stop_exec_btn.hide()

    def _set_search_interactive(self, enabled: bool):
        self._search_interactive = enabled
        try:
            hwnd = int(self.winId())
            ex = win32gui.GetWindowLong(hwnd, win32con.GWL_EXSTYLE)
            if enabled:
                ex &= ~WS_EX_NOACTIVATE
            else:
                ex |= WS_EX_NOACTIVATE
            win32gui.SetWindowLong(hwnd, win32con.GWL_EXSTYLE, ex)
        except Exception:
            pass

    def toggle_search_box(self):
        if self._search_interactive or self.search_input.isVisible():
            self.exit_search()
        else:
            self.enter_search()

    def enter_search(self):
        self._search_interactive = True
        self.layout_combo.hide()
        self.search_input.show()
        self.search_input.clear()
        self._set_search_interactive(True)
        self.show()
        self.raise_()
        self.activateWindow()
        self.search_input.setFocus(QtCore.Qt.OtherFocusReason)

    def exit_search(self, rebuild: bool = True):
        self._search_interactive = False
        self.search_input.blockSignals(True)
        self.search_input.clear()
        self.search_input.blockSignals(False)
        self.search_input.hide()
        self.layout_combo.show()
        self._set_search_interactive(False)
        self.clearFocus()
        if rebuild:
            self.rebuild_buttons()
        # Restore focus to external target app so typing is immediately directed there
        eff_hwnd = self.target_mgr.get_effective_hwnd()
        if eff_hwnd and self.target_mgr.window_manager.is_window_valid(eff_hwnd):
            self.target_mgr.window_manager.set_foreground_safe(eff_hwnd)

    def filter_buttons(self, text):
        query = (text or "").strip().lower()
        if not query:
            self.rebuild_buttons()
            return

        for widget in self.buttons_widgets:
            widget.setParent(None)
            widget.deleteLater()
        self.buttons_widgets.clear()

        if self.button_grid_layout is not None:
            sip.delete(self.button_grid_layout)
        self.button_grid_layout = QtWidgets.QGridLayout(self.button_grid_widget)
        self.button_grid_layout.setContentsMargins(0, 1, 0, 1)
        self.button_grid_layout.setSpacing(3)

        matched_results = []
        seen_keys = set()
        for lid, layout in self.layout_mgr.layouts.items():
            for slot in layout.buttons:
                bm = self.layout_mgr.get_button(slot.button_id)
                if not bm:
                    continue
                action = self.layout_mgr.actions.get(bm.action_id)
                action_text = ""
                if action:
                    action_text = f"{action.label} {action.description} " + " ".join(
                        f"{s.value} {s.key} {s.hotkey} {s.name}" for s in action.steps
                    )
                haystack = f"{bm.label} {bm.tooltip} {bm.id} {bm.action_id} {action_text}".lower()
                if query in haystack:
                    key = (lid, bm.id)
                    if key not in seen_keys:
                        seen_keys.add(key)
                        matched_results.append((lid, layout.name, bm))

        curr_layout = self.layout_mgr.get_active_layout()
        cols = max(1, curr_layout.columns if curr_layout else 4)
        for idx, (lid, lname, bm) in enumerate(matched_results):
            r = idx // cols
            c = idx % cols
            widget = ActionButtonWidget(bm, self.button_grid_widget)
            widget.setToolTip(f"所属布局：【{lname}】\n点击切换至此布局并定位按钮")
            widget.clicked.connect(
                lambda checked=False, target_lid=lid, target_bid=bm.id: self._on_search_result_clicked(target_lid, target_bid)
            )
            self.button_grid_layout.addWidget(widget, r, c)
            self.buttons_widgets.append(widget)

        self._apply_button_scale()

    def _on_search_result_clicked(self, target_lid: str, target_bid: str):
        self.exit_search(rebuild=False)
        if target_lid != self.layout_mgr.active_layout_id:
            self.layout_mgr.set_active_layout(target_lid)
        else:
            self.rebuild_buttons()
        self._highlight_button(target_bid)

    def _highlight_button(self, target_bid: str):
        for widget in self.buttons_widgets:
            if widget.button_model.id == target_bid:
                orig_style = widget.styleSheet()
                flash_style = orig_style + "QPushButton { border: 2.5px solid #00E676; background-color: rgba(0, 230, 118, 0.45); }"
                # Double-pulse flash feedback
                widget.setStyleSheet(flash_style)
                QtCore.QTimer.singleShot(200, lambda w=widget, s=orig_style: w.setStyleSheet(s))
                QtCore.QTimer.singleShot(350, lambda w=widget, s=flash_style: w.setStyleSheet(s))
                QtCore.QTimer.singleShot(550, lambda w=widget, s=orig_style: w.setStyleSheet(s))
                break

    def open_settings(self):
        if hasattr(self, "_settings_dialog") and self._settings_dialog and self._settings_dialog.isVisible():
            self._settings_dialog.raise_()
            self._settings_dialog.activateWindow()
            return

        if self._search_interactive:
            self.exit_search(rebuild=False)

        self.save_window_config()
        self._remove_topmost_temporarily()

        self._settings_dialog = SettingsDialog(
            self.layout_mgr, self.executor, self.target_mgr, self.config_store, parent=None
        )
        self._settings_dialog.setWindowModality(QtCore.Qt.NonModal)
        self._settings_dialog.finished.connect(self._on_settings_closed)
        self._settings_dialog.show()
        self._settings_dialog.raise_()
        self._settings_dialog.activateWindow()

    def _remove_topmost_temporarily(self):
        try:
            hwnd = int(self.winId())
            ex = win32gui.GetWindowLong(hwnd, win32con.GWL_EXSTYLE)
            ex &= ~win32con.WS_EX_TOPMOST
            win32gui.SetWindowLong(hwnd, win32con.GWL_EXSTYLE, ex)
            win32gui.SetWindowPos(
                hwnd,
                win32con.HWND_NOTOPMOST,
                0, 0, 0, 0,
                win32con.SWP_NOMOVE | win32con.SWP_NOSIZE | win32con.SWP_NOACTIVATE,
            )
        except Exception:
            pass

    def _on_settings_closed(self, result):
        if hasattr(self, "_settings_dialog"):
            self._settings_dialog = None
        self._apply_topmost_setting()
        self.config = self.config_store.load_config()
        self.refresh_layout_combo()
        self.rebuild_buttons()
        self.apply_config(restore_pos=False)

    def hide_to_tray(self):
        """Hide the panel while keeping the process and tray menu alive."""
        self.save_window_config()
        self.hide()

    def request_quit(self):
        """Exit from the panel itself."""
        self._allow_close = True
        self.save_window_config()
        app = QtWidgets.QApplication.instance()
        if app:
            app.quit()

    def apply_config(self, restore_pos: bool = True):
        window = self.config.get("window", {})
        if restore_pos:
            self.move(window.get("x", 350), window.get("y", 250))
        layout = self.layout_mgr.get_active_layout()
        if layout:
            base_scale = {"compact": 1.0, "standard": 1.25, "touch": 1.5}.get(layout.settings.button_size, 1.0)
            bw = int(40 * base_scale)
            bh = int(30 * base_scale)
            calc_w = max(220, layout.columns * (bw + 2) + 24)
            calc_h = max(60, layout.rows * (bh + 2) + 72)
            sw = layout.settings.window_width
            sh = layout.settings.window_height
            if sw and sh and sw < 900:
                self.resize(max(220, int(sw)), max(60, int(sh)))
            else:
                self.resize(calc_w, calc_h)
                layout.settings.window_width = calc_w
                layout.settings.window_height = calc_h
        op = float(layout.settings.opacity) if layout else float(window.get("opacity", 0.95))
        self.setWindowOpacity(op)
        if hasattr(self, "opacity_slider"):
            op_val = int(op * 100)
            self.opacity_slider.blockSignals(True)
            self.opacity_slider.setValue(op_val)
            self.opacity_slider.setToolTip(f"透明度: {op_val}%")
            self.opacity_slider.blockSignals(False)
        if hasattr(self, "auto_enter_cb") and layout:
            self.auto_enter_cb.blockSignals(True)
            self.auto_enter_cb.setChecked(bool(layout.settings.auto_enter_default))
            self.auto_enter_cb.blockSignals(False)
        self._apply_topmost_setting()

    def _apply_topmost_setting(self):
        """Apply the selected layout's topmost preference without activation."""
        if hasattr(self, "_settings_dialog") and self._settings_dialog and self._settings_dialog.isVisible():
            return
        try:
            hwnd = int(self.winId())
            layout = self.layout_mgr.get_active_layout()
            keep_top = bool(layout.settings.always_on_top) if layout else True
            ex = win32gui.GetWindowLong(hwnd, win32con.GWL_EXSTYLE)
            ex = (ex | win32con.WS_EX_TOPMOST) if keep_top else (ex & ~win32con.WS_EX_TOPMOST)
            win32gui.SetWindowLong(hwnd, win32con.GWL_EXSTYLE, ex)
            win32gui.SetWindowPos(
                hwnd,
                win32con.HWND_TOPMOST if keep_top else win32con.HWND_NOTOPMOST,
                0, 0, 0, 0,
                win32con.SWP_NOMOVE | win32con.SWP_NOSIZE | win32con.SWP_NOACTIVATE,
            )
        except Exception:
            pass

    def save_window_config(self):
        layout = self.layout_mgr.get_active_layout()
        if layout and not self._auto_sizing:
            layout.settings.window_width = self.width()
            layout.settings.window_height = self.height()
        window = self.config.setdefault("window", {})
        window.update({
            "x": self.x(),
            "y": self.y(),
            "width": self.width(),
            "height": self.height(),
            "opacity": self.windowOpacity(),
        })
        self.config["active_layout_id"] = self.layout_mgr.active_layout_id
        # Persist layouts, buttons, actions, and profiles to ensure full sync
        self.config["layouts"] = {lid: lay.to_dict() for lid, lay in self.layout_mgr.layouts.items()}
        self.config["buttons"] = {bid: b.to_dict() for bid, b in self.layout_mgr.buttons.items()}
        self.config["actions"] = {aid: a.to_dict() for aid, a in self.layout_mgr.actions.items()}
        self.config["profiles"] = [p.to_dict() for p in self.layout_mgr.profiles]
        self.config_store.save_config(self.config)

    def eventFilter(self, watched, event):
        if watched is self.search_input and event.type() == QtCore.QEvent.KeyPress:
            if event.key() == QtCore.Qt.Key_Escape:
                self.exit_search()
                return True
            elif event.key() in (QtCore.Qt.Key_Return, QtCore.Qt.Key_Enter):
                if self.buttons_widgets:
                    self.buttons_widgets[0].click()
                    return True
        return super().eventFilter(watched, event)

    def mousePressEvent(self, event):
        if event.button() == QtCore.Qt.LeftButton and not self._search_interactive:
            self._drag_pos = event.globalPos() - self.frameGeometry().topLeft()
            event.accept()
            return
        super().mousePressEvent(event)

    def mouseMoveEvent(self, event):
        if self._drag_pos and event.buttons() & QtCore.Qt.LeftButton:
            pos = event.globalPos() - self._drag_pos
            screen = QtGui.QGuiApplication.screenAt(event.globalPos()) or QtGui.QGuiApplication.primaryScreen()
            if screen:
                area = screen.availableGeometry()
                snap = 18
                if abs(pos.x() - area.left()) <= snap:
                    pos.setX(area.left())
                if abs(pos.y() - area.top()) <= snap:
                    pos.setY(area.top())
                if abs(pos.x() + self.width() - area.right() - 1) <= snap:
                    pos.setX(area.right() - self.width() + 1)
                if abs(pos.y() + self.height() - area.bottom() - 1) <= snap:
                    pos.setY(area.bottom() - self.height() + 1)
            self.move(pos)
            event.accept()
            return
        super().mouseMoveEvent(event)

    def mouseReleaseEvent(self, event):
        if self._drag_pos:
            self._drag_pos = None
            self.save_window_config()
        super().mouseReleaseEvent(event)

    def keyPressEvent(self, event):
        if event.key() == QtCore.Qt.Key_Escape and self.executor.is_running:
            self.executor.cancel_current()
            event.accept()
            return
        super().keyPressEvent(event)

    def closeEvent(self, event):
        self.save_window_config()
        if self._allow_close:
            event.accept()
        else:
            # Native close hides to system tray; quit is done via tray context menu
            event.ignore()
            self.hide()
