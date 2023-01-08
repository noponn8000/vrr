from __future__ import annotations;

import os;

import textwrap;
import random;
from typing import Callable, Optional, Tuple, TYPE_CHECKING, Union;

import tcod.event;

import actions;
from actions import Action, BumpAction, WaitAction, PickupAction;
from components.attributes import Attributes;
from components.ai import WalkTowards;
import color;
import exceptions;
import tile_types;

if TYPE_CHECKING:
    from engine import Engine;
    from entity import Item;

MOVE_KEYS = {
    # Arrow keys.
    tcod.event.K_UP: (0, -1),
    tcod.event.K_DOWN: (0, 1),
    tcod.event.K_LEFT: (-1, 0),
    tcod.event.K_RIGHT: (1, 0),
    tcod.event.K_HOME: (-1, -1),
    tcod.event.K_END: (-1, 1),
    tcod.event.K_PAGEUP: (1, -1),
    tcod.event.K_PAGEDOWN: (1, 1),
    # Numpad keys.
    tcod.event.K_KP_1: (-1, 1),
    tcod.event.K_KP_2: (0, 1),
    tcod.event.K_KP_3: (1, 1),
    tcod.event.K_KP_4: (-1, 0),
    tcod.event.K_KP_6: (1, 0),
    tcod.event.K_KP_7: (-1, -1),
    tcod.event.K_KP_8: (0, -1),
    tcod.event.K_KP_9: (1, -1),
}

WAIT_KEYS = {
        tcod.event.K_PERIOD,
        tcod.event.K_KP_5,
        tcod.event.K_CLEAR,
}

CONFIRM_KEYS = {
    tcod.event.K_RETURN,
    tcod.event.K_KP_ENTER
}

ActionOrHandler = Union[Action, "BaseEventHandler"];
"""An event handler return value which can trigger an action or switch active handler.
If a handler is returned then it will become the active handler for future events.
If an action is returned it will be attempted and if it's valid then
MainGameEventHandler will become the active handler.
"""

class BaseEventHandler(tcod.event.EventDispatch[ActionOrHandler]):
    def handle_events(self, event: tcod.event.Event) -> BaseEventHandler:
        """Handle an event and return the next active event handler."""
        state = self.dispatch(event);
        if isinstance(state, tcod.event.EventDispatch):
            return state;
        assert not isinstance(state, Action), f"{self!r} can not handle actions.";
        return self;

    def on_render(self, console: tcod.Console) -> None:
        raise NotImplementedError();

    def ev_quit(self, event: tcod.event.Quit) -> Optional[Action]:
        raise SystemExit();

class PopupMessage(BaseEventHandler):
    """Display a popup text window."""

    def __init__(self, parent_handler: BaseEventHandler, text: str):
        self.parent = parent_handler;
        self.text = text;

    def on_render(self, console: tcod.Console) -> None:
        """Render the parent and dim the result, then print the message on top."""
        self.parent.on_render(console);
        console.tiles_rgb["fg"] //= 8;
        console.tiles_rgb["bg"] //= 6;

        console.draw_frame(
            x=console.width // 2 - (len(self.text) // 2 + 1),
            y=console.height // 2 - 1,
            width=len(self.text) + 3,
            height=3,
            bg=color.ui_background
        );
        console.print(
            console.width // 2,
            console.height // 2,
            self.text,
            fg=color.ui_foreground,
            bg=color.ui_background,
            alignment=tcod.CENTER
        );

    def ev_keydown(self, event: tcod.event.KeyDown) -> Optional[BaseEventHandler]:
        if event.sym in CONFIRM_KEYS:
            return self.parent;
        return None;

# Subclass of tcod's EventDispatch class.
# EventDispatch is a clas which allows us to send an event to its proper method
# based on what type of event it is.
class EventHandler(BaseEventHandler):
    def on_quit(self) -> None:
        """Handle exiting out of a finished game."""
        if os.path.exists("savegame.sav"):
            os.remove("savegame.sav"); # Deletes the save file.
        raise exceptions.QuitWithoutSaving(); # Avoid saving a finished game.

    def ev_quit(self, event: tcod.event.Quit) -> None:
        self.on_quit();

    def __init__(self, engine: Engine):
        self.engine = engine;

    def handle_events(self, event: tcod.event.Event) -> BaseEventHandler:
        """Handle events for input handlers with an engine."""
        action_or_state = self.dispatch(event);
        if isinstance(action_or_state, tcod.event.EventDispatch):
            return action_or_state;
        if self.handle_action(action_or_state):
            # A valid action was performed.
            if not self.engine.player.is_alive:
                # The player was killed sometime during or after the action.
                return GameOverEventHandler(self.engine);
            elif self.engine.player.level.requires_level_up:
                return LevelUpEventHandler(self.engine);
            return MainGameEventHandler(self.engine); # Return to the main handler.
        return self;

    def handle_action(self, action: Optional[Action]) -> None:
        """Handle actions returned from event methods.

        Returns True if the action will advance a turn.
        """
        if action is None:
            return False;

        try:
            action.perform();
        except exceptions.Impossible as exc:
            self.engine.message_log.add_message(exc.args[0], color.impossible);
            return False; # Skip enemy turn on exceptions.

        self.engine.handle_enemy_turns();

        self.engine.update_fov();
        return True;

    def ev_mousemotion(self, event: tcod.event.MouseMotion) -> None:
        if self.engine.game_map.in_bounds(event.tile.x, event.tile.y):
            self.engine.mouse_location = event.tile.x, event.tile.y;

    def on_render(self, console: tcod.Console) -> None:
        self.engine.render(console);

class AskUserEventHandler(EventHandler):
    """Handles user input for actions which require special input."""

    def ev_keydown(self, event: tcod.event.KeyDown) -> Optional[ActionOrHandler]:
        """By default any key exits this input handler."""
        if event.sym in {
            tcod.event.K_LSHIFT,
            tcod.event.K_RSHIFT,
            tcod.event.K_LCTRL,
            tcod.event.K_RCTRL,
            tcod.event.K_LALT,
            tcod.event.K_RALT,
        }:
            return None;
        return self.on_exit();

    def ev_mousebuttondown(self, event: tcod.event.MouseButtonDown) -> Optional[ActionOrHandler]:
        """By default any mouse click exits this input handler."""
        return self.on_exit();

    def on_exit(self) -> Optional[ActionOrHandler]:
        """Called when the user is trying to exit or cancel an action.

        By default this returns to the main event handler.
        """
        return MainGameEventHandler(self.engine);

class LevelUpEventHandler(AskUserEventHandler):
    TITLE = "Level Up";

    def on_render(self, console: tcod.Console) -> None:
        super().on_render(console);

        if self.engine.player.x <= 30:
            x = 40;
        else:
            x = 0;

        console.draw_frame(
            x=x,
            y=0,
            width=35,
            height=8,
            title=self.TITLE,
            clear=True,
            fg=color.ui_foreground,
            bg=color.ui_background
        );

        console.print(x=x + 1, y=1, string="You level up.", fg=color.level_up);
        console.print(x=x + 1, y=2, string="Choose an attribute to increase.");

        console.print(
            x=x+1,
            y=4,
            string=f"a) Vitality (+20 HP, from {self.engine.player.fighter.max_hp})"
        );
        console.print(
            x=x+1,
            y=5,
            string=f"b) Strength (+1 AP, from {self.engine.player.fighter.power})"
        );
        console.print(
            x=x+1,
            y=6,
            string=f"c) Resistance (+1 DP, from {self.engine.player.fighter.defense})"
        );

    def ev_keydown(self, event: tcod.event.KeyDown) -> Optional[ActionOrHandler]:
        player = self.engine.player;
        key = event.sym;
        index = key - tcod.event.K_a;


        if 0 <= index <= 2:
            match index:
               case 0:
                    player.attributes.attributes["vitality"] += 1;
               case 1:
                    player.attributes.attributes["strength"] += 1;
               case 2:
                    player.attributes.attributes["resistance"] += 1;
            player.level.increase_level();
            player.fighter.update_stats();
        else:
            self.engine.message_log.add_message("Invalid entry.", color.invalid);

            return None;

        return super().ev_keydown(event);

    def ev_mousebuttondown(
            self, event: tcod.event.MouseButtonDown
    ) -> Optional[ActionOrHandler]:
        """
        Do not allow the player to click to exit the menu.
        """
        return None;

class InventoryEventHandler(AskUserEventHandler):
    """This handler lets the user select an item.
    What happens then depends on the subclass.
    """

    TITLE = "<missing title>";

    def __init__(self, inventory: Inventory, engine: Engine):
        super().__init__(engine);

        self.inventory = inventory;
        self.number_of_entries = min(len(self.inventory.items), 26);
        self.cursor = 0;
        self.offset = 0;

    def on_render(self, console: tcod.Console) -> None:
        """Render an inventory menu, which displays the items in the inventory.
        It will move to a different position based on where the player is located.
        """
        super().on_render(console);

        height = self.number_of_entries + 2;

        if height <= 3:
            height = 3;

        if self.engine.player.x <= 30:
            x = 40;
        else:
            x = 0;

        y = 0;

        width = len(self.TITLE) + 4;

        console.draw_frame(
            x=x,
            y=y,
            width=width,
            height=height,
            title=self.TITLE,
            clear=True,
            fg=color.ui_foreground,
            bg=color.ui_background
        );

        if self.number_of_entries > 0:
            for i, slot in enumerate(self.inventory.items[self.offset:]):
                bg = color.ui_highlight if i == self.cursor else color.ui_background;
                item_key = chr(ord("a") + i);
                item = slot.item;
                is_equipped = self.engine.player.equipment.item_is_equipped(item);

                item_string = f"({item_key}) {item.name}";

                if slot.count > 1:
                    item_string += f" x{slot.count} "

                if is_equipped:
                    item_string = item_string + " (E) ";

                console.print(x + 1, y + i + 1,
                              f"[{item.char}] ",
                              fg=item.color,
                              bg=color.ui_background
                );
                console.print(
                    x + 5,
                    y + i + 1,
                    item_string,
                    bg=bg,
                    fg=color.ui_foreground
                );
        else:
            console.print(x + 1, y + 1, "(Empty)");

    def ev_keydown(self, event: tcod.event.KeyDown) -> Optional[ActionOrHandler]:
        if not self.inventory:
            return MainGameEventHandler(self.engine);

        player = self.engine.player;
        key = event.sym;
        index = key - tcod.event.K_a;

        if key in CURSOR_Y_KEYS:
            self.cursor = min(
                max(self.cursor + CURSOR_Y_KEYS[key], 0),
                len(self.inventory.items)
             );

            if self.cursor > self.number_of_entries - 1:
                self.offset += 1;

            return None;

        if key in CONFIRM_KEYS:
            selected_item = self.inventory.items[self.cursor].item;
            return self.on_item_selected(selected_item);

        if 0 <= index <= 26:
            try:
                selected_item = self.inventory.items[index + self.offset];
            except IndexError:
                self.engine.message_log.add_message("Invalid entry.", color.invalid);
                return None;
            return self.on_item_selected(selected_item);
        return super().ev_keydown(event);

    def on_item_selected(self, item: Item) -> Optional[ActionOrHandler]:
        """Called when the user selects a valid item."""
        raise NotImplementedError();

class InventoryCollectHandler(InventoryEventHandler):
    def __init__(self, engine: Engine, inventory: Inventory, title: str = "<No Title>"):
        super().__init__(inventory, engine);
        self.TITLE = title;

    def set_position(x: int, y: int) -> None:
        super().set_position(x, y);
        self.inventory = self.engine.game_map.get_inventory_at_location(self.x, self.y);
        self.title = f"{self.inventory.parent.name}'s Inventory";

    def on_item_selected(self, item: Item) -> Optional[ActionOrHandler]:
        self.engine.player.inventory.add(item);
        self.inventory.remove(item);

class InventoryActivateHandler(InventoryEventHandler):
    """Handle using an inventory item."""

    TITLE = "Inventory - Context Menu";

    def on_item_selected(self, item: Item) -> Optional[ActionOrHandler]:
        """Return the action for the selected item."""
        if item.consumable:
            return item.consumable.get_action(self.engine.player);
        elif item.equippable:
            return actions.EquipAction(self.engine.player, item);
        else:
            return None;

class InventoryDropHandler(InventoryEventHandler):
    """Handle dropping an inventory item."""

    TITLE = "Inventory - Drop item";

    def on_item_selected(self, item: Item) -> Optional[ActionOrHandler]:
        """Drop this item"""
        return actions.DropItemAction(self.engine.player, item);

class SelectIndexHandler(AskUserEventHandler):
    """Handles asking the user for an index on the map."""
    def __init__(self, engine: Engine):
        super().__init__(engine);
        player = self.engine.player;
        engine.mouse_location = player.x, player.y;

    def on_render(self, console: tcod.Console) -> None:
        """Highlight the tile under the cursor."""
        super().on_render(console);
        x, y = self.engine.mouse_location;
        console.tiles_rgb["bg"][x, y] = color.white;
        console.tiles_rgb["fg"][x, y] = color.black;

    def ev_keydown(self, event: tcod.event.KeyDown) -> Optional[ActionOrHandler]:
        """Check for key movement or confirmation keys."""
        key = event.sym;
        if key in MOVE_KEYS:
            modifier = 1; # Holding modifier keys will speed up movement.
            if event.mod & (tcod.event.KMOD_LSHIFT | tcod.event.KMOD_RSHIFT):
                modifier *= 5;
            if event.mod & (tcod.event.KMOD_LCTRL | tcod.event.KMOD_RCTRL):
                modifier *= 10;
            if event.mod & (tcod.event.KMOD_LALT | tcod.event.KMOD_RALT):
                modifier *= 20;

            x, y = self.engine.mouse_location;
            dx, dy = MOVE_KEYS[key];
            x += dx * modifier;
            y += dy * modifier;
            # Clamp the cursor index to the map size.
            x = max(0, min(x, self.engine.game_map.width -1));
            y = max(0, min(y, self.engine.game_map.height - 1));
            self.engine.mouse_location = x, y;
            return None;
        elif key in CONFIRM_KEYS:
            return self.on_index_selected(*self.engine.mouse_location);
        return super().ev_keydown(event);

    def ev_mousebuttondown(self, event: tcod.event.MouseButtonDown) -> Optional[ActionOrHandler]:
        """Left click confirms a selection."""
        if self.engine.game_map.in_bounds(*event.tile):
            if event.button == 1:
                return self.on_index_selected(*event.tile);
        return super().ev_mousebuttondown(event);

    def on_index_selected(self, x: int, y: int) -> Optional[ActionOrHandler]:
        """Called when an index is selected."""
        raise NotImplementedError;

class LookHandler(SelectIndexHandler):
    """Lets the player look around using the keyboard."""

    def on_render(self, console: tcod.Console) -> None:
        super().on_render(console);

        x, y = self.engine.mouse_location;
        entities = self.engine.game_map.get_entities_at_location(x, y);

        if entities == []:
            return;

        topmost_entity = sorted(
                entities, key=lambda x: x.render_order.value
        )[0];

        width = max(len(topmost_entity.name) + 2, 24);
        wrapped_text = textwrap.wrap(topmost_entity.description, width - 2);
        height = len(wrapped_text) + 4;
        offset_x = 1 if x < 40 else -width;
        offset_y = 1 if y < 30 else -height - 6;

        console.draw_frame(
            x=x+offset_x,
            y=y+offset_y,
            width=width,
            height=height,
            clear=True,
            fg=color.ui_foreground,
            bg=color.ui_background,
        );

        # Add 1 to the offsets so that the text prints inside the frame.
        offset_x += 1;
        offset_y += 1;

        console.print(x+offset_x, y+offset_y, topmost_entity.name, fg=topmost_entity.color);
        offset_y += 1;

        for i, line in enumerate(wrapped_text):
            offset_y += 1;
            console.print(x+offset_x, y+offset_y, line, fg=color.white);

    def on_index_selected(self, x: int, y: int) -> MainGameEventHandler:
        """Return to the main handler."""
        self.engine.event_handler = MainGameEventHandler(self.engine);

class SingleRangedAttackHandler(SelectIndexHandler):
    """Handles targeting a single enemy. Only the enemy selected will be affected."""
    def __init__(
        self, engine: Engine, callback: Callable[[Tuple[int, int]], Optional[Action]]
    ):
        super().__init__(engine);

        self.callback = callback;

    def on_index_selected(self, x: int, y: int) -> Optional[Action]:
        return self.callback((x, y));

class AreaRangedAttackHandler(SelectIndexHandler):
    """Handles targeting an area within a given radius. Any entity within the area will be affected."""

    def __init__(
        self,
        engine: Engine,
        radius: int,
        callback: Callable[[Tuple[int,int]], Optional[Action]]
    ):
        super().__init__(engine);

        self.radius = radius;
        self.callback = callback;

    def on_render(self, console: tcod.Console) -> None:
        """Highlight the tile under the cursor."""
        super().on_render(console);

        x, y = self.engine.mouse_location

        # Draw a rectangle around the targeted area
        console.draw_frame(
            x=x - self.radius - 1,
            y=y - self.radius - 1,
            width=self.radius ** 2,
            height=self.radius ** 2,
            fg=color.red,
            clear=False
        );

    def on_index_selected(self, x: int, y: int) -> Optional[Action]:
        return self.callback((x, y));

class MainGameEventHandler(EventHandler):
    def ev_keydown(self, event: tcod.event.KeyDown) -> Optional[ActionOrHandler]:
        action: Optional[Action] = None;

        key = event.sym;
        modifier = event.mod;

        player = self.engine.player;

        if key == tcod.event.K_PERIOD and modifier & (
                tcod.event.KMOD_LSHIFT | tcod.event.KMOD_RSHIFT
        ):
            if (player.x, player.y) == self.engine.game_map.downstairs_location:
                return actions.TakeDownStairsAction(player);
            elif self.engine.game_map.explored[self.engine.game_map.downstairs_location]:
                return WalkTowardsHandler(self.engine, self.engine.game_map.downstairs_location);
        elif key == tcod.event.K_COMMA and modifier & (
                tcod.event.KMOD_LSHIFT | tcod.event.KMOD_RSHIFT
        ):
            return actions.TakeUpStairsAction(player);

        if key in MOVE_KEYS:
            dx, dy = MOVE_KEYS[key];
            action = BumpAction(player, dx, dy);
        elif key in WAIT_KEYS:
            action = WaitAction(player);
        elif key == tcod.event.K_ESCAPE:
            raise SystemExit();
        elif key == tcod.event.K_v:
            return HistoryViewer(self.engine);
        elif key == tcod.event.K_g:
            action = PickupAction(player);
        elif key == tcod.event.K_u:
            if modifier & (tcod.event.KMOD_LSHIFT | tcod.event.KMOD_RSHIFT):
                return ChooseCollectDirectionHandler(self.engine, player.x, player.y);
                #inventory_at_location = self.engine.game_map.get_inventory_at_location(player.x, player.y);

                #if inventory_at_location:
                    #title = f"{inventory_at_location.parent.name}'s Inventory";
                    #return InventoryCollectHandler(self.engine, inventory_at_location, title);
            else:
                return InventoryActivateHandler(self.engine.player.inventory, self.engine);
        elif key == tcod.event.K_t:
            return ChooseDialogueDirectionHandler(self.engine, player.x, player.y);
        elif key == tcod.event.K_d:
            return InventoryDropHandler(self.engine.player.inventory, self.engine);
        elif key == tcod.event.K_l:
            return LookHandler(self.engine);
        elif key==tcod.event.K_r:
            # Reveal the whole map (debug purposes)
            self.engine.game_map.explored[:, :] = True;
        elif key==tcod.event.K_x:
            return CharacterSheet(self.engine.player, self.engine);


        return action;

class GameOverEventHandler(EventHandler):
    def ev_keydown(self, event: tcod.event.KeyDown) -> None:
        if event.sym == tcod.event.K_ESCAPE:
            self.on_quit();

CURSOR_Y_KEYS = {
        tcod.event.K_UP: -1,
        tcod.event.K_DOWN: 1,
        tcod.event.K_PAGEUP: -10,
        tcod.event.K_PAGEDOWN: 10
};

class HistoryViewer(EventHandler):
    """Print the history on a larger window which can be navigated."""

    def __init__(self, engine: Engine):
        super().__init__(engine);
        self.log_length = len(engine.message_log.messages);
        self.cursor = self.log_length - 1;

    def on_render(self, console: tcod.Console) -> Optional[MainGameEventHandler]:
        super().on_render(console);

        log_console = tcod.Console(console.width - 6, console.height - 6);

        # Draw a frame with a custom banner title.
        log_console.draw_frame(0, 0, log_console.width, log_console.height);
        log_console.print_box(
                0, 0, log_console.width, 1, "┤Message history├", alignment=tcod.CENTER
        );

        # Render the message log using the cursor parameter.
        self.engine.message_log.render_messages(
                log_console,
                1,
                1,
                log_console.width - 2,
                log_console.height - 2,
                self.engine.message_log.messages[: self.cursor + 1]
        );
        log_console.blit(console, 3, 3);

    def ev_keydown(self, event: tcod.event.KeyDown) -> None:
        if event.sym in CURSOR_Y_KEYS:
            adjust = CURSOR_Y_KEYS[event.sym];
            if adjust < 0 and self.cursor == 0:
                # Only move from the top to the bottom when you are on the edge.
                self.cursor = self.log_length - 1;
            else:
                # Otherwise move while staying clamped to the bounds of the history.
                self.cursor = max(0, min(self.cursor + adjust, self.log_length - 1));
        elif event.sym == tcod.event.K_HOME:
            self.cursor = 0; # Move directly to the top message.
        elif event.sym == tcod.event.K_END:
            self.cursor = self.log_length - 1; # Move directly to the last message.
        else: # Any other key moves back to the main game state.
            return MainGameEventHandler(self.engine);
        return None;

class CharacterSheet(EventHandler):
    """Print an self.entity's statistics."""
    def __init__(self, entity: Entity, engine: Engine):
        super().__init__(engine);
        self.entity = entity;

    def on_render(self, console: tcod.Console) -> Optional[MainGameEventHandler]:
        super().on_render(console);

        sheet_console=tcod.Console(console.width - 20, console.height - 20);

        sheet_console.draw_frame(0, 0, sheet_console.width, sheet_console.height);
        sheet_console.print_box(
            0, 0, sheet_console.width, 1, f"┤{self.entity.name}'s character sheet├", alignment=tcod.CENTER
        );

        sheet_console.print(1, 1, "┤Level and experience├");

        if self.entity.level:
            sheet_console.print(1, 2, f"- Level: {self.entity.level.current_level}", fg=color.experience);
            sheet_console.print(1, 4, f"- Experience to next level: {self.entity.level.experience_to_next_level}", fg=color.experience);
        else:
            sheet_console.print(1, 2, "- Level: <No Data>");
            sheet_console.print(1, 4, "- Experience to next level: <No Data>");

        sheet_console.print(1, 6, "┤Attributes and health├");

        if self.entity.fighter:
            sheet_console.print(1, 7, f"- Health: ♥{self.entity.fighter.hp}/{self.entity.fighter.max_hp}", fg=color.vitality);
            sheet_console.print(1, 9, f"- Vitality: {self.entity.attributes.attributes['vitality']}", fg=color.vitality);
            sheet_console.print(1, 11, f"- Strength: {self.entity.attributes.attributes['strength']}", fg=color.strength);
            sheet_console.print(1, 13, f"- Resistance: {self.entity.attributes.attributes['resistance']}", fg=color.resistance);
        else:
            sheet_console.print(1, 7, f"- Health: <No Data>");
            sheet_console.print(1, 9, f"- Vitality: <No Data>");
            sheet_console.print(1, 11, f"- Strength: <No Data>");
            sheet_console.print(1, 13, f"- Resistance: <No Data>");

        sheet_console.print(1, 15, "┤Equipment├");

        if self.entity.equipment:
            if self.entity.equipment.get_item_in_slot("weapon"):
                weapon = self.entity.equipment.get_item_in_slot("weapon");
                sheet_console.print(1, 16, f"Weapon: {weapon.name}, ♥{weapon.equippable.roll_number}d{weapon.equippable.damage_roll} ->{weapon.equippable.penetration}", fg=color.strength);
            else:
                sheet_console.print(1, 16, "Weapon: <Empty>");


            if self.entity.equipment.get_item_in_slot("armor"):
                armor = self.entity.equipment.get_item_in_slot('armor');
                sheet_console.print(1, 18, f"Armor: {armor.name}, ■{armor.equippable.defense_bonus}", fg=color.resistance);
            else:
                sheet_console.print(1, 18, "Armor: <Empty>");
        else:
            sheet_console.print(1, 16, "No equimpent");

        sheet_console.blit(console, 10, 10);

    def ev_keydown(self, event: tcod.event.KeyDown) -> None:
        if event.sym == tcod.event.K_ESCAPE:
            return MainGameEventHandler(self.engine);

class DialogueEventHandler(EventHandler):
    def __init__(self, dialogue: Optional[Dialogue], engine: Engine):
        super().__init__(engine);

        if dialogue:
            self.dialogue = dialogue;
        else:
            self.dialogue = self.engine.game_map.get_dialogue_at_position(self.x, self.y);
        self.cursor = 0;
        self.number_of_entries = len(self.dialogue.choices);

    def on_render(self, console: Console) -> None:
        super().on_render(console);

        dialogue_console = tcod.Console(console.width - 30, console.height - 30);

        dialogue_console.draw_frame(0, 0, dialogue_console.width, dialogue_console.height, decoration="╔═╗║ ║╚═╝");
        dialogue_console.print_box(
            0, 0, dialogue_console.width, 1, f"┤{self.dialogue.parent.name}├", alignment=tcod.CENTER
        );

        text_lines = textwrap.wrap(self.dialogue.text, console.width - 2);
        for offset, line in enumerate(text_lines):
            dialogue_console.print(
                1, offset + 1, line
            );

        y = len(text_lines) + 1;
        for index, choice in enumerate(self.dialogue.choices):
           y += 1;
           bg_color = color.ui_highlight if self.cursor == index else color.black;

           char = chr(ord("a") + index);

           frame_width = dialogue_console.width - 4;
           choice_lines = textwrap.wrap(choice.choice_text, frame_width - 5);

           frame_height = len(choice_lines) + 2;

           dialogue_console.draw_frame(1, y, frame_width, frame_height, "");
           dialogue_console.print(2, y + 1, f"{char})");

           for offset, line in enumerate(choice_lines):
               dialogue_console.print(5, y + offset + 1, line, bg=bg_color);
           y += frame_height;

        dialogue_console.blit(console, 15, 15);

    def ev_keydown(self, event: tcod.event.KeyDown) -> Optional[ActionOrHandler]:
        # The player has exhausted the dialogue.
        if self.dialogue.choices == []:
            self.dialogue.reset();
            return MainGameEventHandler(self.engine);

        key = event.sym;
        if key in CURSOR_Y_KEYS:
            self.cursor = max(0, min(self.number_of_entries, self.cursor + CURSOR_Y_KEYS[key]));

        if key in CONFIRM_KEYS:
            self.dialogue.make_choice(self.cursor);

        if key == tcod.event.K_ESCAPE:
            self.dialogue.reset();
            return MainGameEventHandler(self.engine);

        return None;

class ChooseDirectionHandler(EventHandler):
    def __init__(self, engine: Engine, x: int, y: int):
        super().__init__(engine);

        self.x = x;
        self.y = y;

    def on_render(self, console: Console) -> None:
        super().on_render(console);

        console.draw_frame(0, 0, 25, 3);
        console.print(1, 1, "Select a direction...");

    def choose_direction(self, event: tcod.event.KeyDown):
        if event.sym in MOVE_KEYS:
            dx, dy = MOVE_KEYS[event.sym];
            if self.engine.game_map.in_bounds(self.x + dx, self.y + dy):
                print(self.x);
                self.x += dx;
                self.y += dy;

class ChooseCollectDirectionHandler(ChooseDirectionHandler):
    def __init__(self, engine: Engine, x: int, y: int):
        super().__init__(engine, x, y);

    def ev_keydown(self, event: tcod.event.KeyDown) -> Optional[ActionOrHandler]:
        super().choose_direction(event);

        if event.sym in MOVE_KEYS or event.sym in CONFIRM_KEYS:
                inventory_at_location = self.engine.game_map.get_inventory_at_location(self.x, self.y);
                print(inventory_at_location);

                if inventory_at_location:
                    title = f"{inventory_at_location.parent.name}'s Inventory";
                    return InventoryCollectHandler(self.engine, inventory_at_location, title);
                else:
                    return MainGameEventHandler(self.engine);

        if event.sym == tcod.event.K_ESCAPE:
            return MainGameEventHandler(self.engine);

        return None;

class ChooseDialogueDirectionHandler(ChooseDirectionHandler):
    def __init__(self, engine: Engine, x: int, y: int):
        super().__init__(engine, x, y);

    def ev_keydown(self, event: tcod.event.KeyDown) -> Optional[ActionOrHandler]:
        super().choose_direction(event);

        if event.sym in MOVE_KEYS or event.sym in CONFIRM_KEYS:
                dialogue_at_location = self.engine.game_map.get_dialogue_at_location(self.x, self.y);

                if dialogue_at_location:
                    return DialogueEventHandler(dialogue_at_location, self.engine);
                else:
                    return MainGameEventHandler(self.engine);

        if event.sym == tcod.event.K_ESCAPE:
            return MainGameEventHandler(self.engine);

        return None;


class CharacterCreationHandler(EventHandler):
    def __init__(self, engine: Engine, attributes: List[str], points: int):
        super().__init__(engine);
        self.attributes = {};
        for attribute in attributes:
           self.attributes[attribute] = 0;
        self.points = points;
        self.index = 0;

    def on_render(self, console: tcod.Console) -> None:
        super().on_render(console);

        character_console = tcod.Console(console.width - 30, console.height - 30);

        character_console.draw_frame(0, 0, character_console.width, character_console.height, "Character Creation");
        character_console.print(1, 1, "Choose your attributes:");

        y = 2;
        for index, attribute in enumerate(list(self.attributes.keys())):
            bg_color = color.ui_highlight if index == self.index else color.black;
            character_console.print(1, y, f"{attribute.capitalize()}: {self.attributes[attribute]}", bg=bg_color, fg=color.attribute_colors[attribute]);

            y += 2;

        character_console.print(1, y, f"Points remaining: {self.points}");
        if self.points > 0:
            character_console.print(1, y + 1, "You have points remaining. Press r to distribute them randomly.")
        else:
            character_console.print(1, y + 1, "Press Return to finish character creation.");

        character_console.blit(console, 15, 15);

    def ev_keydown(self, event: tcod.event.KeyDown) -> Optional[ActionOrHandler]:
        key = event.sym;
        current_attribute = list(self.attributes.keys())[self.index];

        if key in CURSOR_Y_KEYS:
            self.index = max(0, min(self.index + CURSOR_Y_KEYS[key], len(self.attributes) - 1));

        elif key == tcod.event.K_LEFT:
            if self.attributes[current_attribute] > 0:
                self.attributes[current_attribute] -= 1;
                self.points += 1;
        elif key == tcod.event.K_RIGHT:
            if self.points > 0:
                self.attributes[current_attribute] += 1;
                self.points -= 1;
        elif key in CONFIRM_KEYS:
            if self.points == 0:
                # TODO: assign the attributes to the player
                self.engine.player.attributes = Attributes(self.attributes);
                self.engine.player.fighter.update_stats();
                return MainGameEventHandler(self.engine);
        elif key == tcod.event.K_r:
            for i in range(self.points):
                self.attributes[
                    random.choice(list(self.attributes.keys()))
                ] += 1;
                self.points -= 1;

        return None;

class MapEditorHandler(SelectIndexHandler):
    def __init__(self, engine: Engine):
        self.engine = engine;
        self.char = "#";
        engine.mouse_location = (0, 0);

    def on_render(self, console: tcod.Console) -> None:
        self.engine.render(console);
        super().on_render(console);

    def ev_keydown(self, event: tcod.event.KeyDown) -> Optional[ActionOrHandler]:
        try:
            char = chr(event.sym.value);
        except ValueError:
            char = self.char;

        if char in list(tile_types.tiles_by_char.keys()):
            self.char = char;

        super().ev_keydown(event);

        return None;

    def on_index_selected(self, x: int, y: int) -> None:
        self.engine.game_map.tiles[x, y] = tile_types.tiles_by_char[self.char];

class WalkTowardsHandler(EventHandler):
    def __init__(self, engine: Engine, target: Tuple[int, int]):
        super().__init__(engine);
        self.target = target;
        self.ai = WalkTowards(self.engine.player, self.target);

    def ev_keydown(self, event: tcod.event.KeyDown) -> Optional[ActionOrHandler]:
        if event.sym == tcod.event.K_PERIOD:
            return self.ai.perform();
        else:
            return MainGameEventHandler(self.engine);
