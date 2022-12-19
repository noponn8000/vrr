from typing import Tuple;

import numpy as np;

# Tile graphics structured type compatible with Console.tiles_rgb
graphic_dt = np.dtype(
        [
            ("ch", np.int32), # Unicode codepoint
            ("fg", "3B"), # 3 unsigned bytes for RGB
            ("bg", "3B"),
        ]
);

# Tile struct used for statically defined tile data
tile_dt = np.dtype(
        [
            ("walkable", np.bool), # True if this tile can be walked over
            ("transparent", np.bool), # True if this tile does not block FOV.
            ("dark", graphic_dt), # Graphics for when this tile is not in FOV.
            ("light", graphic_dt), # Graphics for when this tile is in FOV.
        ]
);

def new_tile(
        *, # Enforce the use of keywords in order to ignore parameter order
        walkable: int,
        transparent: int,
        dark: Tuple[int, Tuple[int, int, int], Tuple[int, int, int]],
        light: Tuple[int, Tuple[int, int, int], Tuple[int, int, int]]
) -> np.ndarray:
    """ Helper function for defining individual tile types """
    return np.array((walkable, transparent, dark, light), dtype=tile_dt);

SHROUD = np.array((ord(" "), (255, 255, 255), (0, 0, 0)), dtype=graphic_dt);

floor = new_tile(
        walkable=True, transparent=True, dark=(ord(" "), (255, 255, 255), (50, 50, 150)),
        light=(ord(" "), (255, 255, 255), (200, 100, 50))
);
wall = new_tile(
        walkable=False, transparent=False, dark=(ord(" "), (255, 255, 255), (0, 0, 100)),
        light=(ord(" "), (255, 255, 255), (130, 110, 50))
);
