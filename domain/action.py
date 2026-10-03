# -*- coding: utf-8 -*-
"""Action domain model and step definitions."""

from dataclasses import dataclass, field
from typing import List, Dict, Any, Optional
import copy


VALID_STEP_TYPES = {
    "text",
    "key",
    "hotkey",
    "delay",
    "paste",
    "variable",
    "repeat",
    "mouse",
}

VALID_VARIABLES = {
    "clipboard",
    "date",
    "time",
    "counter",
    "app_name",
}


@dataclass
class ActionStep:
    """Represents an atomic execution step in an action/macro."""
    type: str
    value: str = ""
    key: str = ""
    hotkey: str = ""
    keys: List[str] = field(default_factory=list)
    ms: int = 50
    name: str = ""
    count: int = 1
    steps: List["ActionStep"] = field(default_factory=list)
    mouse_action: str = "click"  # click, dblclick, rclick, move
    x: Optional[int] = None
    y: Optional[int] = None

    def validate(self) -> List[str]:
        errors = []
        if self.type not in VALID_STEP_TYPES:
            errors.append(f"Invalid step type: '{self.type}'. Allowed: {sorted(VALID_STEP_TYPES)}")
            return errors

        if self.type == "text" and not isinstance(self.value, str):
            errors.append("Step 'text' requires string 'value'")
        elif self.type == "key" and not self.key:
            errors.append("Step 'key' requires non-empty 'key'")
        elif self.type == "hotkey":
            if not self.hotkey and not self.keys:
                errors.append("Step 'hotkey' requires 'hotkey' string or 'keys' list")
        elif self.type == "delay":
            if not isinstance(self.ms, (int, float)) or self.ms < 0:
                errors.append("Step 'delay' requires non-negative number 'ms'")
        elif self.type == "paste" and not isinstance(self.value, str):
            errors.append("Step 'paste' requires string 'value'")
        elif self.type == "variable":
            if not self.name or self.name.lower() not in VALID_VARIABLES:
                errors.append(f"Step 'variable' requires valid 'name' in {sorted(VALID_VARIABLES)}")
        elif self.type == "repeat":
            if self.count < 1:
                errors.append("Step 'repeat' requires count >= 1")
            for sub_step in self.steps:
                errors.extend(sub_step.validate())
        return errors

    def to_dict(self) -> Dict[str, Any]:
        data: Dict[str, Any] = {"type": self.type}
        if self.type == "text":
            data["value"] = self.value
        elif self.type == "key":
            data["key"] = self.key
        elif self.type == "hotkey":
            if self.hotkey:
                data["hotkey"] = self.hotkey
            if self.keys:
                data["keys"] = list(self.keys)
        elif self.type == "delay":
            data["ms"] = int(self.ms)
        elif self.type == "paste":
            data["value"] = self.value
        elif self.type == "variable":
            data["name"] = self.name
        elif self.type == "repeat":
            data["count"] = self.count
            data["steps"] = [s.to_dict() for s in self.steps]
        elif self.type == "mouse":
            data["mouse_action"] = self.mouse_action
            if self.x is not None:
                data["x"] = self.x
            if self.y is not None:
                data["y"] = self.y
        return data

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "ActionStep":
        step_type = data.get("type", "text")
        sub_steps: List[ActionStep] = []
        if step_type == "repeat" and "steps" in data:
            sub_steps = [cls.from_dict(s) for s in data["steps"] if isinstance(s, dict)]

        raw_keys = data.get("keys", [])
        if isinstance(raw_keys, str):
            keys = [k.strip() for k in raw_keys.split("+") if k.strip()]
        else:
            keys = list(raw_keys)

        return cls(
            type=step_type,
            value=str(data.get("value", "")),
            key=str(data.get("key", "")),
            hotkey=str(data.get("hotkey", "")),
            keys=keys,
            ms=int(data.get("ms", 50)),
            name=str(data.get("name", "")),
            count=int(data.get("count", 1)),
            steps=sub_steps,
            mouse_action=str(data.get("mouse_action", "click")),
            x=data.get("x"),
            y=data.get("y"),
        )


@dataclass
class Action:
    """Action definition containing identity, display attributes, and steps."""
    id: str
    label: str
    description: str = ""
    icon: str = ""
    color: str = ""
    steps: List[ActionStep] = field(default_factory=list)
    on_error: str = "stop"  # "stop" or "continue"
    confirm: bool = False
    auto_enter: bool = False

    def validate(self) -> List[str]:
        errors = []
        if not self.id or not isinstance(self.id, str):
            errors.append("Action 'id' must be a non-empty string")
        if not self.label or not isinstance(self.label, str):
            errors.append("Action 'label' must be a non-empty string")
        if self.on_error not in ("stop", "continue"):
            errors.append("Action 'on_error' must be 'stop' or 'continue'")
        for idx, step in enumerate(self.steps):
            step_errs = step.validate()
            for err in step_errs:
                errors.append(f"Step #{idx + 1}: {err}")
        return errors

    def to_dict(self) -> Dict[str, Any]:
        return {
            "id": self.id,
            "label": self.label,
            "description": self.description,
            "icon": self.icon,
            "color": self.color,
            "steps": [s.to_dict() for s in self.steps],
            "on_error": self.on_error,
            "confirm": bool(self.confirm),
            "auto_enter": bool(self.auto_enter),
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "Action":
        raw_steps = data.get("steps", [])
        steps = [ActionStep.from_dict(s) for s in raw_steps if isinstance(s, dict)]
        return cls(
            id=str(data.get("id", "")),
            label=str(data.get("label", "")),
            description=str(data.get("description", "")),
            icon=str(data.get("icon", "")),
            color=str(data.get("color", "")),
            steps=steps,
            on_error=str(data.get("on_error", "stop")),
            confirm=bool(data.get("confirm", False)),
            auto_enter=bool(data.get("auto_enter", False)),
        )

    def clone(self, new_id: Optional[str] = None) -> "Action":
        copied = copy.deepcopy(self)
        if new_id:
            copied.id = new_id
        return copied
