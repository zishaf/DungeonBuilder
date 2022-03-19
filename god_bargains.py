from __future__ import annotations
from typing import TYPE_CHECKING

import tile_types

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
    for xy in engine.game_map.coords_of_tile_type(tile_types.down_stairs):
        engine.game_map.explored[xy[0], xy[1]] = True


def activate_teleportitis(engine: Engine):
    engine.player.flags["teleportitis"] = True


see_through_walls = GodBargain("The power to see through walls~~~", 100, activate_see_through_walls)
one_eyed = GodBargain("Lose an eye .(", -100, activate_one_eyed)
see_stairs = GodBargain("Sense the exit", 100, activate_see_stairs)
teleportitis = GodBargain("Randomly teleport", -50, activate_teleportitis)
