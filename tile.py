from typing import Tuple

import numpy as np #type: ignore
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
        ("graphic", graphic_dt),
    ]
)

#helper function to initialize new tiles
def new_tile(
        *,
        walkable: int,
        transparent: int,
        graphic: Tuple[int, Tuple[int, int, int], Tuple[int, int, int]],
) -> np.ndarray:
    return np.array((walkable, transparent, graphic), dtype=tile_dt)


floor = new_tile(
    walkable=True,
    transparent=True,
    graphic=(46, (150, 150, 150), (30, 30, 30))
)

wall = new_tile(
    walkable=False,
    transparent=True,
    graphic=(127, (116, 94, 162), (20, 20, 20))
)



"""my effort at Tile class
from typing import Tuple

class Tile():
    def __init__(
            self, char: int,
            fg: Tuple[int, int, int]=(255, 255, 255),
            bg: Tuple[int, int, int]=(0, 0, 0),
    ):
        self.char = char
        self.fg = fg
        self.bg = bg

WALL  = Tile(127, (169, 153, 255), (20, 20, 20))
FLOOR = Tile(46, (150, 150, 150), (30, 30, 30))"""