from __future__ import annotations;

from typing import TYPE_CHECKING;

import color;

if TYPE_CHECKING:
    from tcod import Console;
    from engine import Engine;
    from game_map import GameMap;

def get_names_at_location(x: int, y: int, game_map: GameMap) -> str:
    if not game_map.in_bounds(x, y) or not game_map.visible[x, y]:
        return "";

    names = ", ".join(
            entity.name for entity in game_map.entities if entity.x == x and entity.y == y
    );

    return names.capitalize();

def render_bar(
        console: Console,
        x: int,
        y: int,
        current_value: int,
        maximum_value: int,
        total_width: int,
        color_empty: Tuple[int, int, int] = color.bar_empty,
        color_filled: Tuple[int, int, int] = color.bar_filled
) -> None:
    bar_width = int(float(current_value) / maximum_value * total_width);

    console.draw_rect(x=x, y=y, width=total_width, height=1, ch=1, bg=color_empty);

    if bar_width > 0:
        console.draw_rect(
                x=x, y=y, width=bar_width, height=1, ch=1, bg=color_filled
        );

    console.print(
            x=x + 1, y=y, string=f"{current_value}/{maximum_value}", fg=color.bar_text
    );

def render_dungeon_level(
        console: Console, dungeon_level: int, location: Tuple[int, int]
) -> None:
    """
    Render the current floor the player is on at the given location.
    """
    x, y = location;

    console.print(x=x, y=y, string=f"{dungeon_level} floors deep");

def render_names_at_mouse_location(
        console: Console, x: int, y: int, engine: Engine
) -> None:
    mouse_x, mouse_y = engine.mouse_location;

    names_at_mouse_location = get_names_at_location(
            x=mouse_x, y=mouse_y, game_map=engine.game_map
    );

    console.print(x=x, y=y, string=names_at_mouse_location, fg=color.ui_foreground);
