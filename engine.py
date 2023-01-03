from __future__ import annotations;

import lzma;
import pickle;
from typing import TYPE_CHECKING, Optional;

from tcod.context import Context;
from tcod.console import Console;
from tcod.map import compute_fov;

from actions import MovementAction;
import exceptions;
from message_log import MessageLog;
import render_functions;
import color;

if TYPE_CHECKING:
    from entity import Actor;
    from game_map import GameMap;

class Engine:
    game_map: GameMap

    def save_as(self, filename: str) -> None:
        """Save this Engine instance as a compressed file."""
        save_data = lzma.compress(pickle.dumps(self));
        with open(filename, "wb") as f:
            f.write(save_data);

    def __init__(self, player: Optional[Actor], show_all_tiles = False):
        self.message_log = MessageLog();
        self.mouse_location = (0, 0);
        self.player = player;
        self.show_all_tiles = show_all_tiles;

    def handle_enemy_turns(self) -> None:
        for entity in set(self.game_map.actors) - {self.player}:
            if entity.ai:
                try:
                    entity.ai.perform();
                except exceptions.Impossible:
                    pass; # Ignore impossible action exceptions from AI-controlled actors.

    def render(self, console: Console) -> None:
        self.game_map.render(console);

        if not self.player:
            return;

        self.message_log.render(console, x=21, y=45, width=40, height=5);

        render_functions.render_bar(
                console=console,
                x=0,
                y=45,
                current_value=self.player.fighter.hp,
                maximum_value=self.player.fighter.max_hp,
                total_width=20,
        );

        render_functions.render_bar(
            console=console,
            x=0,
            y=46,
            current_value = self.player.level.current_xp,
            maximum_value = self.player.level.experience_to_next_level,
            total_width=20,
            color_empty=color.xp_bar_empty,
            color_filled=color.xp_bar_filled
        );

        render_functions.render_names_at_mouse_location(console=console, x=21, y=44, engine=self);

        render_functions.render_dungeon_level(
            console=console,
            dungeon_level=self.game_world.current_floor,
            location=(0, 47)
        )

    def update_fov(self) -> None:
        """ Recompute the visible area based on the player's point of view."""
        if self.show_all_tiles:
            self.game_map.visible[:] = True;
        else:
            self.game_map.visible[:] = compute_fov(
                self.game_map.tiles["transparent"],
                (self.player.x, self.player.y),
                radius=8,
            );

        self.game_map.explored |= self.game_map.visible;
