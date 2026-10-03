# -*- coding: utf-8 -*-
"""Automated tests for UI components: FloatingPanel, SettingsDialog, MacroRecorderDialog, and TrayIcon."""

import sys
import tempfile
import pytest
from PyQt5 import QtWidgets

from domain.layout import Layout, LayoutSettings
from domain.button import Button
from application.layout_manager import LayoutManager
from application.action_executor import ActionExecutor
from application.target_manager import TargetManager
from application.macro_recorder import MacroRecorder
from storage.config_store import ConfigStore
from tests.test_executor import MockInputInjector, MockClipboardManager, MockWindowManager


@pytest.fixture(scope="session")
def qapp():
    app = QtWidgets.QApplication.instance()
    if not app:
        app = QtWidgets.QApplication(sys.argv)
    return app


def test_ui_all_modules_import(qapp):
    import ui
    import ui.floating_panel
    import ui.settings_dialog
    import ui.macro_recorder_dialog
    import ui.tray_icon
    import ui.qt_signals
    assert ui.FloatingPanel is not None
    assert ui.SettingsDialog is not None
    assert ui.MacroRecorderDialog is not None
    assert ui.SystemTrayIcon is not None


def test_action_button_widget_displays_icon(qapp):
    from ui.floating_panel import ActionButtonWidget

    b1 = Button(id="b1", label="保存", action_id="a1", icon="💾")
    w1 = ActionButtonWidget(b1)
    assert "💾" in w1.text()
    assert "保存" in w1.text()

    b2 = Button(id="b2", label="兵", action_id="a2", icon="")
    w2 = ActionButtonWidget(b2)
    assert w2.text() == "兵"


def test_settings_dialog_slot_movement(qapp):
    from ui.settings_dialog import SettingsDialog

    with tempfile.TemporaryDirectory() as tmp_dir:
        cs = ConfigStore(config_dir=tmp_dir)
        lm = LayoutManager()
        lay = lm.create_layout_with_presets("test_move", "测试移动", rows=2, columns=2)
        inj = MockInputInjector()
        wm = MockWindowManager()
        clip = MockClipboardManager()
        tm = TargetManager(window_manager=wm)
        ex = ActionExecutor(injector=inj, clipboard_mgr=clip, target_mgr=tm)

        dlg = SettingsDialog(lm, ex, tm, cs)

        btn00_id = lay.get_button_at(0, 0)
        btn01_id = lay.get_button_at(0, 1)

        # Select (0, 0) and move right
        dlg._select_slot(0, 0, btn00_id)
        dlg._move_slot(0, 1)

        assert lay.get_button_at(0, 0) == btn01_id
        assert lay.get_button_at(0, 1) == btn00_id

        # Move down
        dlg._move_slot(1, 0)
        assert lay.get_button_at(1, 1) == btn00_id


def test_settings_dialog_slot_drag_swap(qapp):
    from ui.settings_dialog import SettingsDialog

    with tempfile.TemporaryDirectory() as tmp_dir:
        cs = ConfigStore(config_dir=tmp_dir)
        lm = LayoutManager()
        lay = lm.create_layout_with_presets("test_drag", "测试拖拽", rows=2, columns=2)
        inj = MockInputInjector()
        wm = MockWindowManager()
        clip = MockClipboardManager()
        tm = TargetManager(window_manager=wm)
        ex = ActionExecutor(injector=inj, clipboard_mgr=clip, target_mgr=tm)

        dlg = SettingsDialog(lm, ex, tm, cs)

        btn00_id = lay.get_button_at(0, 0)
        btn11_id = lay.get_button_at(1, 1)

        # Simulate drag & drop from (0, 0) to (1, 1)
        dlg._on_slot_drag_swap(0, 0, 1, 1)

        assert lay.get_button_at(0, 0) == btn11_id
        assert lay.get_button_at(1, 1) == btn00_id


def test_settings_dialog_icon_removed_and_label_editing(qapp):
    from ui.settings_dialog import SettingsDialog

    with tempfile.TemporaryDirectory() as tmp_dir:
        cs = ConfigStore(config_dir=tmp_dir)
        lm = LayoutManager()
        lay = lm.create_layout_with_presets("test_icon", "测试图标", rows=1, columns=2)
        inj = MockInputInjector()
        wm = MockWindowManager()
        clip = MockClipboardManager()
        tm = TargetManager(window_manager=wm)
        ex = ActionExecutor(injector=inj, clipboard_mgr=clip, target_mgr=tm)

        dlg = SettingsDialog(lm, ex, tm, cs)
        # Requirement 4: Ensure btn_icon_edit is deleted
        assert not hasattr(dlg, "btn_icon_edit")

        btn_id = lay.get_button_at(0, 0)
        dlg._select_slot(0, 0, btn_id)

        # Edit label
        dlg.btn_label_edit.setText("新标签")
        assert lm.get_button(btn_id).label == "新标签"

        # Check preview button text updated in place
        preview_btn = dlg._preview_widgets.get((0, 0))
        assert preview_btn is not None
        assert "新标签" in preview_btn.text()


def test_settings_dialog_clear_slot(qapp):
    from ui.settings_dialog import SettingsDialog

    with tempfile.TemporaryDirectory() as tmp_dir:
        cs = ConfigStore(config_dir=tmp_dir)
        lm = LayoutManager()
        lay = lm.create_layout_with_presets("test_clear", "测试清空", rows=1, columns=2)
        inj = MockInputInjector()
        wm = MockWindowManager()
        clip = MockClipboardManager()
        tm = TargetManager(window_manager=wm)
        ex = ActionExecutor(injector=inj, clipboard_mgr=clip, target_mgr=tm)

        dlg = SettingsDialog(lm, ex, tm, cs)
        btn_id = lay.get_button_at(0, 0)
        dlg._select_slot(0, 0, btn_id)

        # Clear slot
        dlg._clear_selected_slot()

        assert lay.get_button_at(0, 0) is None
        assert dlg.selected_button_id is None
        assert dlg.btn_label_edit.text() == ""
        assert dlg.btn_label_edit.isEnabled() is False


def test_macro_recorder_own_window_focus_lost():
    rec = MacroRecorder(record_delays=False)
    rec.is_recording = True
    rec.set_target(hwnd=10001, pid=5555)
    rec.register_own_hwnd(30003)

    lost = []
    regained = []
    rec.on_target_lost = lambda: lost.append(True)
    rec.on_target_regained = lambda: regained.append(True)

    # 1. Key from own QuickInput window -> should be discarded and trigger target lost
    rec.simulate_record_key(ord("A"), fg_hwnd=30003)
    assert len(rec.steps) == 0
    assert len(lost) == 1
    assert rec.is_target_in_focus is False

    # 2. Key from target window -> should be captured and trigger target regained
    rec.simulate_record_key(ord("A"), fg_hwnd=10001)
    assert len(rec.steps) == 1
    assert len(regained) == 1
    assert rec.is_target_in_focus is True


def test_floating_panel_opacity_slider_sync(qapp):
    from ui.floating_panel import FloatingPanel

    with tempfile.TemporaryDirectory() as tmp_dir:
        cs = ConfigStore(config_dir=tmp_dir)
        cs.load_config()
        lm = LayoutManager()
        lay = Layout(id="lay_op", name="透明度测试", settings=LayoutSettings(opacity=0.75))
        lm.register_layout(lay)
        lm.set_active_layout("lay_op")

        inj = MockInputInjector()
        wm = MockWindowManager()
        clip = MockClipboardManager()
        tm = TargetManager(window_manager=wm)
        ex = ActionExecutor(injector=inj, clipboard_mgr=clip, target_mgr=tm)

        panel = FloatingPanel(lm, ex, tm, cs)
        assert panel.opacity_slider.value() == 75

        # Modify layout opacity and re-apply config
        lay.settings.opacity = 0.50
        panel.apply_config()
        assert panel.opacity_slider.value() == 50


def test_settings_dialog_transposition(qapp):
    from ui.settings_dialog import SettingsDialog

    with tempfile.TemporaryDirectory() as tmp_dir:
        cs = ConfigStore(config_dir=tmp_dir)
        lm = LayoutManager()
        lay = lm.create_layout_with_presets("test_trans", "测试转置", rows=2, columns=3)
        inj = MockInputInjector()
        wm = MockWindowManager()
        clip = MockClipboardManager()
        tm = TargetManager(window_manager=wm)
        ex = ActionExecutor(injector=inj, clipboard_mgr=clip, target_mgr=tm)

        dlg = SettingsDialog(lm, ex, tm, cs)

        # Before transposition: rows=2, columns=3
        assert lay.rows == 2
        assert lay.columns == 3
        assert dlg.rows_spin.value() == 2
        assert dlg.cols_spin.value() == 3

        btn_0_1 = lay.get_button_at(0, 1)
        assert btn_0_1 is not None

        # Execute transpose
        dlg._transpose_layout()

        # After transposition: rows=3, columns=2
        assert lay.rows == 3
        assert lay.columns == 2
        assert dlg.rows_spin.value() == 3
        assert dlg.cols_spin.value() == 2

        # The slot originally at (0, 1) is now at (1, 0)
        assert lay.get_button_at(1, 0) == btn_0_1


def test_floating_panel_per_layout_window_size_switching(qapp):
    from ui.floating_panel import FloatingPanel

    with tempfile.TemporaryDirectory() as tmp_dir:
        cs = ConfigStore(config_dir=tmp_dir)
        cs.load_config()
        lm = LayoutManager()
        lay1 = lm.create_layout_with_presets("lay_1", "布局一", rows=2, columns=4)
        lay1.settings.window_width = 380
        lay1.settings.window_height = 140

        lay2 = lm.create_layout_with_presets("lay_2", "布局二", rows=4, columns=2)
        lay2.settings.window_width = 260
        lay2.settings.window_height = 240

        lm.set_active_layout("lay_1")

        inj = MockInputInjector()
        wm = MockWindowManager()
        clip = MockClipboardManager()
        tm = TargetManager(window_manager=wm)
        ex = ActionExecutor(injector=inj, clipboard_mgr=clip, target_mgr=tm)

        panel = FloatingPanel(lm, ex, tm, cs)

        # Active is lay_1 -> should have lay_1 size
        assert panel.width() == 380
        assert panel.height() == 140

        # Switch to lay_2
        lm.set_active_layout("lay_2")
        assert panel.width() == 260
        assert panel.height() == 240

        # User resizes lay_2 while active
        panel.resize(300, 280)
        assert lay2.settings.window_width == 300
        assert lay2.settings.window_height == 280

        # Switch back to lay_1 -> restores lay_1's size (380, 140), NOT lay_2's size (300, 280)
        lm.set_active_layout("lay_1")
        assert panel.width() == 380
        assert panel.height() == 140


def test_tray_icon_right_click_persistent_menu(qapp):
    from ui.tray_icon import SystemTrayIcon
    from PyQt5 import QtWidgets

    lm = LayoutManager()
    lm.create_layout_with_presets("lay_tray", "托盘布局", rows=2, columns=2)
    wm = MockWindowManager()
    tm = TargetManager(window_manager=wm)

    toggled = []
    opened = []
    quitted = []

    tray = SystemTrayIcon(
        layout_mgr=lm,
        target_mgr=tm,
        on_toggle_visible=lambda: toggled.append(True),
        on_open_settings=lambda: opened.append(True),
        on_quit=lambda: quitted.append(True),
    )

    # Context menu is persistent and has actions
    assert tray.tray_menu is not None
    assert len(tray.tray_menu.actions()) >= 4

    # Triggering context menu activation
    tray._on_tray_activated(QtWidgets.QSystemTrayIcon.Context)
    assert tray.tray_menu is not None
    assert len(tray.tray_menu.actions()) >= 4


def test_settings_dialog_select_slot_none_coordinates(qapp):
    from ui.settings_dialog import SettingsDialog

    with tempfile.TemporaryDirectory() as tmp_dir:
        cs = ConfigStore(config_dir=tmp_dir)
        lm = LayoutManager()
        lay = lm.create_layout_with_presets("test_none_coords", "坐标测试", rows=1, columns=1)
        btn = lay.buttons[0]
        inj = MockInputInjector()
        wm = MockWindowManager()
        clip = MockClipboardManager()
        tm = TargetManager(window_manager=wm)
        ex = ActionExecutor(injector=inj, clipboard_mgr=clip, target_mgr=tm)

        dlg = SettingsDialog(lm, ex, tm, cs)

        # Calling _select_slot with None coordinates should not crash
        dlg._select_slot(None, None, btn.button_id)
        assert btn.button_id == dlg.selected_button_id
        button_model = lm.get_button(btn.button_id)
        assert button_model.label in dlg.selected_info_label.text()

        # Calling _select_slot with None button should clear selection
        dlg._select_slot(None, None, None)
        assert dlg.selected_button_id is None
        assert "未选中" in dlg.selected_info_label.text()


def test_layout_transposition_empty_layout():
    from domain.layout import Layout

    empty_lay = Layout(id="empty", name="空布局", rows=3, columns=5, buttons=[])
    empty_lay.transpose()
    assert empty_lay.rows == 5
    assert empty_lay.columns == 3
    assert len(empty_lay.buttons) == 0


def test_floating_panel_combo_box_switching(qapp):
    from ui.floating_panel import FloatingPanel

    with tempfile.TemporaryDirectory() as tmp_dir:
        cs = ConfigStore(config_dir=tmp_dir)
        cs.load_config()
        lm = LayoutManager()
        lay1 = lm.create_layout_with_presets("lay_a", "布局A", rows=2, columns=2)
        lay1.settings.window_width = 320
        lay1.settings.window_height = 120

        lay2 = lm.create_layout_with_presets("lay_b", "布局B", rows=3, columns=3)
        lay2.settings.window_width = 440
        lay2.settings.window_height = 200

        lm.set_active_layout("lay_a")

        inj = MockInputInjector()
        wm = MockWindowManager()
        clip = MockClipboardManager()
        tm = TargetManager(window_manager=wm)
        ex = ActionExecutor(injector=inj, clipboard_mgr=clip, target_mgr=tm)

        panel = FloatingPanel(lm, ex, tm, cs)
        assert panel.width() == 320
        assert panel.height() == 120

        # Switch via combo box index
        idx_b = panel.layout_combo.findData("lay_b")
        assert idx_b >= 0
        panel.layout_combo.setCurrentIndex(idx_b)

        assert lm.active_layout_id == "lay_b"
        assert panel.width() == 440
        assert panel.height() == 200

        # Switch back to layout A via combo box
        idx_a = panel.layout_combo.findData("lay_a")
        assert idx_a >= 0
        panel.layout_combo.setCurrentIndex(idx_a)

        assert lm.active_layout_id == "lay_a"
        assert panel.width() == 320
        assert panel.height() == 120


def test_floating_panel_switching_uninitialized_layouts(qapp):
    """Verify that switching between layouts without pre-saved window dimensions computes independent sizes without cross-layout leakage."""
    from ui.floating_panel import FloatingPanel

    with tempfile.TemporaryDirectory() as tmp_dir:
        cs = ConfigStore(config_dir=tmp_dir)
        cs.load_config()
        lm = LayoutManager()
        lm.create_layout_with_presets("lay_h", "横排", rows=2, columns=7)
        lay_vert = lm.create_layout_with_presets("lay_v", "竖排", rows=7, columns=2)
        lm.set_active_layout("lay_h")

        wm = MockWindowManager()
        clip = MockClipboardManager()
        tm = TargetManager(window_manager=wm)
        ex = ActionExecutor(injector=MockInputInjector(), clipboard_mgr=clip, target_mgr=tm)

        panel = FloatingPanel(lm, ex, tm, cs)

        # Initial horizontal layout: width should be ~381, height ~138
        assert panel.width() > 300
        assert panel.height() < 200
        h_width, h_height = panel.width(), panel.height()

        # Switch to vertical layout: width should be ~220, height ~303, NOT adopting horizontal dimensions
        lm.set_active_layout("lay_v")
        assert panel.width() <= 240
        assert panel.height() > 280

        # User resizes vertical layout
        panel.resize(250, 350)
        assert lay_vert.settings.window_width == 250
        assert lay_vert.settings.window_height == 350

        # Switch back to horizontal layout: should restore horizontal size, not 250x350
        lm.set_active_layout("lay_h")
        assert panel.width() == h_width
        assert panel.height() == h_height

        # Switch back to vertical layout: should restore user's resized 250x350
        lm.set_active_layout("lay_v")
        assert panel.width() == 250
        assert panel.height() == 350


def test_settings_dialog_shrinkable_and_scrollable(qapp):
    """Verify SettingsDialog can shrink down to small screen sizes with scroll areas and pinned bottom actions."""
    from ui.settings_dialog import SettingsDialog

    with tempfile.TemporaryDirectory() as tmp_dir:
        cs = ConfigStore(config_dir=tmp_dir)
        lm = LayoutManager()
        lm.create_layout_with_presets("test_shrink", "缩放测试", rows=3, columns=4)
        inj = MockInputInjector()
        wm = MockWindowManager()
        clip = MockClipboardManager()
        tm = TargetManager(window_manager=wm)
        ex = ActionExecutor(injector=inj, clipboard_mgr=clip, target_mgr=tm)

        dlg = SettingsDialog(lm, ex, tm, cs)

        # Tab 0 must be wrapped in a QScrollArea
        tab0 = dlg.tabs.widget(0)
        assert isinstance(tab0, QtWidgets.QScrollArea)
        assert tab0.widgetResizable() is True

        # Dialog minimum size and minimumSizeHint must permit shrinking
        assert dlg.minimumSize().height() <= 350
        assert dlg.minimumSize().width() <= 500
        assert dlg.minimumSizeHint().height() <= 350

        # Dialog must be resizable down to 480x320
        dlg.resize(480, 320)
        assert dlg.width() <= 500
        assert dlg.height() <= 350


def test_layout_transposition_swaps_window_geometry():
    """Verify that transposing a layout swaps window_width and window_height as well as orientation."""
    from domain.layout import Layout, LayoutSettings

    settings = LayoutSettings(window_width=450, window_height=160)
    lay = Layout(id="trans_geom", name="几何转置", rows=2, columns=6, settings=settings)
    assert lay.orientation == "horizontal"

    lay.transpose()

    assert lay.rows == 6
    assert lay.columns == 2
    assert lay.orientation == "vertical"
    assert lay.settings.window_width == 220  # clamped to min 220 from 160
    assert lay.settings.window_height == 450


def test_macro_recorder_native_hook_installation():
    """Verify that low-level keyboard hook installs with a valid native handle on Windows."""
    import time
    rec = MacroRecorder()
    rec.start()
    time.sleep(0.15)
    try:
        assert rec._hook_handle is not None
        assert rec.is_recording is True
    finally:
        rec.stop()
    assert rec._hook_handle is None
    assert rec.is_recording is False


def test_settings_dialog_splitter_integrated_in_layout(qapp):
    """Verify that SettingsDialog splitter is properly added to tab_layout, not stranded at (0, 0, 100, 30)."""
    from ui.settings_dialog import SettingsDialog

    with tempfile.TemporaryDirectory() as tmp_dir:
        cs = ConfigStore(config_dir=tmp_dir)
        lm = LayoutManager()
        lm.create_layout_with_presets("test_splitter", "测试分栏", rows=2, columns=3)
        inj = MockInputInjector()
        wm = MockWindowManager()
        clip = MockClipboardManager()
        tm = TargetManager(window_manager=wm)
        ex = ActionExecutor(injector=inj, clipboard_mgr=clip, target_mgr=tm)

        dlg = SettingsDialog(lm, ex, tm, cs)
        assert hasattr(dlg, "splitter")
        assert isinstance(dlg.splitter, QtWidgets.QSplitter)

        # Tab 0 should contain top_bar, layout_box, and splitter in its layout
        tab0_scroll = dlg.tabs.widget(0)
        tab0 = tab0_scroll.widget()
        tab_layout = tab0.layout()
        assert tab_layout.count() >= 3

        # Splitter must be in tab_layout
        splitter_in_layout = False
        for i in range(tab_layout.count()):
            item = tab_layout.itemAt(i)
            if item.widget() == dlg.splitter:
                splitter_in_layout = True
                break
        assert splitter_in_layout is True, "Splitter must be managed by tab_layout"

        # Show dialog and verify splitter geometry is properly allocated
        dlg.show()
        qapp.processEvents()

        splitter_geom = dlg.splitter.geometry()
        assert splitter_geom.width() > 400
        assert splitter_geom.height() > 200
        # Must not be stuck at top-left (0, 0) overlapping top bar
        assert splitter_geom.y() > 100

        # Both preview pane and right settings pane must have valid non-trivial sizes
        sizes = dlg.splitter.sizes()
        assert len(sizes) == 2
        assert sizes[0] >= 300
        assert sizes[1] >= 300
        dlg.close()


def test_settings_dialog_initial_selection_populated(qapp):
    """Verify that on dialog launch, the first slot is selected, forms populated, and border highlighted."""
    from ui.settings_dialog import SettingsDialog
    from main import load_default_packs

    with tempfile.TemporaryDirectory() as tmp_dir:
        cs = ConfigStore(config_dir=tmp_dir)
        lm = LayoutManager()
        load_default_packs(lm, ".")
        inj = MockInputInjector()
        wm = MockWindowManager()
        clip = MockClipboardManager()
        tm = TargetManager(window_manager=wm)
        ex = ActionExecutor(injector=inj, clipboard_mgr=clip, target_mgr=tm)

        dlg = SettingsDialog(lm, ex, tm, cs)
        dlg.show()
        qapp.processEvents()

        # Slot selection must be initialized
        assert dlg.selected_row == 0
        assert dlg.selected_col == 0
        assert dlg.selected_button_id is not None
        assert "未选中" not in dlg.selected_info_label.text()
        assert "第 1 行，第 1 列" in dlg.selected_info_label.text()
        assert dlg.btn_label_edit.isEnabled() is True
        assert len(dlg.btn_label_edit.text()) > 0
        assert dlg.steps_table.rowCount() >= 1

        # Border must be green for the selected slot
        selected_widget = dlg._preview_widgets.get((0, 0))
        assert selected_widget is not None
        assert "3px solid #00E676" in selected_widget.styleSheet()

        # Right pane scroll must not require horizontal scrolling at default size
        right_scroll = dlg.splitter.widget(1)
        assert right_scroll.horizontalScrollBar().isVisible() is False
        dlg.close()


def test_settings_dialog_slot_movement_updates_info_label(qapp):
    """Verify that moving a slot properly updates selected_row, selected_col, and info label."""
    from ui.settings_dialog import SettingsDialog

    with tempfile.TemporaryDirectory() as tmp_dir:
        cs = ConfigStore(config_dir=tmp_dir)
        lm = LayoutManager()
        lm.create_layout_with_presets("test_move_lbl", "测试移动标签", rows=2, columns=2)
        inj = MockInputInjector()
        wm = MockWindowManager()
        clip = MockClipboardManager()
        tm = TargetManager(window_manager=wm)
        ex = ActionExecutor(injector=inj, clipboard_mgr=clip, target_mgr=tm)

        dlg = SettingsDialog(lm, ex, tm, cs)
        dlg.show()
        qapp.processEvents()

        assert dlg.selected_row == 0
        assert dlg.selected_col == 0
        assert "第 1 行，第 1 列" in dlg.selected_info_label.text()

        # Move slot to right
        dlg._move_slot(0, 1)
        assert dlg.selected_row == 0
        assert dlg.selected_col == 1
        assert "第 1 行，第 2 列" in dlg.selected_info_label.text()
        dlg.close()


def test_settings_dialog_layout_switch_clean_preview_and_selection(qapp):
    """Verify that switching layouts cleanly detaches old preview widgets and selects the new layout's first slot."""
    from ui.settings_dialog import SettingsDialog
    from main import load_default_packs

    with tempfile.TemporaryDirectory() as tmp_dir:
        cs = ConfigStore(config_dir=tmp_dir)
        lm = LayoutManager()
        load_default_packs(lm, ".")
        inj = MockInputInjector()
        wm = MockWindowManager()
        clip = MockClipboardManager()
        tm = TargetManager(window_manager=wm)
        ex = ActionExecutor(injector=inj, clipboard_mgr=clip, target_mgr=tm)

        dlg = SettingsDialog(lm, ex, tm, cs)
        dlg.show()
        qapp.processEvents()

        # Cycle through layouts
        for i in range(dlg.layout_selector.count()):
            dlg.layout_selector.setCurrentIndex(i)
            qapp.processEvents()
            curr = dlg._current_layout()
            expected_count = curr.rows * curr.columns
            visible_children = [
                c for c in dlg.preview_container.children()
                if isinstance(c, QtWidgets.QWidget) and c.isVisible()
            ]
            # No phantom / ghost buttons from previous layouts
            assert len(visible_children) == expected_count

            # The selected button must have a green border
            borders = [
                (r, c) for (r, c), w in dlg._preview_widgets.items()
                if "3px solid #00E676" in w.styleSheet()
            ]
            assert len(borders) == 1
            assert borders[0] == (dlg.selected_row, dlg.selected_col)
        dlg.close()
