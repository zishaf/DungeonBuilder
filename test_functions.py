from __future__ import annotations

import random
from typing import TYPE_CHECKING

import architect
import tile

if TYPE_CHECKING:
    pass


def make_egg_map(floor: architect.Floor):
    #reset the map to all wall
    floor.reset_map(denseness=1.0)

    #choose a random starting point in the central third of the map and carve a random rectangle, 4x4 to 10x10
    egg_x = random.randint(int(handler.game_map.width/3), int(handler.game_map.width*2/3))
    egg_y = random.randint(int(handler.game_map.height/3), int(handler.game_map.height*2/3))
    egg_width, egg_height = random.randint(4,10), random.randint(4, 10)

    handler.game_map.tiles[egg_x:egg_x+egg_width, egg_y:egg_y+egg_height] = tile.floor
    handler.update_console()

    #smooth it out a bit
    smoothing_passes = random.randint(3, 8)
    for i in range(smoothing_passes):
        architect.smooth_it_out(handler.game_map, smoothness=7)
    handler.update_console()

    #make some long corridors
    corrs = random.randint(3, 8)
    for i in range(corrs):
        length = random.randint(30, 40)
        architect.random_corridor(handler.game_map, length=length)
    handler.update_console()

    #some medium corridors
    corrs = random.randint(8, 14)
    for i in range(corrs):
        length = random.randint(20, 30)
        architect.random_corridor(handler.game_map, length=length)
    handler.update_console()

    #and some short corridors
    corrs = random.randint(50, 60)
    for i in range(corrs):
        length = random.randint(10, 20)
        architect.random_corridor(handler.game_map, length=length)
    handler.update_console()