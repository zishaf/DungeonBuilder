from __future__ import annotations

from typing import TYPE_CHECKING

import tile

if TYPE_CHECKING:
    from engine import Engine

class GodBargain:
    def __init__(self, description: str, cost: int, func):
        self.description, self.cost, self.func = description, cost, func

def activate_see_through_walls(engine: Engine):
    engine.player.flags["see_through_walls"] = True

def activate_one_eyed(engine: Engine):
    engine.player.flags["one_eyed"] = True

def activate_see_stairs(engine: Engine):
    engine.player.flags["see_stairs"] = True
    for x in range(1, engine.game_map.width-1):
        for y in range(1, engine.game_map.height-1):
            if engine.game_map.tiles[x, y] == tile.maze_ext:
                engine.game_map.explored[x, y] = True

see_through_walls = GodBargain("The power to see through walls~~~", 200, activate_see_through_walls)
one_eyed = GodBargain("Lose an eye .(", -400, activate_one_eyed)
see_stairs = GodBargain("Sense the exit", 200, activate_see_stairs)