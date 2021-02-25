from typing import Tuple

import numpy as np  # type: ignore

#TODO bug where holding space, enter, etc. doesn't continuously update console.
#lifted and slightly edited from tutorial

#graphics include int reference to spot on tileset, and two sets of three bytes numbers for color
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
        ("graphic", graphic_dt),
    ]
)

#helper function to initialize new tiles
def new_tile(
        *,
        walkable: int,
        transparent: int,
        cost: int,
        graphic: Tuple[int, Tuple[int, int, int], Tuple[int, int, int]],
) -> np.ndarray:
    return np.array((walkable, transparent, cost, graphic), dtype=tile_dt)

floor = new_tile(
    walkable=True,
    transparent=True,
    cost=1,
    graphic=(46, (150, 150, 150), (30, 30, 30))
)

wall = new_tile(
    walkable=False,
    transparent=True,
    cost=0,
    graphic=(127, (116, 94, 162), (20, 20, 20))
)