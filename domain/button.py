# -*- coding: utf-8 -*-
"""Button domain model."""

from dataclasses import dataclass
from typing import Dict, Any, Optional, List
import copy


def format_button_display_text(icon: str, label: str) -> str:
    """Format button display text cleanly, preventing duplicate icon characters."""
    icon = (icon or "").strip()
    label = label or ""
    if not icon:
        return label
    clean_label = label.strip()
    if not clean_label:
        return icon
    first_line = clean_label.split("\n")[0].strip()
    if icon in first_line or clean_label.startswith(icon):
        return label
    first_token = clean_label.split()[0] if clean_label.split() else ""
    if first_token == icon:
        return label
    return f"{icon} {label}".strip()


@dataclass
class Button:
    """Represents a button on the floating keyboard panel."""
    id: str
    label: str
    action_id: str
    icon: str = ""
    color: str = ""
    tooltip: str = ""
    auto_enter: Optional[bool] = None  # None = use global or action setting

    @property
    def display_text(self) -> str:
        return format_button_display_text(self.icon, self.label)

    def validate(self) -> List[str]:
        errors = []
        if not self.id:
            errors.append("Button 'id' must be non-empty")
        if not self.label:
            errors.append("Button 'label' must be non-empty")
        if not self.action_id:
            errors.append("Button 'action_id' must be non-empty")
        return errors

    def to_dict(self) -> Dict[str, Any]:
        data: Dict[str, Any] = {
            "id": self.id,
            "label": self.label,
            "action_id": self.action_id,
            "icon": self.icon,
            "color": self.color,
            "tooltip": self.tooltip,
        }
        if self.auto_enter is not None:
            data["auto_enter"] = self.auto_enter
        return data

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "Button":
        label = str(data.get("label", ""))
        icon = str(data.get("icon", "")).strip()
        if not label and icon:
            label = icon
            icon = ""
        elif icon:
            first_line = label.strip().split("\n")[0].strip() if label.strip() else ""
            if icon in first_line or label.startswith(icon) or (label.split() and label.split()[0] == icon):
                icon = ""
        return cls(
            id=str(data.get("id", "")),
            label=label,
            action_id=str(data.get("action_id", "")),
            icon=icon,
            color=str(data.get("color", "")),
            tooltip=str(data.get("tooltip", "")),
            auto_enter=data.get("auto_enter", None),
        )

    def clone(self, new_id: Optional[str] = None) -> "Button":
        copied = copy.deepcopy(self)
        if new_id:
            copied.id = new_id
        return copied
