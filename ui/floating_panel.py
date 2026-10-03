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


def format_button_display_text(icon: str, label: str) -> str:
    """Format button display text cleanly, preventing duplicate icon characters."""
    icon = (icon or "").strip()
    label = label or ""
    if not icon:
        return label
    if label.startswith(icon):
        return label
    first_token = label.split()[0] if label.split() else ""
    if first_token == icon:
        return label
    return f"{icon} {label}".strip()


class ActionButtonWidget(QtWidgets.QPushButton):
    """A button that never accepts keyboard focus during panel operation."""

    def __init__(self, button_model: Button, parent=None):
        super().__init__(parent)
        self.button_model = button_model
        self.setFocusPolicy(QtCore.Qt.NoFocus)
        self.setCursor(QtGui.QCursor(QtCore.Qt.PointingHandCursor))
        display_text = format_button_display_text(button_model.icon, button_model.label)
        self.setText(display_text)
        self.setToolTip(button_model.tooltip or button_model.label)
        self.apply_scale(1.0)

    def apply_scale(self, scale: float):
        width, height, font_size = 48, 30, 9
        width = max(32, min(180, int(width * scale)))
        height = max(24, min(100, int(height * scale)))
        font = max(8, min(20, int(font_size * scale)))
        self.setFixedSize(width, height)
        color = self.button_model.color or "#0A84FF"
        self.setStyleSheet(f"""
            QPushButton {{
                background-color: {color};
                color: #FFFFFF;
                font-family: -apple-system, "SF Pro Text", "PingFang SC", "Segoe UI Variable Text", "Segoe UI", "Microsoft YaHei UI", sans-serif;
                font-size: {font}px;
                font-weight: 600;
                border: 1px solid rgba(255, 255, 255, 0.18);
                border-radius: 6px;
                padding: 1px 2px;
            }}
            QPushButton:hover {{
                border: 1.5px solid rgba(255, 255, 255, 0.85);
            }}
            QPushButton:pressed {{
                background-color: rgba(0, 0, 0, 0.38);
                border: 1px solid rgba(255, 255, 255, 0.25);
            }}
        """)

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
        self.setAttribute(QtCore.Qt.WA_TranslucentBackground, True)
        self.setAttribute(QtCore.Qt.WA_ShowWithoutActivating, True)
        self.setMinimumSize(220, 60)
        self.setWindowTitle("快捷输入工作台")

    def showEvent(self, event):
        super().showEvent(event)
        try:
            hwnd = int(self.winId())
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
            if fg and fg != int(self.winId()) and not self._search_interactive:
                self.target_mgr.update_active_window(fg)
                if self.config.get("settings", {}).get("auto_profile_switch", True):
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
                background-color: #1C1C1E;
                border: 1px solid rgba(255, 255, 255, 0.12);
                border-radius: 10px;
            }
            QLabel {
                color: #F5F5F7;
                font-family: -apple-system, "SF Pro Text", "PingFang SC", "Segoe UI Variable Text", "Segoe UI", "Microsoft YaHei UI", sans-serif;
            }
        """)
        shadow = QtWidgets.QGraphicsDropShadowEffect(self)
        shadow.setBlurRadius(16)
        shadow.setColor(QtGui.QColor(0, 0, 0, 140))
        shadow.setOffset(0, 3)
        self.main_container.setGraphicsEffect(shadow)

        self.container_layout = QtWidgets.QVBoxLayout(self.main_container)
        self.container_layout.setContentsMargins(7, 5, 7, 5)
        self.container_layout.setSpacing(5)

        # 1. Header (Search button is first on left, then current layout dropdown, then settings)
        self.init_header(self.container_layout)

        # 2. Search Box Frame (Hidden by default, expands on clicking search)
        self.search_box_frame = QtWidgets.QFrame(self)
        self.search_box_frame.hide()
        search_layout = QtWidgets.QHBoxLayout(self.search_box_frame)
        search_layout.setContentsMargins(0, 1, 0, 1)
        self.search_input = QtWidgets.QLineEdit(self.search_box_frame)
        self.search_input.setPlaceholderText("搜索当前布局按钮… (按 Esc 退出搜索)")
        self.search_input.setClearButtonEnabled(True)
        self.search_input.setStyleSheet("""
            QLineEdit {
                background-color: rgba(255, 255, 255, 0.08);
                color: #F5F5F7;
                border: 1px solid rgba(255, 255, 255, 0.12);
                padding: 4px 8px;
                border-radius: 6px;
                font-family: -apple-system, "SF Pro Text", "PingFang SC", "Segoe UI Variable Text", "Segoe UI", sans-serif;
                font-size: 11px;
            }
            QLineEdit:focus {
                border: 1.5px solid #0A84FF;
                background-color: rgba(255, 255, 255, 0.12);
            }
        """)
        self.search_input.textChanged.connect(self.filter_buttons)
        self.search_input.installEventFilter(self)
        search_layout.addWidget(self.search_input)
        self.container_layout.addWidget(self.search_box_frame)

        # 3. Button Grid Area
        self.button_grid_widget = QtWidgets.QWidget(self)
        self.button_grid_layout = QtWidgets.QGridLayout(self.button_grid_widget)
        self.button_grid_layout.setContentsMargins(0, 1, 0, 1)
        self.button_grid_layout.setSpacing(3)
        self.container_layout.addWidget(self.button_grid_widget)

        # 4. Footer (Opacity slider on left, target window lock on right; no persistent status text)
        self.init_footer(self.container_layout)

        root = QtWidgets.QVBoxLayout(self)
        root.setContentsMargins(2, 2, 2, 2)
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
        self.search_toggle_btn.setToolTip("展开/收起搜索")
        self.search_toggle_btn.setFixedSize(26, 24)
        self.search_toggle_btn.setFocusPolicy(QtCore.Qt.NoFocus)
        self.search_toggle_btn.setStyleSheet(self.get_tool_btn_style())
        self.search_toggle_btn.clicked.connect(self.toggle_search_box)
        layout.addWidget(self.search_toggle_btn)

        # Layout selector dropdown
        self.layout_combo = QtWidgets.QComboBox(self.header_widget)
        self.layout_combo.setFocusPolicy(QtCore.Qt.NoFocus)
        self.layout_combo.setStyleSheet("""
            QComboBox {
                background-color: rgba(255, 255, 255, 0.08);
                color: #F5F5F7;
                border: 1px solid rgba(255, 255, 255, 0.10);
                padding: 2px 8px;
                border-radius: 6px;
                font-family: -apple-system, "SF Pro Text", "PingFang SC", "Segoe UI Variable Text", "Segoe UI", "Microsoft YaHei UI", sans-serif;
                font-size: 11px;
                font-weight: 500;
            }
            QComboBox:hover {
                background-color: rgba(255, 255, 255, 0.13);
                border-color: rgba(255, 255, 255, 0.22);
            }
            QComboBox::drop-down {
                subcontrol-origin: padding;
                subcontrol-position: top right;
                width: 16px;
                border-left-width: 0px;
            }
            QComboBox QAbstractItemView {
                background-color: #252528;
                color: #F5F5F7;
                border: 1px solid rgba(255, 255, 255, 0.12);
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
        layout.addWidget(self.layout_combo)

        # Settings button
        self.settings_btn = QtWidgets.QPushButton("⚙", self.header_widget)
        self.settings_btn.setToolTip("设置与布局中心")
        self.settings_btn.setFixedSize(26, 24)
        self.settings_btn.setFocusPolicy(QtCore.Qt.NoFocus)
        self.settings_btn.setStyleSheet(self.get_tool_btn_style())
        self.settings_btn.clicked.connect(self.open_settings)
        layout.addWidget(self.settings_btn)

        layout.addStretch()
        parent_layout.addWidget(self.header_widget)

    def init_footer(self, parent_layout):
        self.footer_widget = QtWidgets.QWidget(self)
        layout = QtWidgets.QHBoxLayout(self.footer_widget)
        layout.setContentsMargins(0, 2, 0, 0)
        layout.setSpacing(6)

        # Left: Layout Opacity Slider
        opacity_label = QtWidgets.QLabel("透明度", self.footer_widget)
        opacity_label.setStyleSheet("color: #8E8E93; font-size: 10px; font-weight: 500;")
        layout.addWidget(opacity_label)

        self.opacity_slider = QtWidgets.QSlider(QtCore.Qt.Horizontal, self.footer_widget)
        self.opacity_slider.setRange(30, 100)
        self.opacity_slider.setFixedWidth(80)
        self.opacity_slider.setFocusPolicy(QtCore.Qt.NoFocus)
        self.opacity_slider.setStyleSheet("""
            QSlider::groove:horizontal {
                height: 4px;
                background: rgba(255, 255, 255, 0.16);
                border-radius: 2px;
            }
            QSlider::sub-page:horizontal {
                background: #0A84FF;
                border-radius: 2px;
            }
            QSlider::handle:horizontal {
                background: #FFFFFF;
                width: 12px;
                height: 12px;
                margin-top: -4px;
                margin-bottom: -4px;
                border-radius: 6px;
            }
            QSlider::handle:horizontal:hover {
                background: #E5E5EA;
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
                background-color: #FF453A;
                color: #FFFFFF;
                border: none;
                border-radius: 5px;
                padding: 2px 10px;
                font-weight: 600;
                font-size: 10px;
            }
            QPushButton:hover {
                background-color: #D70015;
            }
        """)
        self.stop_exec_btn.clicked.connect(self.executor.cancel_current)
        self.stop_exec_btn.hide()
        layout.addWidget(self.stop_exec_btn)

        layout.addStretch()

        # Right: Target window pill and lock toggle
        self.target_lock_btn = QtWidgets.QPushButton("🎯 未检测", self.footer_widget)
        self.target_lock_btn.setFocusPolicy(QtCore.Qt.NoFocus)
        self.target_lock_btn.setStyleSheet("""
            QPushButton {
                background-color: rgba(255, 255, 255, 0.07);
                color: #A1A1A6;
                border: 1px solid rgba(255, 255, 255, 0.10);
                border-radius: 10px;
                padding: 2px 8px;
                font-family: -apple-system, "SF Pro Text", "PingFang SC", "Segoe UI Variable Text", "Segoe UI", sans-serif;
                font-size: 10px;
            }
            QPushButton:hover {
                background-color: rgba(255, 255, 255, 0.13);
                color: #F5F5F7;
            }
        """)
        self.target_lock_btn.clicked.connect(self.target_mgr.toggle_lock)
        layout.addWidget(self.target_lock_btn)

        parent_layout.addWidget(self.footer_widget)

    @staticmethod
    def get_tool_btn_style():
        return """
            QPushButton {
                background-color: rgba(255, 255, 255, 0.08);
                color: #F5F5F7;
                border: 1px solid rgba(255, 255, 255, 0.10);
                border-radius: 6px;
                padding: 0px;
                font-family: -apple-system, "SF Pro Text", "PingFang SC", "Segoe UI Variable Text", "Segoe UI", sans-serif;
            }
            QPushButton:hover {
                background-color: rgba(255, 255, 255, 0.15);
                border-color: rgba(255, 255, 255, 0.24);
            }
            QPushButton:pressed {
                background-color: rgba(255, 255, 255, 0.05);
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
        if layout.settings.window_width and layout.settings.window_height:
            w = max(220, int(layout.settings.window_width))
            h = max(60, int(layout.settings.window_height))
            self.resize(w, h)
        else:
            base_scale = {"compact": 1.0, "standard": 1.25, "touch": 1.5}.get(layout.settings.button_size, 1.0)
            bw = int(48 * base_scale)
            bh = int(30 * base_scale)
            w = max(220, layout.columns * (bw + 3) + 24)
            h = max(60, layout.rows * (bh + 3) + 72)
            self.resize(w, h)
            layout.settings.window_width = w
            layout.settings.window_height = h
        self._auto_sizing = False
        self._apply_button_scale()

    def _apply_button_scale(self):
        layout = self.layout_mgr.get_active_layout()
        if not layout or not self.buttons_widgets:
            return
        base_scale = {"compact": 1.0, "standard": 1.25, "touch": 1.5}.get(layout.settings.button_size, 1.0)
        scale_x = (self.width() - 24) / max(1, layout.columns * 51)
        scale_y = (self.height() - 72) / max(1, layout.rows * 33)
        scale = max(0.72, min(2.5, min(scale_x, scale_y) * base_scale if scale_y > 0 else scale_x * base_scale))
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
        if self.search_box_frame.isVisible():
            self.search_box_frame.hide()
            self.search_input.clear()
            self.filter_buttons("")
            self._set_search_interactive(False)
            self.clearFocus()
            self.adjustSize()
        else:
            self.search_box_frame.show()
            self._set_search_interactive(True)
            self.show()
            self.raise_()
            self.activateWindow()
            self.search_input.setFocus(QtCore.Qt.OtherFocusReason)
            self.search_input.selectAll()
            self.adjustSize()

    def filter_buttons(self, text):
        query = (text or "").strip().lower()
        for widget in self.buttons_widgets:
            model = widget.button_model
            haystack = " ".join((model.label, model.tooltip, model.icon)).lower()
            widget.setVisible(not query or query in haystack)
        self.button_grid_widget.adjustSize()
        self.adjustSize()

    def open_settings(self):
        dialog = SettingsDialog(
            self.layout_mgr, self.executor, self.target_mgr, self.config_store, parent=None
        )
        dialog.exec_()
        self.config = self.config_store.load_config()
        self.refresh_layout_combo()
        self.rebuild_buttons()
        self.apply_config()

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

    def apply_config(self):
        window = self.config.get("window", {})
        self.move(window.get("x", 350), window.get("y", 250))
        layout = self.layout_mgr.get_active_layout()
        if layout and layout.settings.window_width and layout.settings.window_height:
            self.resize(int(layout.settings.window_width), int(layout.settings.window_height))
        elif layout:
            base_scale = {"compact": 1.0, "standard": 1.25, "touch": 1.5}.get(layout.settings.button_size, 1.0)
            bw = int(48 * base_scale)
            bh = int(30 * base_scale)
            w = max(220, layout.columns * (bw + 3) + 24)
            h = max(60, layout.rows * (bh + 3) + 72)
            self.resize(w, h)
            layout.settings.window_width = w
            layout.settings.window_height = h
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
                self.toggle_search_box()
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
