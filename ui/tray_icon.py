# -*- coding: utf-8 -*-
"""System Tray Icon for QuickInput."""

from PyQt5 import QtCore, QtGui, QtWidgets
from typing import Callable
from application.layout_manager import LayoutManager
from application.target_manager import TargetManager


class SystemTrayIcon(QtWidgets.QSystemTrayIcon):
    """System tray icon with menu for quick actions and layout switching."""

    def __init__(
        self,
        layout_mgr: LayoutManager,
        target_mgr: TargetManager,
        on_toggle_visible: Callable[[], None],
        on_open_settings: Callable[[], None],
        on_quit: Callable[[], None],
        parent=None,
    ):
        super().__init__(parent)
        self.layout_mgr = layout_mgr
        self.target_mgr = target_mgr
        self.on_toggle_visible = on_toggle_visible
        self.on_open_settings = on_open_settings
        self.on_quit = on_quit

        # Create persistent menu to prevent garbage collection
        self.tray_menu = QtWidgets.QMenu()
        self.tray_menu.setStyleSheet("""
            QMenu {
                background-color: #252528;
                color: #F5F5F7;
                border: 1px solid rgba(255, 255, 255, 0.12);
                border-radius: 8px;
                padding: 5px;
                font-family: -apple-system, "SF Pro Text", "PingFang SC", "Segoe UI Variable Text", "Segoe UI", sans-serif;
                font-size: 12px;
            }
            QMenu::item {
                color: #F5F5F7;
                padding: 6px 18px;
                border-radius: 4px;
            }
            QMenu::item:selected {
                background-color: #0A84FF;
                color: #FFFFFF;
            }
            QMenu::separator {
                height: 1px;
                background: rgba(255, 255, 255, 0.08);
                margin: 4px 6px;
            }
        """)
        self.tray_menu.aboutToShow.connect(self.build_menu)
        self.setContextMenu(self.tray_menu)

        # Create icon
        icon = self._create_icon()
        self.setIcon(icon)
        self.setToolTip("快捷输入工作台｜左键显示/隐藏，右键菜单可退出")

        self.activated.connect(self._on_tray_activated)
        self.build_menu()

    def _create_icon(self) -> QtGui.QIcon:
        pix = QtGui.QPixmap(32, 32)
        pix.fill(QtCore.Qt.transparent)
        painter = QtGui.QPainter(pix)
        painter.setRenderHint(QtGui.QPainter.Antialiasing)

        # Draw rounded badge
        painter.setBrush(QtGui.QColor("#0A84FF"))
        painter.setPen(QtCore.Qt.NoPen)
        painter.drawRoundedRect(2, 2, 28, 28, 7, 7)

        # Draw text 'Q'
        painter.setPen(QtGui.QColor("#FFFFFF"))
        font = QtGui.QFont("SF Pro Display", 16, QtGui.QFont.Bold)
        font.setStyleHint(QtGui.QFont.SansSerif)
        painter.setFont(font)
        painter.drawText(pix.rect(), QtCore.Qt.AlignCenter, "Q")
        painter.end()

        return QtGui.QIcon(pix)

    def build_menu(self):
        self.tray_menu.clear()

        # 1. Toggle visibility
        toggle_action = self.tray_menu.addAction("显示/隐藏工作台 (Alt+Q)")
        toggle_action.triggered.connect(self.on_toggle_visible)

        # 2. Layout submenu
        layout_submenu = self.tray_menu.addMenu("切换当前布局")
        for lid, lay in self.layout_mgr.layouts.items():
            act = layout_submenu.addAction(lay.name)
            act.setCheckable(True)
            act.setChecked(lid == self.layout_mgr.active_layout_id)
            act.triggered.connect(lambda ch, l_id=lid: self.layout_mgr.set_active_layout(l_id))

        # 3. Lock/Unlock target
        target_info = self.target_mgr.get_target_info()
        lock_text = "🔓 解锁目标窗口" if target_info.get("is_locked") else "🔒 锁定当前目标窗口"
        lock_action = self.tray_menu.addAction(lock_text)
        lock_action.triggered.connect(self.target_mgr.toggle_lock)

        self.tray_menu.addSeparator()

        # 4. Settings
        settings_action = self.tray_menu.addAction("⚙ 设置与布局中心...")
        settings_action.triggered.connect(self.on_open_settings)

        self.tray_menu.addSeparator()

        # 5. Quit
        quit_action = self.tray_menu.addAction("退出程序")
        quit_action.triggered.connect(self.on_quit)

    def _on_tray_activated(self, reason):
        if reason == QtWidgets.QSystemTrayIcon.Trigger:  # Single click
            self.on_toggle_visible()
        elif reason == QtWidgets.QSystemTrayIcon.DoubleClick:
            self.on_toggle_visible()
        elif reason == QtWidgets.QSystemTrayIcon.Context:  # Right click
            self.build_menu()
            if not self.tray_menu.isVisible():
                self.tray_menu.popup(QtGui.QCursor.pos())
