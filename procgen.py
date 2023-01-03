from __future__ import annotations;
from typing import Dict, Iterator, List, Tuple, TYPE_CHECKING;
import random;
import copy;

import entity_factories;
from game_map import GameMap;
import tile_types;
from entity import Actor;
from components.inventory import Inventory, Slot;

import tcod

if TYPE_CHECKING:
    from engine import Engine;
    from entity import Entity;

max_items_by_floor = [
    (0, 1),
    (4, 2)
];

max_monsters_by_floor = [
    (0, 2),
    (4, 3),
    (6, 5)
];

item_chances: Dict[int, List[Tuple[Entity, int]]] = {
    0: [(entity_factories.health_potion, 35)],
    2: [(entity_factories.confusion_scroll, 10)],
    4: [(entity_factories.lightning_scroll, 25), (entity_factories.sword, 5)],
    6: [(entity_factories.fireball_scroll, 25), (entity_factories.chain_mail, 15)]
};
enemy_chances: Dict[int, List[Tuple[Entity, int]]] = {
    0: [(entity_factories.toad, 80), (entity_factories.chest, 5), (entity_factories.miner, 10)],
    3: [(entity_factories.tortoise, 15)],
    5: [(entity_factories.tortoise, 30)],
    7: [(entity_factories.tortoise, 60)],
}
inventory_chances: Dict[Entity, List[Tuple[Entity, int]]] = {
    "Depraved Toad": [(entity_factories.basalt_rock, 25)],
    "Merciless Tortoise": [(entity_factories.basalt_rock, 50)],
    "Lapidified Miner": [(entity_factories.pickaxe, 100)],
    "Chest": [(entity_factories.chain_mail, 50), (entity_factories.fireball_scroll, 25), (entity_factories.sword, 25)]
};

def get_max_value_for_floor(
        max_value_by_floor: List[Tuple[int, int]], floor: int
) -> int:
    current_value = 0;

    for floor_minimum, value in max_value_by_floor:
        if floor_minimum > floor:
            break;
        else:
            current_value = value;

    return current_value;

def get_entities_at_random(
        weighted_chances_by_floor: Dict[int, List[Tuple[Entity, int]]],
        number_of_entities,
        floor: int
) -> List[Entity]:
    entity_weighted_chances = {};

    for key, values in weighted_chances_by_floor.items():
        if key > floor:
            break;
        else:
            for value in values:
                entity = value[0];
                weighted_chance = value[1];

                entity_weighted_chances[entity] = weighted_chance;

    entities = list(entity_weighted_chances.keys());
    entity_weighted_chance_values = list(entity_weighted_chances.values());

    chosen_entities = random.choices(
        entities, weights=entity_weighted_chance_values, k=number_of_entities
    );

    return chosen_entities;

def get_inventory_at_random(weighted_chances_by_entity: Dict[Entity, List[Tuple[Entity, int]]],
                            entity: Entity,
                            number_of_items: int
) -> List[Item]:
    inventory = [];
    items = weighted_chances_by_entity[entity.name];
    chances = {};

    for item, chance in items:
        chances[item] = chance;

    items = random.choices(list(chances.keys()), weights=list(chances.values()), k=number_of_items);

    for item in items:
        inventory.append(item);

    return inventory;

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
        engine: Engine,
) -> GameMap:
    """Generate a new dungeon map."""
    player = engine.player;
    dungeon = GameMap(engine, map_width, map_height, entities=[player]);

    rooms: List[RectangularRoom] = [];

    center_of_last_room = (0, 0);

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
            entity_factories.chest.place(*new_room.center, dungeon);
        else:
            # Connect the last and current room by a tunnel.
            for x, y in tunnel_between(rooms[-1].center, new_room.center):
                dungeon.tiles[x, y] = tile_types.floor;

            center_of_last_room = new_room.center;

        place_entities(new_room, dungeon, engine.game_world.current_floor);

        rooms.append(new_room);

    dungeon.tiles[center_of_last_room] = tile_types.down_stairs;
    dungeon.downstairs_location = center_of_last_room;

    return dungeon;

def cellular_dungeon(engine: Engine,
                     map_width: int = 80,
                     map_height: int = 45,
                     wall_conversion: int = 4,
                     floor_conversion: int = 4,
                     step_count: int = 10,
                     wall_chance: float = 0.5,
                     floor_tile = tile_types.floor,
                     wall_tile = tile_types.wall,
) -> GameMap:
    game_map = generate_random_map(map_width, map_height, wall_chance, floor_tile, wall_tile, engine);

    for step in range(step_count):
       game_map = iterate_automaton(game_map, wall_conversion, floor_conversion, floor_tile, wall_tile);

    engine.player.place(*find_random_tile(game_map, tile_types.floor), game_map);
    game_map.engine = engine;

    return game_map;

def find_random_tile(game_map: GameMap, tile) -> Tuple[int, int]:
    random_tile = None;
    while random_tile != tile:
        x = random.randint(0, game_map.width - 1);
        y = random.randint(0, game_map.height - 1);

        random_tile = game_map.tiles[x, y];

    return (x, y);

def iterate_automaton(game_map: GameMap, wall_conversion: float, floor_conversion: float, floor_tile, wall_tile) -> GameMap:
    new_map = copy.deepcopy(game_map);

    for x in range(game_map.width):
        for y in range(game_map.height):
            floor_neighbour_count = count_neighbours(game_map, (x, y), floor_tile);
            if game_map.tiles[x, y] == floor_tile:
                new_map.tiles[x, y] = floor_tile if floor_neighbour_count > floor_conversion else wall_tile;
            else:
                new_map.tiles[x, y] = wall_tile if 8 - floor_neighbour_count > wall_conversion else floor_tile;

    return new_map;

def count_neighbours(game_map: GameMap, position: Tuple[int, int], tile) -> int:
    directions = [(1, 0), (1, 1), (1, -1), (0, 1), (0, -1), (-1, 1), (-1, 0), (-1, -1)]
    count = 0;

    for direction in directions:
        dx, dy = direction;
        x, y = position;

        x += dx;
        x += dy;

        if (x < 0 or x >= game_map.width) or (y < 0 or y >= game_map.height):
            continue;

        neighbour = game_map.tiles[x, y];
        if neighbour == tile:
            count += 1;

    return count;

def generate_random_map(map_width: int, map_height: int, wall_chance: float, floor_tile, wall_tile, engine: Engine) -> GameMap:
    game_map = GameMap(engine=engine, width=map_width, height=map_height);

    for x in range(map_width):
       for y in range(map_height):
           game_map.tiles[x, y] = wall_tile if random.random() < wall_chance else floor_tile;

    return game_map;

def place_entities(
        room: RectangularRoom, dungeon: GameMap, floor_number: int
) -> None:
    number_of_monsters = random.randint(
        0, get_max_value_for_floor(max_monsters_by_floor, floor_number)
    );
    number_of_items = random.randint(
        0, get_max_value_for_floor(max_items_by_floor, floor_number)
    );

    monsters: List[Entity] = get_entities_at_random(
        enemy_chances, number_of_monsters, floor_number
    );

    items: List[Entity] = get_entities_at_random(
        item_chances, number_of_items, floor_number
    );

    for entity in monsters + items:
        entity = copy.deepcopy(entity);
        x = random.randint(room.x1 + 1, room.x2 - 1);
        y = random.randint(room.y1 + 1, room.y2 - 1);


        if not any(entity.x == x and entity.y == y for entity in dungeon.entities):
            if isinstance(entity, Actor):
                entity.fighter.update_stats();
                for item in get_inventory_at_random(inventory_chances, entity, entity.inventory.capacity):
                    entity.inventory.add(item);
            entity.spawn(dungeon, x, y);
