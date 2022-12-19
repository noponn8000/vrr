from __future__ import annotations;
from typing import Iterator, List, Tuple, TYPE_CHECKING;
import random;

import entity_factories;
from game_map import GameMap;
import tile_types;

import tcod

if TYPE_CHECKING:
    from engine import Engine;

class RectangularRoom:
    def __init__(self, x: int, y: int, width: int, height: int):
        self.x1 = x;
        self.y1 = y;
        self.x2 = x + width;
        self.y2 = y + height;

    @property
    def center(self) -> Tuple[int, int]:
        center_x = int((self.x1 + self.x2) / 2);
        center_y = int((self.y1 + self.y2) / 2);

        return center_x, center_y;

    @property
    def inner(self) -> Tuple[slice, slice]:
        """Return the inner area of this room as a 2D array index."""
        return slice(self.x1 + 1, self.x2), slice(self.y1 + 1, self.y2);

    def intersects(self, other: RectangularRoom) -> bool:
        """Return True if this room overlaps with another RectangularRoom."""
        return (
            self.x1 <= other.x2
            and self.x2 >= other.x1
            and self.y1 <= other.y2
            and self.y2 >= other.y1
        );

def tunnel_between(
        start: Tuple[int, int], end: Tuple[int, int]
) -> Iterator[Tuple[int, int]]:
    """Return an L-shaped tunnel between these two points"""
    x1, y1 = start;
    x2, y2 = end;
    if random.random() < 0.5:
        corner_x, corner_y = x2, y1;
    else:
        corner_x, corner_y = x1, y2;

    for x, y in tcod.los.bresenham((x1, y1), (corner_x, corner_y)).tolist():
        yield x, y;
    for x, y in tcod.los.bresenham((corner_x, corner_y), (x2, y2)).tolist():
        yield x, y;

def generate_dungeon(
        max_rooms: int,
        room_min_size: int,
        room_max_size: int,
        map_width: int,
        map_height: int,
        max_monsters_per_room: int,
        engine: Engine,
) -> GameMap:
    """Generate a new dungeon map."""
    player = engine.player;
    dungeon = GameMap(engine, map_width, map_height, entities=[player]);

    rooms: List[RectangularRoom] = [];

    for r in range(max_rooms):
        room_width = random.randint(room_min_size, room_max_size);
        room_height = random.randint(room_min_size, room_max_size);

        x = random.randint(0, dungeon.width - room_width - 1);
        y = random.randint(0, dungeon.height - room_height - 1);

        new_room = RectangularRoom(x, y, room_width, room_height);

        if any(new_room.intersects(other_room) for other_room in rooms):
            continue;
        
        dungeon.tiles[new_room.inner] = tile_types.floor;

        if len(rooms) == 0:
            # Place the player in the first room.
            player.place(*new_room.center, dungeon);
        else:
            # Connect the last and current room by a tunnel.
            for x, y in tunnel_between(rooms[-1].center, new_room.center):
                dungeon.tiles[x, y] = tile_types.floor;

        place_entities(new_room, dungeon, max_monsters_per_room);

        rooms.append(new_room);

    return dungeon;

def place_entities(
        room: RectangularRoom, dungeon: GameMap, maximum_monsters: int
) -> None:
    number_of_monsters = random.randint(0, maximum_monsters);

    for i in range(number_of_monsters):
        x = random.randint(room.x1 + 1, room.x2 - 1);
        y = random.randint(room.y1 + 1, room.y2 - 1);

        if not any(entity.x == x and entity.y == y for entity in dungeon.entities):
            if random.random() < 0.8:
                entity_factories.toad.spawn(dungeon, x, y);
            else:
                entity_factories.tortoise.spawn(dungeon, x, y);
