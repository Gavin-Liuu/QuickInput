# -*- coding: utf-8 -*-
"""Internationalization (i18n) translation system supporting Chinese and English."""

from typing import Dict, Optional

# Supported languages
LANG_ZH = "zh"
LANG_EN = "en"

_CURRENT_LANG = LANG_ZH

TRANSLATIONS: Dict[str, Dict[str, str]] = {
    # Main Window / Floating Panel
    "app_title": {
        "zh": "快捷输入工作台",
        "en": "QuickInput Workbench",
    },
    "search_placeholder": {
        "zh": "全局搜索所有布局按钮… (Esc 退出)",
        "en": "Search all buttons… (Esc to exit)",
    },
    "search_tooltip": {
        "zh": "搜索按钮 (点击展开/退出搜索)",
        "en": "Search (Click to toggle search box)",
    },
    "settings_tooltip": {
        "zh": "打开设置中心",
        "en": "Open Settings Center",
    },
    "opacity_label": {
        "zh": "透明度",
        "en": "Opacity",
    },
    "target_undetected": {
        "zh": "未检测",
        "en": "Undetected",
    },
    "target_locked": {
        "zh": "已锁定",
        "en": "Locked",
    },
    "target_auto": {
        "zh": "自动跟随",
        "en": "Auto Follow",
    },
    "target_tooltip": {
        "zh": "目标：{title} ({proc})\n状态：{status}\n点击切换锁定状态",
        "en": "Target: {title} ({proc})\nStatus: {status}\nClick to toggle lock",
    },

    # Settings Dialog Navigation & Tabs
    "settings_title": {
        "zh": "快捷输入工作台 - 设置中心",
        "en": "QuickInput - Settings Center",
    },
    "tab_layouts": {
        "zh": "布局与按钮",
        "en": "Layouts & Buttons",
    },
    "tab_general": {
        "zh": "常规与诊断",
        "en": "General & Diagnostics",
    },

    # Settings - Layouts Tab - Top bar
    "layout_select_label": {
        "zh": "当前布局:",
        "en": "Current Layout:",
    },
    "btn_new_layout": {
        "zh": "＋ 新建布局",
        "en": "+ New Layout",
    },
    "btn_copy_layout": {
        "zh": "复制当前布局",
        "en": "Duplicate Layout",
    },
    "btn_rename_layout": {
        "zh": "重命名",
        "en": "Rename",
    },
    "btn_del_layout": {
        "zh": "删除布局",
        "en": "Delete Layout",
    },
    "btn_reset_preset": {
        "zh": "恢复预设",
        "en": "Reset Preset",
    },
    "btn_reset_preset_tip": {
        "zh": "将当前布局重置为官方预设初始状态",
        "en": "Reset current layout to official preset defaults",
    },
    "btn_export_pack": {
        "zh": "导出场景包…",
        "en": "Export Pack…",
    },
    "btn_import_pack": {
        "zh": "导入场景包…",
        "en": "Import Pack…",
    },

    # Settings - Layout Properties Box
    "layout_props_title": {
        "zh": "布局属性与全局默认值 (当前布局)",
        "en": "Layout Properties & Defaults (Current)",
    },
    "rows_label": {
        "zh": "行数:",
        "en": "Rows:",
    },
    "cols_label": {
        "zh": "列数:",
        "en": "Columns:",
    },
    "btn_size_label": {
        "zh": "按钮尺寸:",
        "en": "Button Size:",
    },
    "size_compact": {
        "zh": "紧凑",
        "en": "Compact",
    },
    "size_standard": {
        "zh": "标准",
        "en": "Standard",
    },
    "size_touch": {
        "zh": "触屏大按钮",
        "en": "Touch / Large",
    },
    "opacity_slider_label": {
        "zh": "透明度:",
        "en": "Opacity:",
    },
    "always_on_top_chk": {
        "zh": "保持在顶层",
        "en": "Always on Top",
    },
    "confirm_action_chk": {
        "zh": "执行前确认",
        "en": "Confirm Before Action",
    },
    "confirm_action_tip": {
        "zh": "开启后，点击当前布局内任何按钮执行动作前均弹出确认对话框",
        "en": "Show confirmation dialog before executing any action in this layout",
    },
    "auto_enter_chk": {
        "zh": "动作结束后发送 Enter",
        "en": "Send Enter on Completion",
    },
    "auto_enter_tip": {
        "zh": "开启后，当前布局所有动作执行完毕后自动追加一个 Enter 回车键",
        "en": "Automatically append an Enter key when action finishes",
    },

    # Settings - Layout Preview
    "preview_lbl": {
        "zh": "布局预览:",
        "en": "Preview:",
    },
    "preview_hint": {
        "zh": "（点击选中 / 拖动调换）",
        "en": "(Click to select / Drag to swap)",
    },
    "preview_tip": {
        "zh": "点击按钮即可选中编辑；支持拖动按钮与其他槽位调换位置",
        "en": "Click button to select & edit; drag to swap slots",
    },
    "btn_transpose": {
        "zh": "⇄ 行列转换",
        "en": "⇄ Transpose",
    },
    "btn_transpose_tip": {
        "zh": "转换行列（转置布局），行列数互换",
        "en": "Transpose layout rows and columns",
    },
    "btn_clear_slot": {
        "zh": "清空槽位",
        "en": "Clear Slot",
    },
    "btn_clear_slot_tip": {
        "zh": "删除当前选中槽位的按钮并保留空槽位",
        "en": "Delete button in selected slot keeping it empty",
    },
    "slot_adjust_label": {
        "zh": "槽位微调:",
        "en": "Nudge Slot:",
    },
    "btn_slot_up": {
        "zh": "▲ 上移",
        "en": "▲ Up",
    },
    "btn_slot_down": {
        "zh": "▼ 下移",
        "en": "▼ Down",
    },
    "btn_slot_left": {
        "zh": "◀ 左移",
        "en": "◀ Left",
    },
    "btn_slot_right": {
        "zh": "▶ 右移",
        "en": "▶ Right",
    },

    # Button Properties Box
    "btn_props_title": {
        "zh": "选中按钮属性",
        "en": "Selected Button Properties",
    },
    "slot_status_label": {
        "zh": "槽位状态:",
        "en": "Slot Status:",
    },
    "no_btn_selected": {
        "zh": "未选中按钮（请在左侧预览中点击按钮）",
        "en": "No button selected (Click a slot in preview)",
    },
    "slot_info_occupied": {
        "zh": "第 {row} 行，第 {col} 列 (按钮 ID: {id})",
        "en": "Row {row}, Col {col} (Button ID: {id})",
    },
    "slot_info_empty": {
        "zh": "第 {row} 行，第 {col} 列 (空槽位，添加下方动作即可新建)",
        "en": "Row {row}, Col {col} (Empty slot, add steps below)",
    },
    "btn_text_label": {
        "zh": "显示文字:",
        "en": "Display Text:",
    },
    "btn_text_placeholder": {
        "zh": "例如: 保存 或 Ctrl+S",
        "en": "e.g. Save or Ctrl+S",
    },
    "btn_text_tip": {
        "zh": "按钮显示的文字标签，支持换行（输入 \\n 可表示换行）",
        "en": "Button display label, supports \\n for newline",
    },
    "btn_color_label": {
        "zh": "按钮颜色:",
        "en": "Button Color:",
    },
    "btn_tooltip_label": {
        "zh": "悬浮提示:",
        "en": "Tooltip:",
    },

    # Preset Color Names
    "color_blue": {
        "zh": "蓝色",
        "en": "Blue",
    },
    "color_red": {
        "zh": "红色",
        "en": "Red",
    },
    "color_gray": {
        "zh": "灰色",
        "en": "Gray",
    },
    "color_green": {
        "zh": "绿色",
        "en": "Green",
    },
    "color_purple": {
        "zh": "紫色",
        "en": "Purple",
    },
    "color_orange": {
        "zh": "橙色",
        "en": "Orange",
    },
    "color_sky": {
        "zh": "天蓝",
        "en": "Sky Blue",
    },
    "color_indigo": {
        "zh": "靛蓝",
        "en": "Indigo",
    },

    # Action Steps Box
    "action_steps_title": {
        "zh": "动作步骤",
        "en": "Action Steps",
    },
    "step_col_type": {
        "zh": "步骤",
        "en": "Step",
    },
    "step_col_param": {
        "zh": "参数",
        "en": "Parameter",
    },
    "step_col_desc": {
        "zh": "说明",
        "en": "Description",
    },
    "step_type_paste": {
        "zh": "文本",
        "en": "Text",
    },
    "step_type_key": {
        "zh": "按键",
        "en": "Key",
    },
    "step_type_hotkey": {
        "zh": "组合键",
        "en": "Hotkey",
    },
    "step_type_delay": {
        "zh": "等待",
        "en": "Delay",
    },
    "step_desc_paste": {
        "zh": "快速文本输入",
        "en": "Fast text input",
    },
    "step_desc_key": {
        "zh": "敲击单键",
        "en": "Press single key",
    },
    "step_desc_hotkey": {
        "zh": "快捷组合键",
        "en": "Shortcut combo",
    },
    "step_desc_delay": {
        "zh": "等待毫秒",
        "en": "Wait milliseconds",
    },
    "btn_record_macro": {
        "zh": "⏺ 录制宏…",
        "en": "⏺ Record Macro…",
    },
    "btn_record_macro_tip": {
        "zh": "实时录制键盘与鼠标操作",
        "en": "Record keyboard and mouse actions in real-time",
    },
    "btn_add_text": {
        "zh": "＋ 文本",
        "en": "+ Text",
    },
    "btn_add_text_tip": {
        "zh": "添加文本输入步骤 (剪贴板粘贴)",
        "en": "Add text input step (Clipboard paste)",
    },
    "btn_add_key": {
        "zh": "＋ 按键",
        "en": "+ Key",
    },
    "btn_add_key_tip": {
        "zh": "添加按键或组合快捷键",
        "en": "Add key or shortcut combination",
    },
    "btn_add_delay": {
        "zh": "＋ 等待",
        "en": "+ Delay",
    },
    "btn_add_delay_tip": {
        "zh": "添加延时等待 (毫秒)",
        "en": "Add delay (ms)",
    },
    "btn_edit_step": {
        "zh": "编辑步骤",
        "en": "Edit Step",
    },
    "btn_del_step": {
        "zh": "删除步骤",
        "en": "Delete Step",
    },
    "btn_move_up": {
        "zh": "▲ 上移",
        "en": "▲ Move Up",
    },
    "btn_move_up_tip": {
        "zh": "将当前选中的动作步骤上移一位",
        "en": "Move selected step up",
    },
    "btn_move_down": {
        "zh": "▼ 下移",
        "en": "▼ Move Down",
    },
    "btn_move_down_tip": {
        "zh": "将当前选中的动作步骤下移一位",
        "en": "Move selected step down",
    },

    # App Binding Box
    "app_binding_title": {
        "zh": "应用绑定 (切到指定软件时自动启用当前布局)",
        "en": "App Binding (Auto switch to current layout when target focused)",
    },
    "bind_col_process": {
        "zh": "目标进程名",
        "en": "Process Name",
    },
    "bind_col_title": {
        "zh": "窗口标题包含",
        "en": "Window Title Filter",
    },
    "btn_bind_current": {
        "zh": "🎯 绑定最近目标应用",
        "en": "🎯 Bind Recent App",
    },
    "btn_bind_current_tip": {
        "zh": "绑定打开设置前最近一次聚焦的外部应用程序",
        "en": "Bind the target window active before opening settings",
    },
    "btn_bind_pick": {
        "zh": "🪟 从打开的窗口选择",
        "en": "🪟 Select Window",
    },
    "btn_bind_pick_tip": {
        "zh": "从当前运行中的全部窗口列表中选择一个应用绑定",
        "en": "Choose an application from currently running windows",
    },
    "btn_bind_custom": {
        "zh": "＋ 手动输入",
        "en": "+ Add Manually",
    },
    "btn_bind_delete": {
        "zh": "删除选中绑定",
        "en": "Delete Binding",
    },

    # Settings - General & Diagnostics Tab
    "language_group_title": {
        "zh": "界面语言与常规设置",
        "en": "Interface Language & General Settings",
    },
    "language_label": {
        "zh": "界面语言:",
        "en": "Language:",
    },
    "lang_zh": {
        "zh": "简体中文 (Chinese Simplified)",
        "en": "简体中文 (Chinese Simplified)",
    },
    "lang_en": {
        "zh": "English (英语)",
        "en": "English",
    },
    "hotkey_group_title": {
        "zh": "全局快捷键与自动化",
        "en": "Global Hotkeys & Automation",
    },
    "auto_profile_switch_label": {
        "zh": "场景切换:",
        "en": "Auto Switch:",
    },
    "auto_profile_switch_chk": {
        "zh": "根据前台活动窗口自动切换布局",
        "en": "Auto switch layout based on foreground window",
    },
    "toggle_hotkey_label": {
        "zh": "显示/隐藏工作台:",
        "en": "Show/Hide Workbench:",
    },
    "toggle_hotkey_placeholder": {
        "zh": "例如 ALT+Q",
        "en": "e.g. ALT+Q",
    },
    "stop_hotkey_label": {
        "zh": "紧急停止宏快捷键:",
        "en": "Emergency Stop Hotkey:",
    },
    "stop_hotkey_placeholder": {
        "zh": "例如 ESC",
        "en": "e.g. ESC",
    },
    "backup_group_title": {
        "zh": "配置备份与恢复",
        "en": "Configuration Backup & Restore",
    },
    "btn_backup": {
        "zh": "备份当前配置",
        "en": "Backup Configuration",
    },
    "diag_group_title": {
        "zh": "系统诊断与最近执行日志",
        "en": "System Diagnostics & Execution Logs",
    },
    "target_info_prefix": {
        "zh": "目标检测: {info}",
        "en": "Target Detection: {info}",
    },
    "log_col_time": {
        "zh": "时间",
        "en": "Time",
    },
    "log_col_action": {
        "zh": "动作 ID",
        "en": "Action ID",
    },
    "log_col_status": {
        "zh": "状态",
        "en": "Status",
    },
    "log_col_desc": {
        "zh": "说明",
        "en": "Description",
    },
    "btn_refresh_diag": {
        "zh": "刷新诊断信息",
        "en": "Refresh Diagnostics",
    },
    "btn_save_settings": {
        "zh": "保存并关闭",
        "en": "Save & Close",
    },
    "btn_cancel_settings": {
        "zh": "取消",
        "en": "Cancel",
    },

    # Key Capture Dialog (Elegant & Concise)
    "key_capture_title": {
        "zh": "按键录制",
        "en": "Key Recording",
    },
    "key_capture_instruction": {
        "zh": "请按下目标按键或组合快捷键：",
        "en": "Press desired key or shortcut combination:",
    },
    "key_capture_input_placeholder": {
        "zh": "等待按键输入… (例如 Ctrl+S 或 Enter)",
        "en": "Waiting for keypress… (e.g. Ctrl+S or Enter)",
    },
    "btn_ok": {
        "zh": "确定",
        "en": "OK",
    },
    "btn_clear": {
        "zh": "清除",
        "en": "Clear",
    },

    # Prompts & Message Boxes
    "prompt_notice": {
        "zh": "提示",
        "en": "Notice",
    },
    "prompt_warning": {
        "zh": "警告",
        "en": "Warning",
    },
    "prompt_confirm": {
        "zh": "确认",
        "en": "Confirm",
    },
    "prompt_record_key_first": {
        "zh": "请先录制或输入要添加的按键/快捷键！",
        "en": "Please record or enter a key/shortcut first!",
    },
    "prompt_new_layout_title": {
        "zh": "新建布局",
        "en": "New Layout",
    },
    "prompt_new_layout_label": {
        "zh": "请输入新布局名称:",
        "en": "Enter new layout name:",
    },
    "prompt_new_layout_default": {
        "zh": "新建布局",
        "en": "New Layout",
    },
    "prompt_copy_layout_title": {
        "zh": "复制布局",
        "en": "Duplicate Layout",
    },
    "prompt_copy_layout_suffix": {
        "zh": " (副本)",
        "en": " (Copy)",
    },
    "prompt_rename_layout_title": {
        "zh": "重命名布局",
        "en": "Rename Layout",
    },
    "prompt_del_layout_confirm": {
        "zh": "确定要删除布局 '{name}' 吗？此操作无法撤销。",
        "en": "Are you sure you want to delete layout '{name}'? This cannot be undone.",
    },
    "prompt_del_layout_min": {
        "zh": "至少需要保留一个布局，无法删除！",
        "en": "At least one layout must be kept, cannot delete!",
    },
    "prompt_reset_preset_confirm": {
        "zh": "确定将布局 '{name}' 重置为官方默认预设吗？自定义修改将丢失。",
        "en": "Reset layout '{name}' to default preset? Custom modifications will be lost.",
    },
    "prompt_reset_preset_nonpreset": {
        "zh": "当前布局不是内置官方预设，无法自动重置！",
        "en": "Current layout is not a built-in preset and cannot be reset!",
    },
    "prompt_backup_success": {
        "zh": "配置已成功备份至:\n{path}",
        "en": "Configuration successfully backed up to:\n{path}",
    },

    # Preset Layout Names
    "layout_name_word": {
        "zh": "微软 Word 常用排版",
        "en": "Microsoft Word Document",
    },
    "layout_name_programmer": {
        "zh": "程序员常用命令",
        "en": "Developer & Shell Commands",
    },
    "layout_name_annotation": {
        "zh": "图片标注",
        "en": "Image Annotation",
    },
    "layout_name_customer_service": {
        "zh": "客服话术",
        "en": "Customer Service Quick Replies",
    },

    # Tray Menu
    "tray_tooltip": {
        "zh": "快捷输入工作台｜左键显示/隐藏，右键菜单可退出",
        "en": "QuickInput | Click to Show/Hide, Right-click for menu",
    },
    "tray_toggle": {
        "zh": "显示/隐藏工作台 (Alt+Q)",
        "en": "Show/Hide Workbench (Alt+Q)",
    },
    "tray_switch_layout": {
        "zh": "切换当前布局",
        "en": "Switch Layout",
    },
    "tray_unlock_target": {
        "zh": "🔓 解锁目标窗口",
        "en": "🔓 Unlock Target Window",
    },
    "tray_lock_target": {
        "zh": "🔒 锁定当前目标窗口",
        "en": "🔒 Lock Current Target Window",
    },
    "tray_settings": {
        "zh": "⚙ 设置与布局中心...",
        "en": "⚙ Settings & Layout Center...",
    },
    "tray_quit": {
        "zh": "退出程序",
        "en": "Quit Application",
    },

    # Binding & Dialog Prompts
    "bind_no_external_target": {
        "zh": "当前未捕获到外部目标应用！\n\n请在外部软件窗口中点击一次，或从运行中的窗口列表中直接选择。",
        "en": "No external target application currently captured!\n\nPlease click an external application window once, or select from running windows.",
    },
    "bind_confirm_target": {
        "zh": "检测到最近使用的外部应用：\n\n• 进程名：{proc}\n• 窗口标题：{title}\n\n是否将该应用绑定到当前布局【{layout}】？",
        "en": "Detected recent external application:\n\n• Process: {proc}\n• Window Title: {title}\n\nBind this application to layout [{layout}]?",
    },
    "bind_success_notice": {
        "zh": "已成功将应用 {proc} 绑定到当前布局【{layout}】！",
        "en": "Successfully bound {proc} to layout [{layout}]!",
    },
    "bind_no_running_windows": {
        "zh": "未找到可绑定的运行中外部窗口。",
        "en": "No running external windows found to bind.",
    },
    "bind_select_running_title": {
        "zh": "请从当前打开的应用列表中选择：",
        "en": "Select from open applications:",
    },
    "bind_custom_proc_prompt": {
        "zh": "目标进程名 (例如 notepad.exe):",
        "en": "Target process name (e.g. notepad.exe):",
    },
    "bind_custom_title_prompt": {
        "zh": "窗口标题包含字符 (可选，留空匹配所有):",
        "en": "Window title filter (Optional, leave blank to match all):",
    },
    "reset_preset_success": {
        "zh": "已成功将“{layout}”恢复为官方预设！",
        "en": "Layout [{layout}] successfully reset to presets!",
    },
    "backup_failed": {
        "zh": "无法创建配置备份。",
        "en": "Failed to create configuration backup.",
    },
    "empty_slot_tooltip": {
        "zh": "点击创建此槽位按钮，或将其他按钮拖放到此处",
        "en": "Click to create button here, or drag another button here",
    },
}


def get_current_language() -> str:
    """Return currently active language code."""
    global _CURRENT_LANG
    return _CURRENT_LANG


def set_current_language(lang: str):
    """Set currently active language code ('zh' or 'en')."""
    global _CURRENT_LANG
    if lang in (LANG_ZH, LANG_EN):
        _CURRENT_LANG = lang


def tr(key: str, lang: Optional[str] = None, **kwargs) -> str:
    """Translate key to specified or current language with optional string formatting."""
    target_lang = lang or _CURRENT_LANG
    entry = TRANSLATIONS.get(key)
    if not entry:
        return key
    text = entry.get(target_lang, entry.get(LANG_ZH, key))
    if kwargs:
        try:
            return text.format(**kwargs)
        except Exception:
            return text
    return text


def get_layout_display_name(lid: str, default_name: str = "") -> str:
    """Return localized display name for a preset layout if available, or its custom name."""
    key = f"layout_name_{lid}"
    val = tr(key)
    if val != key:
        return val
    return default_name or lid
