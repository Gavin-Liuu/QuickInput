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

    # Settings - Layouts Tab
    "layout_select_label": {
        "zh": "当前编辑布局:",
        "en": "Current Layout:",
    },
    "btn_new_layout": {
        "zh": "＋ 新建布局…",
        "en": "+ New Layout…",
    },
    "btn_del_layout": {
        "zh": "删除布局",
        "en": "Delete Layout",
    },
    "btn_export_pack": {
        "zh": "导出场景包…",
        "en": "Export Pack…",
    },
    "btn_import_pack": {
        "zh": "导入场景包…",
        "en": "Import Pack…",
    },
    "preview_box_title": {
        "zh": "布局预览 (点击网格编辑按钮，拖拽可交换位置)",
        "en": "Layout Preview (Click to edit button, drag to swap)",
    },
    "btn_transpose": {
        "zh": "⇄ 行列转换",
        "en": "⇄ Transpose",
    },
    "btn_transpose_tip": {
        "zh": "旋转转换布局的行数与列数（转置网格）",
        "en": "Transpose layout rows and columns",
    },
    "layout_props_title": {
        "zh": "布局属性与全局默认值",
        "en": "Layout Properties & Global Defaults",
    },
    "rows_label": {
        "zh": "行数 (1-20)",
        "en": "Rows (1-20)",
    },
    "cols_label": {
        "zh": "列数 (1-20)",
        "en": "Columns (1-20)",
    },
    "btn_size_label": {
        "zh": "默认按钮尺寸",
        "en": "Default Button Size",
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
        "zh": "窗口透明度",
        "en": "Window Opacity",
    },
    "always_on_top_chk": {
        "zh": "窗口置顶",
        "en": "Always on Top",
    },
    "confirm_action_chk": {
        "zh": "执行危险操作前弹窗二次确认",
        "en": "Confirm before executing risky actions",
    },
    "auto_enter_chk": {
        "zh": "发送动作后默认自动追加回车 (Enter)",
        "en": "Auto append Enter after action by default",
    },

    # Button Properties
    "btn_props_title": {
        "zh": "选中按钮属性",
        "en": "Selected Button Properties",
    },
    "btn_text_label": {
        "zh": "显示文字",
        "en": "Display Text",
    },
    "btn_color_label": {
        "zh": "按钮颜色",
        "en": "Button Color",
    },
    "btn_tooltip_label": {
        "zh": "悬停提示",
        "en": "Tooltip",
    },

    # Action Steps Box (Renamed from Macro Steps)
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
    "btn_record_macro": {
        "zh": "⏺ 录制宏…",
        "en": "⏺ Record Macro…",
    },
    "btn_add_text": {
        "zh": "＋ 文本",
        "en": "+ Text",
    },
    "btn_add_text_tip": {
        "zh": "添加文本输入步骤 (剪贴板极速无损粘贴)",
        "en": "Add text input step (Lossless clipboard paste)",
    },
    "btn_add_key": {
        "zh": "＋ 按键",
        "en": "+ Key",
    },
    "btn_add_key_tip": {
        "zh": "点击录制单键或组合快捷键 (支持 Enter、Ctrl、Alt、Shift 任意组合)",
        "en": "Click to record key or hotkey (supports Enter, Ctrl, Alt, Shift combinations)",
    },
    "btn_add_delay": {
        "zh": "＋ 等待",
        "en": "+ Delay",
    },
    "btn_add_delay_tip": {
        "zh": "添加延时等待毫秒步骤",
        "en": "Add delay (milliseconds) step",
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
    "btn_move_down": {
        "zh": "▼ 下移",
        "en": "▼ Move Down",
    },

    # App Binding Box
    "app_binding_title": {
        "zh": "应用绑定 (切到指定软件时自动启用当前布局)",
        "en": "App Binding (Auto switch to current layout when target focused)",
    },
    "bind_col_process": {
        "zh": "进程名",
        "en": "Process Name",
    },
    "bind_col_title": {
        "zh": "窗口标题包含",
        "en": "Window Title Contains",
    },
    "btn_bind_current": {
        "zh": "🎯 绑定目标应用",
        "en": "🎯 Bind Target App",
    },
    "btn_bind_custom": {
        "zh": "＋ 手动添加进程",
        "en": "+ Add Process Manually",
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
        "zh": "界面语言 (Language)",
        "en": "Interface Language",
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
        "zh": "场景切换",
        "en": "Scene Switching",
    },
    "auto_profile_switch_chk": {
        "zh": "根据前台活动窗口自动切换布局",
        "en": "Auto switch layout based on foreground window",
    },
    "toggle_hotkey_label": {
        "zh": "显示/隐藏工作台",
        "en": "Show/Hide Workbench",
    },
    "stop_hotkey_label": {
        "zh": "紧急停止宏快捷键",
        "en": "Emergency Stop Hotkey",
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
    "target_diag_label": {
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

    # Key Capture Dialog
    "key_capture_title": {
        "zh": "按键与组合键录制",
        "en": "Key & Hotkey Recording",
    },
    "key_capture_instruction": {
        "zh": "请在下方直接按下按键或快捷组合键：\n(提示：按 Enter 键会直接录制为 Enter 键，请在确认无误后点击下方【确定】按钮保存)",
        "en": "Press any key or shortcut combination below:\n(Note: Pressing Enter will record the Enter key. Click [OK] with mouse when done)",
    },
    "key_capture_input_placeholder": {
        "zh": "在此按下任意按键或组合键 (例如 ALT+= 或 ENTER)…",
        "en": "Press any key or hotkey here (e.g. ALT+= or ENTER)…",
    },
    "btn_ok": {
        "zh": "确定",
        "en": "OK",
    },
    "btn_clear": {
        "zh": "清除",
        "en": "Clear",
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
