# -*- coding: utf-8 -*-
"""Layout Manager for handling layout switches, button/action lookups, and profile matching."""

from typing import Dict, List, Optional, Callable
from domain.action import Action
from domain.button import Button
from domain.layout import Layout
from domain.profile import Profile


class LayoutManager:
    """Manages active layouts, button sets, actions, profiles, and auto-switching."""

    def __init__(self):
        self.layouts: Dict[str, Layout] = {}
        self.buttons: Dict[str, Button] = {}
        self.actions: Dict[str, Action] = {}
        self.profiles: List[Profile] = []
        self.active_layout_id: str = ""
        self.recent_button_ids: List[str] = []

        self._on_layout_changed_callbacks: List[Callable[[Layout], None]] = []

    def add_layout_changed_listener(self, cb: Callable[[Layout], None]):
        self._on_layout_changed_callbacks.append(cb)

    def register_action(self, action: Action):
        self.actions[action.id] = action

    def register_button(self, button: Button):
        self.buttons[button.id] = button

    def register_layout(self, layout: Layout):
        self.layouts[layout.id] = layout
        if not self.active_layout_id:
            self.active_layout_id = layout.id

    def register_profile(self, profile: Profile):
        self.profiles.append(profile)

    def get_active_layout(self) -> Optional[Layout]:
        if not self.active_layout_id:
            if self.layouts:
                self.active_layout_id = next(iter(self.layouts))
            else:
                return None
        return self.layouts.get(self.active_layout_id)

    def set_active_layout(self, layout_id: str) -> bool:
        if layout_id in self.layouts and layout_id != self.active_layout_id:
            self.active_layout_id = layout_id
            layout = self.layouts[layout_id]
            for cb in self._on_layout_changed_callbacks:
                try:
                    cb(layout)
                except Exception:
                    pass
            return True
        return False

    def check_and_apply_profile(self, process_name: str, window_title: str) -> Optional[str]:
        """Matches active app against registered profiles. Returns layout_id if switched."""
        for profile in self.profiles:
            if profile.matches(process_name, window_title):
                target_layout_id = profile.layout_id
                if target_layout_id in self.layouts and target_layout_id != self.active_layout_id:
                    self.set_active_layout(target_layout_id)
                    return target_layout_id
        return None

    def record_button_click(self, button_id: str):
        if button_id in self.recent_button_ids:
            self.recent_button_ids.remove(button_id)
        self.recent_button_ids.insert(0, button_id)
        if len(self.recent_button_ids) > 20:
            self.recent_button_ids.pop()

    def get_button(self, button_id: str) -> Optional[Button]:
        return self.buttons.get(button_id)

    def get_action_for_button(self, button_id: str) -> Optional[Action]:
        btn = self.get_button(button_id)
        if btn and btn.action_id in self.actions:
            return self.actions[btn.action_id]
        return None

    def search_buttons(self, query: str) -> List[Button]:
        """Search buttons by label, tooltip, or action label."""
        q = (query or "").strip().lower()
        if not q:
            return list(self.buttons.values())

        results = []
        for btn in self.buttons.values():
            if q in btn.label.lower() or q in btn.tooltip.lower() or q in btn.id.lower():
                results.append(btn)
                continue
            act = self.actions.get(btn.action_id)
            if act and (q in act.label.lower() or q in act.description.lower()):
                results.append(btn)
        return results

    # CRUD
    def create_layout(self, layout: Layout):
        self.layouts[layout.id] = layout
        self.set_active_layout(layout.id)

    def create_layout_with_presets(
        self,
        layout_id: str,
        name: str,
        orientation: str = "horizontal",
        rows: int = 2,
        columns: int = 4,
        button_size: str = "compact",
    ) -> Layout:
        """Create a new layout pre-populated with clickable button slots."""
        from domain.layout import LayoutSettings, LayoutButtonSlot
        from domain.action import ActionStep

        settings = LayoutSettings(button_size=button_size)
        layout = Layout(
            id=layout_id,
            name=name,
            orientation=orientation,
            rows=rows,
            columns=columns,
            settings=settings,
        )
        idx = 1
        for r in range(rows):
            for c in range(columns):
                btn_id = f"{layout_id}_btn_{r}_{c}"
                while btn_id in self.buttons:
                    btn_id += "_1"
                act_id = f"{btn_id}_act"
                label = f"按钮 {idx}"
                action = Action(id=act_id, label=label, steps=[ActionStep(type="text", value=label)])
                button = Button(id=btn_id, label=label, action_id=act_id, color="#1976D2")
                self.register_action(action)
                self.register_button(button)
                layout.buttons.append(LayoutButtonSlot(button_id=btn_id, row=r, column=c))
                idx += 1
        self.register_layout(layout)
        self.set_active_layout(layout_id)
        return layout

    def create_button_for_slot(
        self, layout_id: str, row: int, column: int, label: str = "新按钮"
    ) -> Optional[Button]:
        from domain.action import ActionStep
        layout = self.layouts.get(layout_id)
        if not layout:
            return None
        btn_id = f"{layout_id}_btn_{row}_{column}"
        while btn_id in self.buttons:
            btn_id += "_1"
        act_id = f"{btn_id}_act"
        action = Action(id=act_id, label=label, steps=[ActionStep(type="text", value=label)])
        button = Button(id=btn_id, label=label, action_id=act_id, color="#1976D2")
        self.register_action(action)
        self.register_button(button)
        layout.set_button_at(row, column, btn_id)
        return button

    def remove_button_from_slot(self, layout_id: str, row: int, column: int) -> bool:
        layout = self.layouts.get(layout_id)
        if not layout:
            return False
        removed_id = layout.remove_button_at(row, column)
        if removed_id:
            # Check if used by any other slot
            is_used = False
            for lay in self.layouts.values():
                for s in lay.buttons:
                    if s.button_id == removed_id:
                        is_used = True
                        break
                if is_used:
                    break
            if not is_used and removed_id in self.buttons:
                btn = self.buttons.pop(removed_id, None)
                if btn and btn.action_id in self.actions:
                    act_used = any(b.action_id == btn.action_id for b in self.buttons.values())
                    if not act_used:
                        self.actions.pop(btn.action_id, None)
            return True
        return False

    def duplicate_layout(self, layout_id: str, new_id: str, new_name: str) -> Optional[Layout]:
        source = self.layouts.get(layout_id)
        if not source:
            return None
        import copy
        clone = source.clone(new_id=new_id, new_name=new_name)
        clone.settings = copy.deepcopy(source.settings)
        # A duplicated layout owns its button definitions. Existing packs use
        # a legacy global registry, so clone the referenced button/action pair
        # under internal storage keys while keeping the visible label intact.
        cloned_slots = []
        for index, slot in enumerate(clone.buttons, start=1):
            source_button = self.buttons.get(slot.button_id)
            if not source_button:
                cloned_slots.append(slot)
                continue
            new_button_id = f"{new_id}_button_{index}"
            while new_button_id in self.buttons:
                new_button_id += "_copy"
            new_action_id = f"{new_button_id}_action"
            button = source_button.clone(new_id=new_button_id)
            action = self.actions.get(source_button.action_id)
            if action:
                action = action.clone(new_id=new_action_id)
                button.action_id = new_action_id
                self.actions[new_action_id] = action
            self.buttons[new_button_id] = button
            slot.button_id = new_button_id
            cloned_slots.append(slot)
        clone.buttons = cloned_slots
        self.layouts[new_id] = clone
        return clone

    def get_buttons_for_layout(self, layout_id: Optional[str] = None) -> List[Button]:
        """Return only the button definitions used by one layout.

        This is the public API used by the settings UI. The global registry
        remains only as a backward-compatible storage index for old packs.
        """
        layout = self.layouts.get(layout_id or self.active_layout_id)
        if not layout:
            return []
        return [self.buttons[slot.button_id] for slot in layout.buttons if slot.button_id in self.buttons]

    def rename_layout(self, layout_id: str, new_name: str) -> bool:
        if layout_id in self.layouts:
            self.layouts[layout_id].name = new_name
            return True
        return False

    def delete_layout(self, layout_id: str) -> bool:
        if layout_id in self.layouts:
            if len(self.layouts) <= 1:
                return False  # Cannot delete the only layout
            layout = self.layouts[layout_id]
            # Clean up buttons and actions used by this layout that are not used by other layouts
            other_btn_ids = set()
            for other_id, other_lay in self.layouts.items():
                if other_id != layout_id:
                    for s in other_lay.buttons:
                        other_btn_ids.add(s.button_id)
            for s in layout.buttons:
                if s.button_id not in other_btn_ids and s.button_id in self.buttons:
                    btn = self.buttons.pop(s.button_id, None)
                    if btn and btn.action_id in self.actions:
                        act_used = any(b.action_id == btn.action_id for b in self.buttons.values())
                        if not act_used:
                            self.actions.pop(btn.action_id, None)
            del self.layouts[layout_id]
            if self.active_layout_id == layout_id:
                self.active_layout_id = next(iter(self.layouts))
                self.set_active_layout(self.active_layout_id)
            return True
        return False
