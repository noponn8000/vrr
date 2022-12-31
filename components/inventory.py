from __future__ import annotations;

from typing import List, TYPE_CHECKING;
import copy;

from components.base_component import BaseComponent;

if TYPE_CHECKING:
    from entity import Actor, Item;

class Slot:
    def __init__(self, item: Item, count: int = 1, stack: bool = True):
        self.item = item;
        self.count = count;
        self.stack = stack;

class Inventory(BaseComponent):
    parent: Actor;

    def __init__(self, capacity: int, items: List[Slot] = [], accessible: bool = False):
        self.capacity = capacity;
        self.items = items;
        self.accessible = accessible;

    def add(self, item: Item, quantity: int = 1) -> None:
        for slot in self.items:
            if item.name == slot.item.name:
                if slot.stack:
                    slot.count += quantity;
                else:
                    for i in range(quantity):
                        self.items.append(Slot(item, quantity));
                return;

        self.items.append(Slot(item, quantity));

    def drop(self, item: Item, quantity: int = 1) -> None:
        """ Removes an item from the inventory and restores it to the game map, at the player's location.
        """
        for slot in self.items:
            if item.name == slot.item.name:
               if quantity >= slot.count:
                   self.items.remove(slot);
                   quantity = slot.count;
               else:
                   slot.count -= quantity;

               for i in range(quantity):
                   copy.deepcopy(item).place(self.parent.x, self.parent.y, self.gamemap);
                   self.engine.message_log.add_message(f"You drop the {item.name}");

    def remove(self, item: Item, quantity: int = 1) -> None:
        for slot in self.items:
            if item.name == slot.item.name:
               if quantity >= slot.count:
                   self.items.remove(slot);
                   quantity = slot.count;
               else:
                   slot.count -= quantity;
