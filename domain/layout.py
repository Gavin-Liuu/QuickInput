# -*- coding: utf-8 -*-
"""Layout domain model."""

from dataclasses import dataclass, field
from typing import List, Dict, Any, Optional
import copy


@dataclass
class LayoutButtonSlot:
    """Position of a button in the layout grid."""
    button_id: str
    row: int
    column: int

    def to_dict(self) -> Dict[str, Any]:
        return {
            "button_id": self.button_id,
            "row": self.row,
            "column": self.column,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "LayoutButtonSlot":
        return cls(
            button_id=str(data.get("button_id", "")),
            row=int(data.get("row", 0)),
            column=int(data.get("column", 0)),
        )


@dataclass
class LayoutSettings:
    """Per-layout display and interaction settings."""
    opacity: float = 0.95
    show_labels: bool = True
    button_size: str = "compact"  # "compact", "standard", "touch"
    always_on_top: bool = True
    auto_enter_default: bool = False
    confirm_before_action: bool = False
    window_width: Optional[int] = None
    window_height: Optional[int] = None

    def to_dict(self) -> Dict[str, Any]:
        data = {
            "opacity": float(self.opacity),
            "show_labels": bool(self.show_labels),
            "button_size": str(self.button_size),
            "always_on_top": bool(self.always_on_top),
            "auto_enter_default": bool(self.auto_enter_default),
            "confirm_before_action": bool(self.confirm_before_action),
        }
        if self.window_width is not None:
            data["window_width"] = int(self.window_width)
        if self.window_height is not None:
            data["window_height"] = int(self.window_height)
        return data

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "LayoutSettings":
        w_w = data.get("window_width")
        w_h = data.get("window_height")
        return cls(
            opacity=float(data.get("opacity", 0.95)),
            show_labels=bool(data.get("show_labels", True)),
            button_size=str(data.get("button_size", "compact")),
            always_on_top=bool(data.get("always_on_top", True)),
            auto_enter_default=bool(data.get("auto_enter_default", False)),
            confirm_before_action=bool(data.get("confirm_before_action", False)),
            window_width=int(w_w) if w_w is not None else None,
            window_height=int(w_h) if w_h is not None else None,
        )


@dataclass
class Layout:
    """Defines a full keyboard layout with grid arrangement and buttons."""
    id: str
    name: str
    orientation: str = "horizontal"  # "horizontal" or "vertical"
    rows: int = 2
    columns: int = 7
    buttons: List[LayoutButtonSlot] = field(default_factory=list)
    settings: LayoutSettings = field(default_factory=LayoutSettings)
    description: str = ""

    def validate(self) -> List[str]:
        errors = []
        if not self.id:
            errors.append("Layout 'id' must be non-empty")
        if not self.name:
            errors.append("Layout 'name' must be non-empty")
        if self.orientation not in ("horizontal", "vertical"):
            errors.append("Layout 'orientation' must be 'horizontal' or 'vertical'")
        if self.rows < 1 or self.columns < 1:
            errors.append("Layout rows and columns must be >= 1")
        for slot in self.buttons:
            if not slot.button_id:
                errors.append("Button slot missing 'button_id'")
            if slot.row < 0 or slot.column < 0:
                errors.append(f"Button slot for '{slot.button_id}' has negative coordinates ({slot.row}, {slot.column})")
        return errors

    def get_slot_at(self, row: int, column: int) -> Optional[LayoutButtonSlot]:
        for slot in self.buttons:
            if slot.row == row and slot.column == column:
                return slot
        return None

    def get_button_at(self, row: int, column: int) -> Optional[str]:
        slot = self.get_slot_at(row, column)
        return slot.button_id if slot else None

    def set_button_at(self, row: int, column: int, button_id: str):
        slot = self.get_slot_at(row, column)
        if slot:
            slot.button_id = button_id
        else:
            self.buttons.append(LayoutButtonSlot(button_id=button_id, row=row, column=column))

    def remove_button_at(self, row: int, column: int) -> Optional[str]:
        for idx, slot in enumerate(self.buttons):
            if slot.row == row and slot.column == column:
                bid = slot.button_id
                del self.buttons[idx]
                return bid
        return None

    def swap_slots(self, r1: int, c1: int, r2: int, c2: int):
        slot1 = self.get_slot_at(r1, c1)
        slot2 = self.get_slot_at(r2, c2)
        if slot1 and slot2:
            slot1.row, slot2.row = r2, r1
            slot1.column, slot2.column = c2, c1
        elif slot1:
            slot1.row, slot1.column = r2, c2
        elif slot2:
            slot2.row, slot2.column = r1, c1

    def transpose(self):
        """Transpose the layout grid: swap rows and columns, and swap (r, c) of each button slot."""
        self.rows, self.columns = self.columns, self.rows
        self.orientation = "vertical" if self.rows > self.columns else "horizontal"
        for slot in self.buttons:
            slot.row, slot.column = slot.column, slot.row
        if self.settings.window_width is not None and self.settings.window_height is not None:
            self.settings.window_width, self.settings.window_height = (
                max(220, self.settings.window_height),
                max(60, self.settings.window_width),
            )

    def to_dict(self) -> Dict[str, Any]:
        return {
            "id": self.id,
            "name": self.name,
            "orientation": self.orientation,
            "rows": self.rows,
            "columns": self.columns,
            "buttons": [b.to_dict() for b in self.buttons],
            "settings": self.settings.to_dict(),
            "description": self.description,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "Layout":
        raw_buttons = data.get("buttons", [])
        buttons = [LayoutButtonSlot.from_dict(b) for b in raw_buttons if isinstance(b, dict)]
        raw_settings = data.get("settings", {})
        settings = LayoutSettings.from_dict(raw_settings if isinstance(raw_settings, dict) else {})
        return cls(
            id=str(data.get("id", "")),
            name=str(data.get("name", "")),
            orientation=str(data.get("orientation", "horizontal")),
            rows=int(data.get("rows", 2)),
            columns=int(data.get("columns", 7)),
            buttons=buttons,
            settings=settings,
            description=str(data.get("description", "")),
        )

    def clone(self, new_id: Optional[str] = None, new_name: Optional[str] = None) -> "Layout":
        copied = copy.deepcopy(self)
        if new_id:
            copied.id = new_id
        if new_name:
            copied.name = new_name
        return copied
