from __future__ import annotations;

import copy;
import math;
from typing import Optional, Tuple, Type, TypeVar, TYPE_CHECKING, Union;

from render_order import RenderOrder;

if TYPE_CHECKING:
    from game_map import GameMap;
    from components.ai import BaseAI;
    from components.consumable import Consumable;
    from components.equippable import Equippable;
    from components.equipment import Equipment;
    from components.inventory import Inventory;
    from components.level import Level;
    from components.fighter import Fighter;
    from components.attributes import Attributes;

T = TypeVar("T", bound="Entity");

class Entity:
    """
    A generic object representing any entity, such as the player, enemies, items, etc.
    """
    parent: Union[GameMap, Inventory];

    def __init__(
            self,
            parent: Optional[GameMap] = None,
            x: int = 0,
            y: int = 0,
            char: str = "?",
            color: Tuple[int, int, int] = (255, 255, 255),
            name: str = "<Unnamed>",
            description: str = "<No Description>",
            blocks_movement: bool = False,
            render_order: RenderOrder = RenderOrder.CORPSE,
            inventory: Optional[Inventory] = None
        ):
        self.x = x;
        self.y = y;
        self.char = char;
        self.color = color;
        self.name = name;
        self.description=description;
        self.blocks_movement = blocks_movement;
        self.render_order = render_order;
        self.inventory = inventory;
        if self.inventory:
            self.inventory.parent = self;

        if parent:
            # If the gamemap is not provided now then it will be set later.
            self.parent = parent;
            parent.entities.add(self);

    @property
    def gamemap(self) -> GameMap:
        return self.parent.gamemap;

    def spawn(self: T, gamemap: GameMap, x: int, y: int) -> T:
        """ Spawn a copy of this instance at the given location. """
        clone = copy.deepcopy(self);
        clone.x = x;
        clone.y = y;
        clone.parent = gamemap;
        gamemap.entities.add(clone);
        return clone;

    def place(self, x: int, y: int, gamemap: Optional[GameMap] = None) -> None:
        """Place this entity at a new location. Handles moving across GameMaps."""
        self.x = x;
        self.y = y;
        if gamemap:
            if hasattr(self, "parent"): # Possibly uninitialized.
                if self.parent is self.gamemap:
                    self.gamemap.entities.remove(self);
            self.parent = gamemap;
            gamemap.entities.add(self);

    def distance_to(self, x: int, y: int) -> float:
        """
        Return the distance between the current entity and the given (x, y) coordinate.
        """
        return math.sqrt((x - self.x) ** 2 + (y - self.y) ** 2);

    def move(self, dx: int, dy: int) -> None:
        self.x += dx;
        self.y += dy;

class Item(Entity):
    def __init__(
        self,
        *,
        x: int = 0,
        y: int = 0,
        char: str = "?",
        color: Tuple[int, int, int] = (255, 255, 255),
        name: str = "<Unnamed>",
        description: str = "<No Description>",
        consumable: Optional[Consumable] = None,
        equippable: Optional[Equippable] = None,
    ):
        super().__init__(
            x=x,
            y=y,
            char=char,
            color=color,
            name=name,
            description=description,
            blocks_movement=False,
            render_order=RenderOrder.ITEM,
        );

        self.consumable = consumable;

        if self.consumable:
            self.consumable.parent = self;

        self.equippable = equippable;

        if self.equippable:
            self.equippable.parent = self;

class Actor(Entity):
    def __init__(
            self,
            *,
            x: int = 0,
            y: int = 0,
            char: str = "?",
            color: Tuple[int, int, int] = (255, 255, 255),
            name: str = "<Unnamed>",
            description: str = "<No Description>",
            blocks_movement: bool = True,
            ai_cls: Type[BaseAI],
            equipment: Equipment,
            fighter: Fighter,
            inventory: Inventory,
            level: Level,
            dialogue: Dialogue,
            attributes: Attributes
    ):
        super().__init__(
            x=x,
            y=y,
            char=char,
            color=color,
            name=name,
            description=description,
            blocks_movement=True,
            render_order=RenderOrder.ACTOR,
            inventory=inventory
        );

        self.ai: Optional[BaseAI] = ai_cls(self);

        self.equipment = equipment;
        self.equipment.parent = self;

        self.fighter = fighter;
        self.fighter.parent = self;

        self.inventory = inventory;
        self.inventory.parent = self;

        self.level = level;
        self.level.parent = self;

        self.dialogue = dialogue;
        self.dialogue.parent = self;

        self.attributes = attributes;
        self.attributes.parent = self;

    @property
    def is_alive(self) -> bool:
        """Returns True as long as this actor can perform actions."""
        return bool(self.ai);
