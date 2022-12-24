from __future__ import annotations;

from typing import Iterable, Iterator, Optional, TYPE_CHECKING;

import numpy as np;
from tcod.console import Console;

from entity import Actor, Item;
import tile_types;

if TYPE_CHECKING:
    from engine import Engine;
    from entity import Entity;

class GameMap:
    def __init__(self, engine: Engine, width: int, height: int, entities: Iterable[Entity]= ()):
        self.engine = engine;
        self.width, self.height = width, height;
        self.entities = set(entities);
        self.tiles = np.full((width, height), fill_value=tile_types.wall, order="F");

        self.visible = np.full((width, height), fill_value=False, order="F"); # Tiles the player is currently seeing
        self.explored = np.full((width, height), fill_value=False, order="F"); # Tiles the player has previously seen

        self.downstairs_location = (0, 0);
        self.upstairs_location = (0, 0);

    def get_entities_at_location(self, location_x: int, location_y: int) -> List[Entity]:
        entities_at_location = [];

        for entity in self.entities:
            if entity.x == location_x and entity.y == location_y:
                entities_at_location.append(entity);

        return entities_at_location;

    def get_blocking_entity_at_location(self, location_x: int, location_y: int) -> Optional[Entity]:
        for entity in self.entities:
            if entity.blocks_movement and entity.x == location_x and entity.y == location_y:
                return entity;

        return None;

    def get_actor_at_location(self, x: int, y: int) -> Optional[Actor]:
        for actor in self.actors:
            if actor.x == x and actor.y == y:
                return actor;

        return None;

    @property
    def gamemap(self) -> GameMap:
        return self;

    @property
    def actors(self) -> Iterator[Actor]:
        """Iterate over this map's living actors."""
        yield from (
                entity
                for entity in self.entities
                if isinstance(entity, Actor) and entity.is_alive
    );

    @property
    def items(self) -> Iterator[Item]:
        yield from (entity for entity in self.entities if isinstance(entity, Item));

    def in_bounds(self, x: int, y: int) -> bool:
        """ Returns True if x and y are inside of the bounds of this map. """
        return 0 <= x < self.width and 0 <= y < self.height;

    def render(self, console: Console) -> None:
        """
        Renders the map.

        If a tile is in the "visible" array, then draw it with the "light" color.
        If it is not, but it is in the "explored" array, then draw ith with the "dark" color.
        Otherwise, the default is "SHROUD".
        """

        console.tiles_rgb[0:self.width, 0:self.height] = np.select(
                condlist=[self.visible, self.explored],
                choicelist=[self.tiles["light"], self.tiles["dark"]],
                default=tile_types.SHROUD
        );

        entities_sorted_for_rendering = sorted(
                self.entities, key=lambda x: x.render_order.value
        );

        for entity in entities_sorted_for_rendering:
            # Only print entities that are in the FOV
            if self.visible[entity.x, entity.y]:
                console.print(entity.x, entity.y, entity.char, fg=entity.color);

class GameWorld:
    """
    Holds the settings for the GameMap, and generates new maps when moving down.
    """

    def __init__(
            self,
            *,
            engine: Engine,
            map_width: int,
            map_height: int,
            max_rooms: int,
            room_min_size: int,
            room_max_size: int,
            current_floor: int = 0,
    ):
        self.engine = engine;

        self.map_width = map_width;
        self.map_height = map_height;

        self.max_rooms = max_rooms;

        self.room_min_size = room_min_size;
        self.room_max_size = room_max_size;

        self.current_floor = current_floor;

        self.floors = [];

    def next_floor(self) -> None:
        self.current_floor += 1;

        if len(self.floors) > self.current_floor:
            self.load_floor(self.current_floor);

            x, y = self.engine.game_map.upstairs_location;
            self.engine.player.place(x, y, self.engine.game_map);
        else:
            self.generate_floor();

    def previous_floor(self) -> None:
        self.current_floor -= 1;

        self.load_floor(self.current_floor);

        x, y = self.engine.game_map.downstairs_location;
        self.engine.player.place(x, y, self.engine.game_map);

    def generate_floor(self) -> None:
        from procgen import generate_dungeon;

        new_floor = generate_dungeon(
            max_rooms=self.max_rooms,
            room_min_size=self.room_min_size,
            room_max_size=self.room_max_size,
            map_width=self.map_width,
            map_height=self.map_height,
            engine=self.engine,
        );

        self.floors.append(new_floor);

        self.engine.game_map = new_floor;

        if self.current_floor > 0:
            self.engine.game_map.tiles[self.engine.player.x, self.engine.player.y] = tile_types.up_stairs;
            self.engine.game_map.upstairs_location = (self.engine.player.x, self.engine.player.y);

    def load_floor(self, index: int) -> None:
        try:
            self.engine.game_map = self.floors[index];
        except IndexError:
            print(f"Invalid floor index {index}");
            return;
