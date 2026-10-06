# -*- coding: utf-8 -*-
"""Visual Macro Recorder Dialog with live step preview, target filtering, and text capture."""

from PyQt5 import QtCore, QtWidgets
from typing import List, Optional
from domain.action import ActionStep, Action
from application.macro_recorder import MacroRecorder
from application.action_executor import ActionExecutor
import win32gui
import win32process


class RecorderSignals(QtCore.QObject):
    step_captured = QtCore.pyqtSignal()
    target_lost = QtCore.pyqtSignal()
    target_regained = QtCore.pyqtSignal()


class MacroRecorderDialog(QtWidgets.QDialog):
    """Dialog for recording keystrokes and adjusting captured steps with target filtering."""

    def __init__(
        self,
        recorder: MacroRecorder,
        executor: Optional[ActionExecutor] = None,
        target_mgr=None,
        parent=None,
    ):
        super().__init__(parent)
        self.recorder = recorder
        self.executor = executor
        self.target_mgr = target_mgr
        self.recorded_steps: List[ActionStep] = []
        self.focus_poll_timer: Optional[QtCore.QTimer] = None
        self._countdown_timer: Optional[QtCore.QTimer] = None
        self._countdown_seconds = 0

        self.setWindowTitle("宏按键录制器")
        flags = (
            QtCore.Qt.Window
            | QtCore.Qt.WindowTitleHint
            | QtCore.Qt.WindowSystemMenuHint
            | QtCore.Qt.WindowMinimizeButtonHint
            | QtCore.Qt.WindowMaximizeButtonHint
            | QtCore.Qt.WindowCloseButtonHint
        )
        self.setWindowFlags(flags)
        self.setMinimumSize(620, 500)
        self.setStyleSheet("""
            QDialog {
                background-color: #1E1E20;
                color: #F5F5F7;
                font-family: "Segoe UI Variable Text", "Segoe UI", "PingFang SC", "Microsoft YaHei UI", sans-serif;
            }
            QLabel {
                color: #F5F5F7;
                font-size: 12px;
                font-family: "Segoe UI Variable Text", "Segoe UI", "PingFang SC", "Microsoft YaHei UI", sans-serif;
            }
            QPushButton {
                background-color: rgba(255, 255, 255, 0.08);
                color: #F5F5F7;
                border: 1px solid rgba(255, 255, 255, 0.10);
                border-radius: 6px;
                padding: 6px 14px;
                font-size: 12px;
                font-weight: 500;
                font-family: "Segoe UI Variable Text", "Segoe UI", "PingFang SC", "Microsoft YaHei UI", sans-serif;
            }
            QPushButton:hover {
                background-color: rgba(255, 255, 255, 0.14);
                border-color: rgba(255, 255, 255, 0.20);
            }
            QPushButton:pressed {
                background-color: rgba(255, 255, 255, 0.05);
            }
            QPushButton:disabled {
                color: #636366;
                background-color: rgba(255, 255, 255, 0.03);
                border-color: rgba(255, 255, 255, 0.05);
            }
            QTableWidget {
                background-color: #18181A;
                color: #F5F5F7;
                gridline-color: rgba(255, 255, 255, 0.04);
                border: 1px solid rgba(255, 255, 255, 0.08);
                border-radius: 8px;
                outline: none;
                font-family: "Segoe UI Variable Text", "Segoe UI", "PingFang SC", "Microsoft YaHei UI", sans-serif;
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
            QTableCornerButton::section {
                background-color: #222225;
                border: none;
                border-bottom: 1px solid rgba(255, 255, 255, 0.10);
            }
            QScrollBar:vertical {
                background: transparent;
                width: 6px;
                margin: 0px;
            }
            QScrollBar::handle:vertical {
                background: rgba(255, 255, 255, 0.18);
                border-radius: 3px;
                min-height: 20px;
            }
            QScrollBar::handle:vertical:hover {
                background: rgba(255, 255, 255, 0.32);
            }
            QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical,
            QScrollBar::add-page:vertical, QScrollBar::sub-page:vertical {
                background: none;
                height: 0px;
            }
        """)

        # Default to full-system recording so user can type in any external app
        self.recorder.set_target(None, None, "", "")

        self.init_ui()

        # Connect recorder callbacks via Qt signals for thread-safe UI updates
        self.signals = RecorderSignals(self)
        self.signals.step_captured.connect(self._update_table_from_recorder)
        self.signals.target_lost.connect(self.warning_label.show)
        self.signals.target_regained.connect(self.warning_label.hide)

        self.recorder.on_step_recorded = lambda s: self.signals.step_captured.emit()
        self.recorder.on_target_lost = lambda: self.signals.target_lost.emit()
        self.recorder.on_target_regained = lambda: self.signals.target_regained.emit()

    def init_ui(self):
        layout = QtWidgets.QVBoxLayout(self)
        layout.setSpacing(10)
        layout.setContentsMargins(14, 14, 14, 14)

        # 0. User Guidance Banner
        help_card = QtWidgets.QFrame(self)
        help_card.setStyleSheet(
            "QFrame { background-color: rgba(10, 132, 255, 0.08); border: 1px solid rgba(10, 132, 255, 0.22); border-radius: 8px; padding: 6px; }"
        )
        hc_layout = QtWidgets.QVBoxLayout(help_card)
        hc_layout.setContentsMargins(10, 8, 10, 8)
        hc_layout.setSpacing(3)
        help_title = QtWidgets.QLabel("💡 宏按键录制指南：", help_card)
        help_title.setStyleSheet("font-weight: 600; color: #0A84FF; font-size: 12px;")
        hc_layout.addWidget(help_title)
        help_text = QtWidgets.QLabel(
            "1. 点击下方【● 开始录制】按钮。\n"
            "2. 切换到您需要操作的任意其他软件（如记事本、聊天软件、网页等）正常打字或按快捷键。\n"
            "3. 外部输入将实时自动捕获并显示在列表中。录制完成后切回本窗口，点击【⏹ 停止录制】即可保存。",
            help_card,
        )
        help_text.setStyleSheet("color: #A1A1A6; font-size: 11px;")
        hc_layout.addWidget(help_text)
        layout.addWidget(help_card)

        # 1. Target & Status Banner
        self.target_box = QtWidgets.QGroupBox("1. 录制目标与状态", self)
        self.target_box.setStyleSheet(
            "QGroupBox { font-family: 'Segoe UI Variable Text', 'Segoe UI', 'PingFang SC', 'Microsoft YaHei UI', sans-serif; font-weight: 600; background-color: #252528; border: 1px solid rgba(255, 255, 255, 0.08); border-radius: 10px; margin-top: 14px; padding-top: 14px; padding-bottom: 10px; padding-left: 12px; padding-right: 12px; } "
            "QGroupBox::title { subcontrol-origin: margin; subcontrol-position: top left; left: 12px; top: 2px; background-color: #1E1E20; padding: 1px 6px; border-radius: 4px; color: #F5F5F7; font-size: 12px; }"
        )
        t_layout = QtWidgets.QVBoxLayout(self.target_box)

        top_row = QtWidgets.QHBoxLayout()
        self.target_label = QtWidgets.QLabel(self)
        self.target_label.setStyleSheet("font-size: 12px; font-weight: 600; color: #0A84FF;")
        self._update_target_label()
        top_row.addWidget(self.target_label, 1)

        self.pick_target_btn = QtWidgets.QPushButton("🎯 选择/刷新录制目标", self)
        self.pick_target_btn.setToolTip("将当前前台软件设为录制目标")
        self.pick_target_btn.clicked.connect(self.pick_target_dialog)
        top_row.addWidget(self.pick_target_btn)
        t_layout.addLayout(top_row)

        status_row = QtWidgets.QHBoxLayout()
        self.status_indicator = QtWidgets.QLabel("状态：未录制", self)
        self.status_indicator.setStyleSheet("color: #8E8E93; font-size: 12px;")
        status_row.addWidget(self.status_indicator)

        self.warning_label = QtWidgets.QLabel("⚠️ 已切换离开录制目标，按键已自动过滤", self)
        self.warning_label.setStyleSheet("color: #FF453A; font-weight: 600; font-size: 12px;")
        self.warning_label.hide()
        status_row.addWidget(self.warning_label)

        status_row.addStretch()
        t_layout.addLayout(status_row)
        layout.addWidget(self.target_box)

        # 2. Controls Bar
        btn_bar = QtWidgets.QHBoxLayout()
        self.record_btn = QtWidgets.QPushButton("● 开始录制", self)
        self.record_btn.setStyleSheet(
            "QPushButton { background-color: #FF453A; color: white; font-weight: 600; padding: 6px 18px; border-radius: 6px; border: none; } QPushButton:hover { background-color: #D70015; }"
        )
        self.record_btn.clicked.connect(self.toggle_recording)
        btn_bar.addWidget(self.record_btn)

        self.pause_btn = QtWidgets.QPushButton("❚❚ 暂停", self)
        self.pause_btn.setEnabled(False)
        self.pause_btn.clicked.connect(self.toggle_pause)
        btn_bar.addWidget(self.pause_btn)

        self.clear_btn = QtWidgets.QPushButton("清空步骤", self)
        self.clear_btn.clicked.connect(self.clear_steps)
        btn_bar.addWidget(self.clear_btn)

        self.text_capture_btn = QtWidgets.QPushButton("📝 文本/粘贴捕获…", self)
        self.text_capture_btn.setToolTip("直接输入或粘贴长文本或中文，生成稳定文本步骤")
        self.text_capture_btn.clicked.connect(self.open_text_capture)
        btn_bar.addWidget(self.text_capture_btn)

        btn_bar.addStretch()

        self.test_btn = QtWidgets.QPushButton("▶ 测试运行", self)
        self.test_btn.setStyleSheet(
            "QPushButton { background-color: #0A84FF; color: white; font-weight: 600; padding: 6px 16px; border-radius: 6px; border: none; } QPushButton:hover { background-color: #0071E3; }"
        )
        self.test_btn.clicked.connect(self.test_run)
        btn_bar.addWidget(self.test_btn)

        layout.addLayout(btn_bar)

        # 3. Table of recorded steps
        self.table = QtWidgets.QTableWidget(self)
        self.table.setColumnCount(3)
        self.table.setHorizontalHeaderLabels(["序号", "动作类型", "内容 / 参数"])
        self.table.horizontalHeader().setSectionResizeMode(0, QtWidgets.QHeaderView.ResizeToContents)
        self.table.horizontalHeader().setSectionResizeMode(1, QtWidgets.QHeaderView.ResizeToContents)
        self.table.horizontalHeader().setSectionResizeMode(2, QtWidgets.QHeaderView.Stretch)
        self.table.setSelectionBehavior(QtWidgets.QAbstractItemView.SelectRows)
        self.table.doubleClicked.connect(self.edit_selected_step)
        layout.addWidget(self.table, 1)

        # 4. Step editing tools
        edit_bar = QtWidgets.QHBoxLayout()
        edit_step_btn = QtWidgets.QPushButton("编辑步骤", self)
        edit_step_btn.clicked.connect(self.edit_selected_step)
        edit_bar.addWidget(edit_step_btn)

        del_step_btn = QtWidgets.QPushButton("删除步骤", self)
        del_step_btn.clicked.connect(self.delete_selected_step)
        edit_bar.addWidget(del_step_btn)

        up_btn = QtWidgets.QPushButton("上移", self)
        up_btn.clicked.connect(self.move_step_up)
        edit_bar.addWidget(up_btn)

        down_btn = QtWidgets.QPushButton("下移", self)
        down_btn.clicked.connect(self.move_step_down)
        edit_bar.addWidget(down_btn)

        edit_bar.addStretch()
        layout.addLayout(edit_bar)

        # 5. Bottom buttons (Save / Cancel)
        bottom_box = QtWidgets.QDialogButtonBox(
            QtWidgets.QDialogButtonBox.Ok | QtWidgets.QDialogButtonBox.Cancel, self
        )
        bottom_box.button(QtWidgets.QDialogButtonBox.Ok).setText("保存步骤到按钮")
        bottom_box.button(QtWidgets.QDialogButtonBox.Cancel).setText("取消")
        bottom_box.accepted.connect(self._on_save_accepted)
        bottom_box.rejected.connect(self.reject)
        layout.addWidget(bottom_box)

    def _update_target_label(self):
        proc = self.recorder.target_process_name or "未指定"
        title = self.recorder.target_title or "任意窗口"
        if not self.recorder.target_hwnd:
            self.target_label.setText("录制范围：全系统应用（可在任何软件中打字，自动捕获）")
        else:
            self.target_label.setText(f"录制目标：{proc} - {title}")

    def pick_target_dialog(self):
        """Allows selecting a running window or prefill from TargetManager."""
        info = self.target_mgr.get_target_info() if self.target_mgr else {}
        curr_proc = info.get("process_name", "")
        curr_title = info.get("title", "")
        curr_hwnd = info.get("handle", 0)

        msg_box = QtWidgets.QMessageBox(self)
        msg_box.setWindowTitle("选择录制目标窗口")
        desc = "请选择设置录制目标的方式："
        if curr_hwnd and curr_proc and curr_hwnd != int(self.winId()):
            desc += f"\n\n当前检测到的活动窗口：\n进程: {curr_proc}\n标题: {curr_title}"
        msg_box.setText(desc)

        btn_use_current = None
        if curr_hwnd and curr_proc and curr_hwnd != int(self.winId()):
            btn_use_current = msg_box.addButton(f"🎯 锁定当前目标 ({curr_proc})", QtWidgets.QMessageBox.ActionRole)
        btn_countdown = msg_box.addButton("⏱ 3秒倒计时拾取其他窗口", QtWidgets.QMessageBox.ActionRole)
        btn_clear = msg_box.addButton("🌐 录制全系统 (不限目标)", QtWidgets.QMessageBox.ActionRole)
        msg_box.addButton("取消", QtWidgets.QMessageBox.RejectRole)

        msg_box.exec_()
        clicked = msg_box.clickedButton()

        if clicked == btn_use_current and btn_use_current is not None:
            self.recorder.set_target(
                hwnd=curr_hwnd,
                pid=info.get("process_id"),
                process_name=curr_proc,
                title=curr_title,
            )
            self._update_target_label()
        elif clicked == btn_countdown:
            self._start_pick_countdown()
        elif clicked == btn_clear:
            self.recorder.set_target(None, None, "", "")
            self._update_target_label()

    def _start_pick_countdown(self):
        self._countdown_seconds = 3
        self.status_indicator.setText(f"请在 {self._countdown_seconds} 秒内点击并激活你要录制的目标软件窗口...")
        self.status_indicator.setStyleSheet("color: #F59E0B; font-weight: bold;")
        if self._countdown_timer:
            self._countdown_timer.stop()
        self._countdown_timer = QtCore.QTimer(self)
        self._countdown_timer.timeout.connect(self._on_pick_countdown_tick)
        self._countdown_timer.start(1000)

    def _on_pick_countdown_tick(self):
        self._countdown_seconds -= 1
        if self._countdown_seconds > 0:
            self.status_indicator.setText(f"请在 {self._countdown_seconds} 秒内点击并激活你要录制的目标软件窗口...")
        else:
            if self._countdown_timer:
                self._countdown_timer.stop()
                self._countdown_timer = None
            self._capture_active_foreground()

    def _capture_active_foreground(self):
        fg = win32gui.GetForegroundWindow()
        if fg and fg != int(self.winId()):
            title = win32gui.GetWindowText(fg)
            _, pid = win32process.GetWindowThreadProcessId(fg)
            proc_name = ""
            if self.target_mgr and hasattr(self.target_mgr, "window_manager"):
                info = self.target_mgr.window_manager.get_window_info(fg)
                proc_name = info.get("process_name", "")
            self.recorder.set_target(hwnd=fg, pid=pid, process_name=proc_name or "target.exe", title=title)
            self._update_target_label()
            self.status_indicator.setText(f"已锁定录制目标：{proc_name or 'target.exe'}，可以开始录制")
            self.status_indicator.setStyleSheet("color: #10B981; font-weight: bold;")
            self.activateWindow()
        else:
            self.status_indicator.setText("未检测到有效外部目标窗口")
            self.status_indicator.setStyleSheet("color: #EF4444;")

    def _poll_focus(self):
        if not self.recorder.is_recording or self.recorder.is_paused:
            return
        if not self.recorder.target_hwnd:
            self.warning_label.hide()
            return
        fg = win32gui.GetForegroundWindow()
        is_target = self.recorder._should_capture_foreground(fg)
        if not is_target:
            self.warning_label.show()
        else:
            self.warning_label.hide()

    def _on_target_lost_event(self):
        QtCore.QMetaObject.invokeMethod(self.warning_label, "show", QtCore.Qt.QueuedConnection)

    def _on_target_regained_event(self):
        QtCore.QMetaObject.invokeMethod(self.warning_label, "hide", QtCore.Qt.QueuedConnection)

    def _on_step_captured(self, step: ActionStep):
        QtCore.QMetaObject.invokeMethod(
            self, "_update_table_from_recorder", QtCore.Qt.QueuedConnection
        )

    @QtCore.pyqtSlot()
    def _update_table_from_recorder(self):
        self.recorded_steps = self.recorder.get_steps()
        self.refresh_table()

    def refresh_table(self):
        self.table.setRowCount(len(self.recorded_steps))
        for idx, step in enumerate(self.recorded_steps):
            num_item = QtWidgets.QTableWidgetItem(str(idx + 1))
            type_item = QtWidgets.QTableWidgetItem(step.type)

            desc = ""
            if step.type == "text":
                desc = f'"{step.value}"'
            elif step.type == "key":
                desc = step.key
            elif step.type == "hotkey":
                desc = step.hotkey or "+".join(step.keys)
            elif step.type == "delay":
                desc = f"{step.ms} 毫秒"
            elif step.type == "paste":
                desc = f'粘贴: "{step.value}"'
            else:
                desc = str(step.to_dict())

            val_item = QtWidgets.QTableWidgetItem(desc)
            self.table.setItem(idx, 0, num_item)
            self.table.setItem(idx, 1, type_item)
            self.table.setItem(idx, 2, val_item)

    def toggle_recording(self):
        if not self.recorder.is_recording:
            # Start
            self.recorder.start()
            self.record_btn.setText("⏹ 停止录制")
            self.record_btn.setStyleSheet("""
                QPushButton {
                    background-color: #D70015;
                    color: white;
                    font-weight: 600;
                    padding: 6px 18px;
                    border-radius: 6px;
                    border: none;
                }
                QPushButton:hover {
                    background-color: #B50010;
                }
            """)
            self.pause_btn.setEnabled(True)
            self.pause_btn.setText("❚❚ 暂停")
            self.status_indicator.setText("状态：正在录制中... (请切换到其他软件正常打字输入)")
            self.status_indicator.setStyleSheet("color: #FF453A; font-size: 12px; font-weight: 600;")
            if not self.focus_poll_timer:
                self.focus_poll_timer = QtCore.QTimer(self)
                self.focus_poll_timer.timeout.connect(self._poll_focus)
            self.focus_poll_timer.start(150)
        else:
            # Stop
            if self.focus_poll_timer:
                self.focus_poll_timer.stop()
            steps = self.recorder.stop()
            self.recorded_steps = steps
            self.record_btn.setText("● 开始录制")
            self.record_btn.setStyleSheet("""
                QPushButton {
                    background-color: #FF453A;
                    color: white;
                    font-weight: 600;
                    padding: 6px 18px;
                    border-radius: 6px;
                    border: none;
                }
                QPushButton:hover {
                    background-color: #D70015;
                }
            """)
            self.pause_btn.setEnabled(False)
            self.status_indicator.setText("状态：已停止")
            self.status_indicator.setStyleSheet("color: #30D158; font-size: 12px; font-weight: 600;")
            self.warning_label.hide()
            self.refresh_table()

    def toggle_pause(self):
        if not self.recorder.is_recording:
            return
        if self.recorder.is_paused:
            self.recorder.resume()
            self.pause_btn.setText("❚❚ 暂停")
            self.status_indicator.setText("状态：正在录制中...")
            self.status_indicator.setStyleSheet("color: #FF453A; font-size: 12px; font-weight: 600;")
            if self.focus_poll_timer:
                self.focus_poll_timer.start(150)
        else:
            self.recorder.pause()
            self.pause_btn.setText("▶ 继续")
            self.status_indicator.setText("状态：已暂停")
            self.status_indicator.setStyleSheet("color: #FF9F0A; font-size: 12px; font-weight: 600;")
            if self.focus_poll_timer:
                self.focus_poll_timer.stop()

    def clear_steps(self):
        self.recorded_steps.clear()
        if self.recorder.is_recording:
            self.recorder.steps.clear()
        self.refresh_table()

    def open_text_capture(self):
        text, ok = QtWidgets.QInputDialog.getMultiLineText(
            self, "文本 / 粘贴捕获", "输入或粘贴文本内容（支持多行和中文）："
        )
        if ok and text:
            msg_box = QtWidgets.QMessageBox(self)
            msg_box.setWindowTitle("选择模式")
            msg_box.setText("请选择如何发送该文本：")
            btn_paste = msg_box.addButton("通过剪贴板粘贴 (推荐中文)", QtWidgets.QMessageBox.ActionRole)
            btn_text = msg_box.addButton("模拟逐字输入", QtWidgets.QMessageBox.ActionRole)
            msg_box.addButton("取消", QtWidgets.QMessageBox.RejectRole)
            msg_box.exec_()
            if msg_box.clickedButton() == btn_paste:
                self.recorder.add_text_step(text, as_paste=True)
            elif msg_box.clickedButton() == btn_text:
                self.recorder.add_text_step(text, as_paste=False)
            self.recorded_steps = list(self.recorder.steps)
            self.refresh_table()

    def delete_selected_step(self):
        row = self.table.currentRow()
        if 0 <= row < len(self.recorded_steps):
            del self.recorded_steps[row]
            if self.recorder.is_recording and row < len(self.recorder.steps):
                del self.recorder.steps[row]
            self.refresh_table()

    def move_step_up(self):
        row = self.table.currentRow()
        if 0 < row < len(self.recorded_steps):
            self.recorded_steps[row], self.recorded_steps[row - 1] = (
                self.recorded_steps[row - 1],
                self.recorded_steps[row],
            )
            self.refresh_table()
            self.table.selectRow(row - 1)

    def move_step_down(self):
        row = self.table.currentRow()
        if 0 <= row < len(self.recorded_steps) - 1:
            self.recorded_steps[row], self.recorded_steps[row + 1] = (
                self.recorded_steps[row + 1],
                self.recorded_steps[row],
            )
            self.refresh_table()
            self.table.selectRow(row + 1)

    def test_run(self):
        if not self.recorded_steps or not self.executor:
            return
        temp_action = Action(
            id="test_record",
            label="测试录制动作",
            steps=self.recorded_steps,
        )
        self.executor.execute_async(temp_action)

    def showEvent(self, event):
        super().showEvent(event)
        try:
            hwnd = int(self.winId())
            self.recorder.register_own_hwnd(hwnd)
            if self.parent():
                self.recorder.register_own_hwnd(int(self.parent().winId()))
            import win32gui, win32con
            win32gui.SetWindowPos(
                hwnd,
                win32con.HWND_NOTOPMOST,
                0, 0, 0, 0,
                win32con.SWP_NOMOVE | win32con.SWP_NOSIZE | win32con.SWP_NOACTIVATE,
            )
        except Exception:
            pass

    def edit_selected_step(self):
        row = self.table.currentRow()
        if not (0 <= row < len(self.recorded_steps)):
            return
        step = self.recorded_steps[row]
        if step.type in ("text", "paste"):
            new_val, ok = QtWidgets.QInputDialog.getText(
                self, "编辑文本步骤", "输入修改后的文本内容:", text=step.value
            )
            if ok:
                step.value = new_val
        elif step.type == "key":
            common_keys = [
                "ENTER", "TAB", "ESC", "SPACE", "BACKSPACE", "DELETE",
                "UP", "DOWN", "LEFT", "RIGHT", "PAGEUP", "PAGEDOWN", "HOME", "END",
                "F1", "F2", "F3", "F4", "F5", "F6", "F7", "F8", "F9", "F10", "F11", "F12"
            ]
            curr_idx = common_keys.index(step.key) if step.key in common_keys else 0
            new_key, ok = QtWidgets.QInputDialog.getItem(
                self, "编辑按键步骤", "选择或输入按键:", common_keys, curr_idx, True
            )
            if ok and new_key:
                step.key = new_key.strip().upper()
        elif step.type == "hotkey":
            curr_hk = step.hotkey or "+".join(step.keys)
            new_hk, ok = QtWidgets.QInputDialog.getText(
                self, "编辑组合键步骤", "输入修改后的组合键 (例如 CTRL+S):", text=curr_hk
            )
            if ok and new_hk:
                step.hotkey = new_hk.strip().upper()
                step.keys = [k.strip() for k in step.hotkey.split("+") if k.strip()]
        elif step.type == "delay":
            new_ms, ok = QtWidgets.QInputDialog.getInt(
                self, "编辑等待步骤", "输入等待毫秒数 (ms):", value=step.ms, min=10, max=30000
            )
            if ok:
                step.ms = new_ms

        self.refresh_table()

    def _cleanup_timers(self):
        if self.focus_poll_timer and self.focus_poll_timer.isActive():
            self.focus_poll_timer.stop()
        if self._countdown_timer and self._countdown_timer.isActive():
            self._countdown_timer.stop()

    def _on_save_accepted(self):
        self._cleanup_timers()
        if self.recorder.is_recording:
            self.recorder.stop()
        self.accept()

    def reject(self):
        self._cleanup_timers()
        if self.recorder.is_recording:
            self.recorder.cancel()
        super().reject()

    def closeEvent(self, event):
        self._cleanup_timers()
        if self.recorder.is_recording:
            self.recorder.cancel()
        super().closeEvent(event)

    def showEvent(self, event):
        super().showEvent(event)
        try:
            from ui.floating_panel import set_window_dark_titlebar
            set_window_dark_titlebar(int(self.winId()))
        except Exception:
            pass
