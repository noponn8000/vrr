from __future__ import annotations;

from typing import Optional, TYPE_CHECKING;

from components.base_component import BaseComponent;
from equipment_types import EquipmentType;

if TYPE_CHECKING:
    from entity import Actor, Item;

class Equipment(BaseComponent):
    parent: Actor;

    def __init__(self, slots: Dict[str, item]={"weapon": None, "armor": None}):
        self.slots = slots;

    def get_item_in_slot(self, slot: str) -> Optional[Item]:
        try:
            return self.slots[slot];
        except KeyError:
            return None;

    def get_equipment_of_type(eq_type: EquipmentType) -> List[Item]:
        items = [];
        for slot, item in self.slots.items():
            if item.equipment.equipment_type == eq_type:
                items.append(item);

    @property
    def defense_bonus(self) -> int:
        bonus = 0;

        for _slot, item in self.slots.items():
            if item:
                bonus += item.equippable.defense_bonus;

        return bonus;

    def item_is_equipped(self, item: Item) -> bool:
        return item in self.slots.values();

    def unequip_message(self, item_name: str) -> None:
        self.parent.gamemap.engine.message_log.add_message(
            f"You remove the {item_name}."
        );

    def equip_message(self, item_name: str) -> None:
        self.parent.gamemap.engine.message_log.add_message(
            f"You equip the {item_name}."
        );

    def equip_to_slot(self, slot: str, item: Item, add_message: bool) -> None:
        current_item = self.slots[slot];

        if current_item is not None:
            self.unequip_from_slot(slot, add_message);

        self.slots[slot] = item;

        if add_message:
            self.equip_message(item.name);

    def unequip_from_slot(self, slot: str, add_message: bool) -> None:
        current_item = self.slots[slot];

        if add_message:
            self.unequip_message(current_item.name);

        self.slots[slot] = None;

    def toggle_equip(self, equippable_item: Item, add_message: bool = True) -> None:
        if equippable_item.equippable:
            match equippable_item.equippable.equipment_type:
                case EquipmentType.WEAPON:
                    slot = "weapon";
                case EquipmentType.ARMOR:
                    slot = "armor";

        if self.slots[slot] == equippable_item:
            self.unequip_from_slot(slot, add_message);
        else:
            self.equip_to_slot(slot, equippable_item, add_message);
