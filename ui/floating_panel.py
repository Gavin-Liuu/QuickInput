# -*- coding: utf-8 -*-
"""Floating action panel with zero-focus normal operation, native frame, and editable search."""

from ctypes import wintypes
import ctypes
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


def set_window_dark_titlebar(hwnd: int):
    """Enable Windows 10/11 native immersive dark title bar."""
    try:
        val = ctypes.c_int(1)
        # DWMWA_USE_IMMERSIVE_DARK_MODE: 20 (Win11 / Win10 build 18985+), 19 (Win10 build 17763-18363)
        hr = ctypes.windll.dwmapi.DwmSetWindowAttribute(hwnd, 20, ctypes.byref(val), ctypes.sizeof(val))
        if hr != 0:
            ctypes.windll.dwmapi.DwmSetWindowAttribute(hwnd, 19, ctypes.byref(val), ctypes.sizeof(val))
    except Exception:
        pass


def get_action_button_style(color_hex: str, font_size: int = 9) -> str:
    """Generate high-tactile beveled linear gradient stylesheet with physical depth."""
    c = QtGui.QColor(color_hex or "#0A84FF")
    r, g, b = c.red(), c.green(), c.blue()

    # Red chess pieces & variants (cinnabar / vermilion tactile bevel)
    if r > 160 and g < 100 and b < 100:
        return f"""
            QPushButton {{
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1, stop:0 #E53935, stop:0.08 #D32F2F, stop:0.85 #B71C1C, stop:1 #8E1515);
                color: #FFFFFF;
                font-family: "Segoe UI Variable Text", "Segoe UI", "PingFang SC", "Microsoft YaHei UI", sans-serif;
                font-size: {font_size}px;
                font-weight: 600;
                border: 1px solid #781010;
                border-radius: 4px;
                padding: 1px 2px;
            }}
            QPushButton:hover {{
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1, stop:0 #FF5252, stop:0.10 #E53935, stop:1 #C62828);
                border: 1px solid #FF8A80;
                color: #FFFFFF;
            }}
            QPushButton:pressed {{
                background: #800000;
                border: 1px solid #4D0000;
                padding-top: 2px;
                padding-left: 2px;
            }}
        """
    # Black / Obsidian chess pieces & dark variants (deep graphite tactile bevel)
    elif r < 90 and g < 100 and b < 110 and abs(r - g) < 30 and abs(g - b) < 30:
        return f"""
            QPushButton {{
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1, stop:0 #455A64, stop:0.08 #37474F, stop:0.85 #263238, stop:1 #1C2428);
                color: #ECEFF1;
                font-family: "Segoe UI Variable Text", "Segoe UI", "PingFang SC", "Microsoft YaHei UI", sans-serif;
                font-size: {font_size}px;
                font-weight: 600;
                border: 1px solid #141B1E;
                border-radius: 4px;
                padding: 1px 2px;
            }}
            QPushButton:hover {{
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1, stop:0 #546E7A, stop:0.10 #455A64, stop:1 #2C383F);
                border: 1px solid #78909C;
                color: #FFFFFF;
            }}
            QPushButton:pressed {{
                background: #101416;
                border: 1px solid #000000;
                padding-top: 2px;
                padding-left: 2px;
            }}
        """
    else:
        # Dynamic bevel gradient for arbitrary colors
        top = c.lighter(125).name()
        body_top = c.lighter(105).name()
        body_bot = c.darker(118).name()
        shadow = c.darker(135).name()
        border = c.darker(145).name()
        hover_top = c.lighter(135).name()
        hover_bot = c.lighter(110).name()
        hover_border = c.lighter(130).name()
        pressed_bg = c.darker(135).name()
        pressed_border = c.darker(160).name()
        return f"""
            QPushButton {{
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1, stop:0 {top}, stop:0.08 {body_top}, stop:0.85 {body_bot}, stop:1 {shadow});
                color: #FFFFFF;
                font-family: "Segoe UI Variable Text", "Segoe UI", "PingFang SC", "Microsoft YaHei UI", sans-serif;
                font-size: {font_size}px;
                font-weight: 600;
                border: 1px solid {border};
                border-radius: 4px;
                padding: 1px 2px;
            }}
            QPushButton:hover {{
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1, stop:0 {hover_top}, stop:1 {hover_bot});
                border: 1px solid {hover_border};
                color: #FFFFFF;
            }}
            QPushButton:pressed {{
                background: {pressed_bg};
                border: 1px solid {pressed_border};
                padding-top: 2px;
                padding-left: 2px;
            }}
        """


class ActionButtonWidget(QtWidgets.QPushButton):
    """A button that never accepts keyboard focus during panel operation."""

    def __init__(self, button_model: Button, parent=None):
        super().__init__(parent)
        self.button_model = button_model
        self._base_style = ""
        self.setFocusPolicy(QtCore.Qt.NoFocus)
        self.setCursor(QtGui.QCursor(QtCore.Qt.PointingHandCursor))
        self.setText(button_model.display_text)
        self.setToolTip(button_model.tooltip or button_model.label)
        self.apply_scale(1.0)

    def apply_scale(self, scale: float):
        width, height, font_size = 48, 32, 9
        width = max(32, min(180, int(width * scale)))
        height = max(26, min(100, int(height * scale)))
        font = max(8, min(20, int(font_size * scale)))
        self.setFixedSize(width, height)
        self._base_style = get_action_button_style(self.button_model.color, font)
        self.setStyleSheet(self._base_style)

    def flash_feedback(self):
        self.setStyleSheet(self._base_style + "QPushButton { border: 2px solid #00E676; }")
        QtCore.QTimer.singleShot(150, lambda: self.setStyleSheet(self._base_style))


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
        # Native Windows frame with minimize, maximize, and close behavior.
        # Edge resizing and native hit-testing are managed by Windows.
        flags = (
            QtCore.Qt.Window
            | QtCore.Qt.WindowTitleHint
            | QtCore.Qt.WindowSystemMenuHint
            | QtCore.Qt.WindowMinimizeButtonHint
            | QtCore.Qt.WindowMaximizeButtonHint
            | QtCore.Qt.WindowCloseButtonHint
        )
        self.setWindowFlags(flags)
        self.setAttribute(QtCore.Qt.WA_ShowWithoutActivating, True)
        self.setMinimumSize(220, 60)
        self.setWindowTitle("快捷输入工作台")

    def showEvent(self, event):
        super().showEvent(event)
        try:
            hwnd = int(self.winId())
            set_window_dark_titlebar(hwnd)
            self.target_mgr.register_own_hwnd(hwnd)
            ex_style = win32gui.GetWindowLong(hwnd, win32con.GWL_EXSTYLE)
            active_layout = self.layout_mgr.get_active_layout()
            keep_top = bool(active_layout.settings.always_on_top) if active_layout else True
            ex_style |= WS_EX_NOACTIVATE
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
        if len(proc) > 20:
            proc = proc[:19] + "…"
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
                background-color: #1A1A20;
                border: none;
            }
            QLabel {
                color: #F0F0F5;
                font-family: "Segoe UI Variable Text", "Segoe UI", "PingFang SC", "Microsoft YaHei UI", sans-serif;
            }
        """)

        self.container_layout = QtWidgets.QVBoxLayout(self.main_container)
        self.container_layout.setContentsMargins(7, 5, 7, 5)
        self.container_layout.setSpacing(5)

        # 1. Header (Search button, inline search input, layout selector dropdown, settings)
        self.init_header(self.container_layout)

        # 2. Button Grid Area
        self.button_grid_widget = QtWidgets.QWidget(self)
        self.button_grid_layout = QtWidgets.QGridLayout(self.button_grid_widget)
        self.button_grid_layout.setContentsMargins(0, 1, 0, 1)
        self.button_grid_layout.setSpacing(3)
        self.container_layout.addWidget(self.button_grid_widget)

        # 3. Footer (Opacity slider on left, target window lock on right; no persistent status text)
        self.init_footer(self.container_layout)

        root = QtWidgets.QVBoxLayout(self)
        root.setContentsMargins(0, 0, 0, 0)
        root.addWidget(self.main_container)
        self.setLayout(root)
        self.rebuild_buttons()

    def init_header(self, parent_layout):
        self.header_widget = QtWidgets.QWidget(self)
        layout = QtWidgets.QHBoxLayout(self.header_widget)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(5)

        # First control on left: Search button
        self.search_toggle_btn = QtWidgets.QPushButton("🔍", self.header_widget)
        self.search_toggle_btn.setToolTip("搜索按钮 (点击展开/退出搜索)")
        self.search_toggle_btn.setFixedSize(26, 24)
        self.search_toggle_btn.setFocusPolicy(QtCore.Qt.NoFocus)
        self.search_toggle_btn.setStyleSheet(self.get_tool_btn_style())
        self.search_toggle_btn.clicked.connect(self.toggle_search_box)
        layout.addWidget(self.search_toggle_btn)

        # Inline search input field (expands horizontally inside header, hidden initially)
        self.search_input = QtWidgets.QLineEdit(self.header_widget)
        self.search_input.setFixedHeight(24)
        self.search_input.setPlaceholderText("全局搜索所有布局按钮… (Esc 退出)")
        self.search_input.setClearButtonEnabled(True)
        self.search_input.setStyleSheet("""
            QLineEdit {
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1, stop:0 #141418, stop:1 #1C1C22);
                color: #F0F0F5;
                border: 1px solid #383846;
                padding: 2px 8px;
                border-radius: 5px;
                font-family: "Segoe UI Variable Text", "Segoe UI", "PingFang SC", "Microsoft YaHei UI", sans-serif;
                font-size: 11px;
                selection-background-color: #0A84FF;
            }
            QLineEdit:focus {
                border: 1.5px solid #0A84FF;
                background: #1E1E28;
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
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1, stop:0 #2C2C36, stop:1 #22222A);
                color: #F0F0F5;
                border: 1px solid #3A3A48;
                padding: 2px 10px 2px 8px;
                border-radius: 5px;
                font-family: "Segoe UI Variable Text", "Segoe UI", "PingFang SC", "Microsoft YaHei UI", sans-serif;
                font-size: 11px;
                font-weight: 500;
            }
            QComboBox:hover {
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1, stop:0 #383846, stop:1 #2A2A34);
                border-color: #55556C;
                color: #FFFFFF;
            }
            QComboBox::drop-down {
                subcontrol-origin: padding;
                subcontrol-position: center right;
                width: 18px;
                border-left-width: 0px;
            }
            QComboBox::down-arrow {
                image: none;
                border-left: 4px solid transparent;
                border-right: 4px solid transparent;
                border-top: 5px solid #A0A0B2;
                margin-right: 6px;
            }
            QComboBox::down-arrow:hover {
                border-top: 5px solid #FFFFFF;
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
        """)
        self.refresh_layout_combo()
        self.layout_combo.currentIndexChanged.connect(self._on_layout_combo_selected)
        layout.addWidget(self.layout_combo, 1)

        # Settings button
        self.settings_btn = QtWidgets.QPushButton("⚙️", self.header_widget)
        self.settings_btn.setToolTip("打开设置中心")
        self.settings_btn.setFixedSize(26, 24)
        self.settings_btn.setFocusPolicy(QtCore.Qt.NoFocus)
        self.settings_btn.setStyleSheet(self.get_tool_btn_style())
        self.settings_btn.clicked.connect(self.open_settings)
        layout.addWidget(self.settings_btn)

        parent_layout.addWidget(self.header_widget)

    def init_footer(self, parent_layout):
        self.footer_widget = QtWidgets.QWidget(self)
        layout = QtWidgets.QHBoxLayout(self.footer_widget)
        layout.setContentsMargins(0, 2, 0, 0)
        layout.setSpacing(6)

        # Left: Layout Opacity Slider
        self.opacity_label = QtWidgets.QLabel("透明度", self.footer_widget)
        self.opacity_label.setStyleSheet("color: #9A9AB0; font-family: 'Segoe UI Variable Text', 'Segoe UI', 'Microsoft YaHei UI', sans-serif; font-size: 10px; font-weight: 500;")
        layout.addWidget(self.opacity_label)

        self.opacity_slider = QtWidgets.QSlider(QtCore.Qt.Horizontal, self.footer_widget)
        self.opacity_slider.setRange(30, 100)
        self.opacity_slider.setFixedWidth(80)
        self.opacity_slider.setFocusPolicy(QtCore.Qt.NoFocus)
        self.opacity_slider.setStyleSheet("""
            QSlider::groove:horizontal {
                height: 4px;
                background: #282834;
                border-radius: 2px;
            }
            QSlider::sub-page:horizontal {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:0, stop:0 #0066CC, stop:1 #0A84FF);
                border-radius: 2px;
            }
            QSlider::handle:horizontal {
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1, stop:0 #FFFFFF, stop:1 #D8D8E0);
                border: 1px solid #808092;
                width: 12px;
                height: 12px;
                margin-top: -4px;
                margin-bottom: -4px;
                border-radius: 6px;
            }
            QSlider::handle:horizontal:hover {
                background: #FFFFFF;
                border: 1px solid #0A84FF;
            }
        """)
        layout_obj = self.layout_mgr.get_active_layout()
        curr_op = int((layout_obj.settings.opacity if layout_obj else 0.95) * 100)
        self.opacity_slider.setValue(curr_op)
        self.opacity_slider.setToolTip(f"透明度: {curr_op}%")
        self.opacity_slider.valueChanged.connect(self._on_opacity_slider_changed)
        self.opacity_slider.sliderReleased.connect(self.save_window_config)
        layout.addWidget(self.opacity_slider)

        # Temporary stop button shown only during macro execution
        self.stop_exec_btn = QtWidgets.QPushButton("⏹ 停止", self.footer_widget)
        self.stop_exec_btn.setFocusPolicy(QtCore.Qt.NoFocus)
        self.stop_exec_btn.setStyleSheet("""
            QPushButton {
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1, stop:0 #FF453A, stop:1 #D70015);
                color: #FFFFFF;
                border: 1px solid #B00010;
                border-radius: 5px;
                padding: 2px 10px;
                font-weight: 600;
                font-size: 10px;
                font-family: "Segoe UI Variable Text", "Segoe UI", "Microsoft YaHei UI", sans-serif;
            }
            QPushButton:hover {
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1, stop:0 #FF5B52, stop:1 #E00018);
                border: 1px solid #FF8B85;
            }
            QPushButton:pressed {
                background: #A00010;
                padding-top: 3px;
                padding-left: 11px;
            }
        """)
        self.stop_exec_btn.clicked.connect(self.executor.cancel_current)
        self.stop_exec_btn.hide()
        layout.addWidget(self.stop_exec_btn)

        layout.addStretch()

        # Right: Target window pill and lock toggle
        self.target_lock_btn = QtWidgets.QPushButton("🎯 未检测", self.footer_widget)
        self.target_lock_btn.setFocusPolicy(QtCore.Qt.NoFocus)
        self.target_lock_btn.setFixedHeight(22)
        self.target_lock_btn.setStyleSheet("""
            QPushButton {
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1, stop:0 #2C2C36, stop:1 #22222A);
                color: #B0B0C4;
                border: 1px solid #3A3A48;
                border-radius: 11px;
                padding: 2px 10px;
                font-family: "Segoe UI Variable Text", "Segoe UI", "PingFang SC", "Microsoft YaHei UI", sans-serif;
                font-size: 10px;
                font-weight: 500;
            }
            QPushButton:hover {
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1, stop:0 #383846, stop:1 #2A2A34);
                color: #FFFFFF;
                border: 1px solid #585870;
            }
            QPushButton:pressed {
                background: #181820;
                padding-top: 3px;
                padding-left: 11px;
            }
        """)
        self.target_lock_btn.clicked.connect(self.target_mgr.toggle_lock)
        layout.addWidget(self.target_lock_btn)

        parent_layout.addWidget(self.footer_widget)

    @staticmethod
    def get_tool_btn_style():
        return """
            QPushButton {
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1, stop:0 #2C2C36, stop:1 #22222A);
                color: #E2E2E8;
                font-family: "Segoe UI Variable Text", "Segoe UI", "PingFang SC", "Microsoft YaHei UI", sans-serif;
                font-size: 11px;
                border: 1px solid #3A3A48;
                border-radius: 5px;
                padding: 0px;
            }
            QPushButton:hover {
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1, stop:0 #383846, stop:1 #2A2A34);
                color: #FFFFFF;
                border: 1px solid #585870;
            }
            QPushButton:pressed {
                background: #181820;
                border: 1px solid #282834;
                padding-top: 1px;
                padding-left: 1px;
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
            self.layout_combo.addItem(lay.name, lid)
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
                old_lay.settings.saved_rows = old_lay.rows
                old_lay.settings.saved_columns = old_lay.columns
        self._current_layout_id = layout.id

        self.update_layout_combo_selection()
        op_val = int(float(layout.settings.opacity) * 100)
        self.opacity_slider.blockSignals(True)
        self.opacity_slider.setValue(op_val)
        self.opacity_slider.setToolTip(f"透明度: {op_val}%")
        self.opacity_slider.blockSignals(False)
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
        self.button_grid_layout.setSpacing(3)

        layout = self.layout_mgr.get_active_layout()
        if not layout:
            return
        layout.sanitize_slots()
        self.setWindowOpacity(float(layout.settings.opacity))
        for slot in layout.buttons:
            if slot.row >= layout.rows or slot.column >= layout.columns:
                continue
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
        bw = int(48 * base_scale)
        bh = int(30 * base_scale)
        calc_w = max(220, layout.columns * (bw + 3) + 24)
        calc_h = max(60, layout.rows * (bh + 3) + 72)

        sw = layout.settings.window_width
        sh = layout.settings.window_height
        mismatched_grid = (
            layout.settings.saved_rows is not None
            and layout.settings.saved_columns is not None
            and (layout.settings.saved_rows != layout.rows or layout.settings.saved_columns != layout.columns)
        )
        if sw and sh and 200 <= sw < 900 and not mismatched_grid:
            w = max(220, int(sw))
            h = max(60, int(sh))
        else:
            w, h = calc_w, calc_h
            layout.settings.window_width = w
            layout.settings.window_height = h
        layout.settings.saved_rows = layout.rows
        layout.settings.saved_columns = layout.columns
        self.resize(w, h)
        self._auto_sizing = False
        self._apply_button_scale()

    def _apply_button_scale(self):
        layout = self.layout_mgr.get_active_layout()
        if not layout or not self.buttons_widgets:
            return
        avail_w = max(1, self.width() - 24)
        avail_h = max(1, self.height() - 72)
        unit_w = (avail_w - (layout.columns - 1) * 3) / max(1, layout.columns)
        unit_h = (avail_h - (layout.rows - 1) * 3) / max(1, layout.rows)
        scale_x = unit_w / 48
        scale_y = unit_h / 30
        scale = max(0.72, min(2.5, min(scale_x, scale_y) if scale_y > 0 else scale_x))
        for widget in self.buttons_widgets:
            widget.apply_scale(scale)

    def resize(self, *args):
        super().resize(*args)
        if hasattr(self, "_auto_sizing") and not self._auto_sizing:
            if not self.isMaximized() and not self.isMinimized():
                layout = self.layout_mgr.get_active_layout()
                if layout:
                    layout.settings.window_width = self.width()
                    layout.settings.window_height = self.height()
                    layout.settings.saved_rows = layout.rows
                    layout.settings.saved_columns = layout.columns
            self._apply_button_scale()

    def resizeEvent(self, event):
        super().resizeEvent(event)
        if not self._auto_sizing:
            if not self.isMaximized() and not self.isMinimized():
                layout = self.layout_mgr.get_active_layout()
                if layout:
                    layout.settings.window_width = self.width()
                    layout.settings.window_height = self.height()
                    layout.settings.saved_rows = layout.rows
                    layout.settings.saved_columns = layout.columns
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

        # Layout-level auto_enter_default passed to executor (not reading from button)
        self.executor.execute_async(action, auto_enter_override=layout.settings.auto_enter_default)

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
                orig_style = getattr(widget, "_base_style", widget.styleSheet())
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
            bw = int(48 * base_scale)
            bh = int(30 * base_scale)
            calc_w = max(220, layout.columns * (bw + 3) + 24)
            calc_h = max(60, layout.rows * (bh + 3) + 72)
            sw = layout.settings.window_width
            sh = layout.settings.window_height
            mismatched_grid = (
                layout.settings.saved_rows is not None
                and layout.settings.saved_columns is not None
                and (layout.settings.saved_rows != layout.rows or layout.settings.saved_columns != layout.columns)
            )
            if sw and sh and 200 <= sw < 900 and not mismatched_grid:
                self.resize(max(220, int(sw)), max(60, int(sh)))
            else:
                self.resize(calc_w, calc_h)
                layout.settings.window_width = calc_w
                layout.settings.window_height = calc_h
            layout.settings.saved_rows = layout.rows
            layout.settings.saved_columns = layout.columns
        op = float(layout.settings.opacity) if layout else float(window.get("opacity", 0.95))
        self.setWindowOpacity(op)
        if hasattr(self, "opacity_slider"):
            op_val = int(op * 100)
            self.opacity_slider.blockSignals(True)
            self.opacity_slider.setValue(op_val)
            self.opacity_slider.setToolTip(f"透明度: {op_val}%")
            self.opacity_slider.blockSignals(False)
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
        if layout and not self._auto_sizing and not self.isMaximized() and not self.isMinimized():
            layout.settings.window_width = self.width()
            layout.settings.window_height = self.height()
        window = self.config.setdefault("window", {})
        if not self.isMaximized() and not self.isMinimized():
            window.update({
                "x": self.x(),
                "y": self.y(),
                "width": self.width(),
                "height": self.height(),
            })
        window["opacity"] = self.windowOpacity()
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
        if event.button() == QtCore.Qt.LeftButton and not self._search_interactive and not self.isMaximized():
            self._drag_pos = event.globalPos() - self.frameGeometry().topLeft()
            event.accept()
            return
        super().mousePressEvent(event)

    def mouseMoveEvent(self, event):
        if self._drag_pos and event.buttons() & QtCore.Qt.LeftButton and not self.isMaximized():
            pos = event.globalPos() - self._drag_pos
            screen = QtGui.QGuiApplication.screenAt(event.globalPos()) or QtGui.QGuiApplication.primaryScreen()
            if screen:
                area = screen.availableGeometry()
                snap = 18
                frame_w = self.frameGeometry().width()
                frame_h = self.frameGeometry().height()
                if abs(pos.x() - area.left()) <= snap:
                    pos.setX(area.left())
                if abs(pos.y() - area.top()) <= snap:
                    pos.setY(area.top())
                if abs(pos.x() + frame_w - area.right() - 1) <= snap:
                    pos.setX(area.right() - frame_w + 1)
                if abs(pos.y() + frame_h - area.bottom() - 1) <= snap:
                    pos.setY(area.bottom() - frame_h + 1)
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
