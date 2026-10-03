# -*- coding: utf-8 -*-
"""Profile domain model for auto-binding layouts to applications."""

from dataclasses import dataclass
from typing import Dict, Any, List, Optional
import copy


@dataclass
class Profile:
    """Rules for automatically selecting a layout based on active target application."""
    process: str = ""
    window_title_contains: str = ""
    layout_id: str = ""
    id: str = ""
    name: str = ""
    enabled: bool = True

    def matches(self, process_name: str, window_title: str) -> bool:
        if not self.enabled:
            return False
        
        proc_match = True
        if self.process:
            proc_match = self.process.lower() in (process_name or "").lower()
            
        title_match = True
        if self.window_title_contains:
            title_match = self.window_title_contains.lower() in (window_title or "").lower()
            
        # Must have at least one condition specified to match
        if not self.process and not self.window_title_contains:
            return False
            
        return proc_match and title_match

    def validate(self) -> List[str]:
        errors = []
        if not self.layout_id:
            errors.append("Profile 'layout_id' must be non-empty")
        if not self.process and not self.window_title_contains:
            errors.append("Profile must specify at least 'process' or 'window_title_contains'")
        return errors

    def to_dict(self) -> Dict[str, Any]:
        return {
            "id": self.id,
            "name": self.name,
            "process": self.process,
            "window_title_contains": self.window_title_contains,
            "layout_id": self.layout_id,
            "enabled": self.enabled,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "Profile":
        return cls(
            id=str(data.get("id", "")),
            name=str(data.get("name", "")),
            process=str(data.get("process", "")),
            window_title_contains=str(data.get("window_title_contains", "")),
            layout_id=str(data.get("layout_id", "")),
            enabled=bool(data.get("enabled", True)),
        )

    def clone(self, new_id: Optional[str] = None) -> "Profile":
        copied = copy.deepcopy(self)
        if new_id:
            copied.id = new_id
        return copied
