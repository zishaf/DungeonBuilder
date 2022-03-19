from typing import Tuple
import colors

import numpy as np  # type: ignore

# lifted and slightly edited from tutorial http://rogueliketutorials.com/tutorials/tcod/v2/

# graphics include int reference to spot on tileset, and two sets of three bytes numbers for color
graphic_dt = np.dtype(
    [
        ("ch", np.int32),
        ("fg", "3B"),
        ("bg", "3B"),
    ]
)

tile_dt = np.dtype(
    [
        ("walkable", np.bool),
        ("transparent", np.bool),
        ("cost", np.int8),
        ("light", graphic_dt),
        ("dark", graphic_dt),
    ]
)


# helper function to initialize new tiles
def new_tile(
        *,
        walkable: int,
        transparent: int,
        cost: int,
        light: Tuple[int, Tuple[int, int, int], Tuple[int, int, int]],
        dark: Tuple[int, Tuple[int, int, int], Tuple[int, int, int]],
) -> np.ndarray:
    return np.array((walkable, transparent, cost, light, dark), dtype=tile_dt)


SHROUD = np.array((ord(" "), (0, 0, 0), (20, 20, 20)), dtype=graphic_dt)

floor = new_tile(
    walkable=True,
    transparent=True,
    cost=1,
    light=(46, colors.GREY, colors.DARK_GREY),
    dark=(46, colors.DARK_GREY, colors.BLACK)
)

wall = new_tile(
    walkable=False,
    transparent=False,
    cost=0,
    light=(127, colors.CRYSTAL, colors.DARK_GREY),
    dark=(127, colors.DARK_CRYSTAL, colors.BLACK)
)

filled = new_tile(
    walkable=False,
    transparent=True,
    cost=1,
    light=(3, colors.WHITE, colors.BLACK),
    dark=(3, colors.WHITE, colors.BLACK)
)

down_stairs = new_tile(
    walkable=True,
    transparent=True,
    cost=1,
    light=(25, colors.WHITE, colors.DARK_GREY),
    dark=(25, colors.GREY, colors.BLACK)
)

acid = new_tile(
    walkable=True,
    transparent=True,
    cost=1,
    light=(176, colors.ACID_GREEN, colors.DARK_GREY),
    dark=(176, colors.OLIVE_GREEN, colors.BLACK)
)
