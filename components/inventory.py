from __future__ import annotations;

from typing import List, TYPE_CHECKING;

from components.base_component import BaseComponent;

if TYPE_CHECKING:
    from entity import Actor, Item;

class Inventory(BaseComponent):
    parent: Actor;

    def __init__(self, capacity: int, items: List[Item] = []):
        self.capacity = capacity;
        self.items = items;

    def drop(self, item: Item) -> None:
        """ Removes an item from the inventory and restores it to the game map, at the player's location.
        """
        self.items.remove(item);
        item.place(self.parent.x, self.parent.y, self.gamemap);

        self.engine.message_log.add_message(f"You drop the {item.name}");

