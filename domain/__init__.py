# -*- coding: utf-8 -*-
"""Domain package for QuickInput."""

from .action import Action, ActionStep, VALID_STEP_TYPES, VALID_VARIABLES
from .button import Button, COLOR_PRESET_KEYS, COLOR_PRESETS, format_button_display_text
from .layout import Layout, LayoutSettings, LayoutButtonSlot
from .profile import Profile
from .i18n import tr, get_current_language, set_current_language

# Backward-compatible alias
ButtonSlot = LayoutButtonSlot

__all__ = [
    "Action",
    "ActionStep",
    "VALID_STEP_TYPES",
    "VALID_VARIABLES",
    "Button",
    "COLOR_PRESET_KEYS",
    "COLOR_PRESETS",
    "format_button_display_text",
    "Layout",
    "LayoutSettings",
    "LayoutButtonSlot",
    "ButtonSlot",
    "Profile",
    "tr",
    "get_current_language",
    "set_current_language",
]
