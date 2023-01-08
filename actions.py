from __future__ import annotations;

import numpy as np;

from typing import Optional, Tuple, TYPE_CHECKING;

import color;
import exceptions;

if TYPE_CHECKING:
    from engine import Engine;
    from entity import Actor, Entity, Item;

class Action:
    def __init__(self, entity: Actor) -> None:
        super().__init__();
        self.entity = entity;

    @property
    def engine(self) -> Engine:
        """ Return the engine this action belongs to. """
        return self.entity.gamemap.engine;

    def perform(self) -> None:
        """
        Perform this action with the objects needed to determine its scope.
        This method must be overriden by Action subclasses.
        """
        raise NotImplementedError();

class PickupAction(Action):
    """Pickup an item and add it to the inventory, if there is room for it."""

    def __init__(self, entity: Actor):
        super().__init__(entity);

    def perform(self) -> None:
        actor_location_x = self.entity.x;
        actor_location_y = self.entity.y;
        inventory = self.entity.inventory;

        for item in self.engine.game_map.items:
            if actor_location_x == item.x and actor_location_y == item.y:
                if len(inventory.items) >= inventory.capacity:
                    raise exceptions.Impossible("Your inventory is full.");

                self.engine.game_map.entities.remove(item);
                item.parent = self.entity.inventory;
                inventory.add(item);

                self.engine.message_log.add_message(f"You pick up the {item.name}.");
                return;

        raise exceptions.Impossible("There is nothing here to pick up.");

class ItemAction(Action):
    def __init__(
        self, entity: Actor, item: Item, target_xy: Optional[Tuple[int, int]]=None
    ):
        super().__init__(entity);
        self.item = item;
        if not target_xy:
            target_xy = entity.x, entity.y;
        self.target_xy = target_xy;

    @property
    def target_actor(self) -> Optional[Actor]:
        """Return the actor at this action's destination."""
        return self.engine.game_map.get_actor_at_location(*self.target_xy);

    def perform(self) -> None:
        """Invoke the item's ability, this action will be given to provide context."""
        if self.item.consumable:
            self.item.consumable.activate(self);

class EquipAction(Action):
    def __init__(self, entity: Actor, item: Item):
        super().__init__(entity);

        self.item = item;

    def perform(self) -> None:
        self.entity.equipment.toggle_equip(self.item);

class DropItemAction(ItemAction):
    def perform(self) -> None:
        if self.entity.equipment.item_is_equipped(self.item):
            self.entity.equipment.toggle_equip(self.item);

        self.entity.inventory.drop(self.item);

class WaitAction(Action):
    def perform(self) -> None:
        pass;

class TakeStairsAction(Action):
    def perform(self) -> None:
        raise NotImplementedError();

class TakeDownStairsAction(TakeStairsAction):
    def perform(self) -> None:
        """
        Take the stairs leading up, if any exist at the entity's location.
        """
        if self.engine.game_map.tiles["name"][self.entity.x, self.entity.y].decode() == "staircase down":
            self.engine.game_world.next_floor();
            self.engine.message_log.add_message(
                "You descend through the staircase.", color.descend
            );
        else:
            raise exceptions.Impossible("There are no stairs leading down here.");

class TakeUpStairsAction(TakeStairsAction):
    def perform(self) -> None:
        """
        Take the stairs leading down, if any exist at the entity's location.
        """
        if self.engine.game_map.tiles["name"][self.entity.x, self.entity.y].decode() == "staircase up":
            self.engine.game_world.previous_floor();

            self.engine.message_log.add_message(
                "You ascend through the staircase.", color.descend
            );
        else:
            raise exceptions.Impossible("There are no stairs here.");

class ActionWithDirection(Action):
    def __init__(self, entity: Actor, dx: int, dy: int):
        super().__init__(entity);
        self.dx = dx;
        self.dy = dy;

    @property
    def dest_xy(self) -> Tuple[int, int]:
        """Returns this action's destination."""
        return self.entity.x + self.dx, self.entity.y + self.dy;
    
    @property
    def blocking_entity(self) -> Optional[Entity]:
        """Returns the blocking entity at this action's destination."""
        return self.engine.game_map.get_blocking_entity_at_location(*self.dest_xy);

    @property
    def target_actor(self) -> Optional[Actor]:
        """Return the actor at this action's destination."""
        return self.engine.game_map.get_actor_at_location(*self.dest_xy);

    def perform(self) -> None:
        raise NotImplementedError();

class MeleeAction(ActionWithDirection):
    def perform(self) -> None:
        target = self.target_actor;

        if not target:
            raise exceptions.Impossible("Nothing to attack.");

        if self.entity.equipment.get_item_in_slot("weapon"):
            damage = self.entity.equipment.get_item_in_slot("weapon").equippable.calculate_damage(self.entity.fighter.power, target.fighter.defense);
        else:
            damage = self.entity.fighter.power - target.fighter.defense;

        attack_desc = f"{self.entity.name.capitalize()} attacks {target.name}";
        if self.entity is self.engine.player:
            attack_color = color.player_atk;
        else:
            attack_color = color.enemy_atk;

        if damage > 0:
            self.engine.message_log.add_message(
                    f"{attack_desc} for {damage} hit points.", attack_color
            );
            target.fighter.hp -= damage;
        else:
            self.engine.message_log.add_message(
                    f"{attack_desc} but does no damage.", attack_color
            );

class MovementAction(ActionWithDirection):
    def perform(self) -> None:
        dest_x, dest_y = self.dest_xy;

        if not self.engine.game_map.in_bounds(dest_x, dest_y):
            # Destination is out of bounds.
            raise exceptions.Impossible("You cannot go that way.");
        if not self.engine.game_map.tiles["walkable"][dest_x, dest_y]:
            # Destination is blocked by a tile.
            tile_name = self.engine.game_map.tiles["name"][dest_x, dest_y].decode();
            raise exceptions.Impossible(f"That way is blocked by a {tile_name}.");

        blocking_entity = self.engine.game_map.get_blocking_entity_at_location(dest_x, dest_y); 
        if blocking_entity:
            # Destination is blocked by an entity.
            raise exceptions.Impossible(f"That way is blocked by {blocking_entity.name}");

        entities_at_dest = self.engine.game_map.get_entities_at_location(dest_x, dest_y);
        entities_at_dest_str = [entity.name for entity in entities_at_dest];

        if len(entities_at_dest) > 0:
            entities_str = ", ".join(entities_at_dest_str);
            self.engine.message_log.add_message(f"You pass by {entities_str}.");

        self.entity.move(self.dx, self.dy);
        
class BumpAction(ActionWithDirection):
    def perform(self) -> None:
        if self.target_actor:
            return MeleeAction(self.entity, self.dx, self.dy).perform();
        else:
            return MovementAction(self.entity, self.dx, self.dy).perform();
