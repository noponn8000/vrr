"""Basic"""
white = (0xFF, 0xFF, 0xFF)
black = (0x0, 0x0, 0x0)
red = (0xFF, 0x0, 0x0);

"""Console / Log"""
player_atk = (0xE0, 0xE0, 0xE0)
enemy_atk = (0xFF, 0xC0, 0xC0)
needs_target = (0x3F, 0xFF, 0xFF);
status_effect_applied = (0x3F, 0xFF, 0x3F);
descend = (0x9F, 0x3F, 0xFF);

player_die = (0xFF, 0x30, 0x30)
enemy_die = (0xFF, 0xA0, 0x30)

invalid = (0xFF, 0xFF, 0x00);
impossible = (0x80, 0x80, 0x80);
error = (0xFF, 0x40, 0x40);

welcome_text = (0x20, 0xA0, 0xFF)
health_recovered = (0x0, 0xFF, 0x0);

xp = (20, 150, 20);
level_up = (150, 150, 20);

"""User Interface"""

# Health bar
bar_text = white
bar_filled = (0x0, 0x60, 0x0)
bar_empty = (0x40, 0x10, 0x10)

# Experience bar
xp_bar_filled = (0, 20, 150);
xp_bar_empty = (0, 0, 20);

# Menu
ui_background = (32, 32, 32);
ui_foreground = (220, 220, 220);
ui_highlight = (64, 64, 64);
ui_title = (100, 30, 30);
ui_subtitle = (150, 45, 45);

# Character sheet
vitality = (20, 255, 20);
strength = (255, 120, 40);
resistance = (20, 20, 255);
experience = (20, 20, 255);

attribute_colors = {"vitality": vitality, "strength": strength, "resistance": resistance};

"""Terrain"""
default_wall_light = (100, 30, 30);
default_wall_dark = (50, 15, 15);

default_floor_light = (100, 50, 70);
default_floor_dark  = (15, 5, 10);

"""Entities"""
lightning=(255, 255, 0);
fireball=(255, 0, 0);
confusion=(0, 100, 255);

steel=(20, 20, 30);
leather=(100, 100, 50);
tin=(20, 30, 20);
