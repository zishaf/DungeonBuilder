from __future__ import annotations

import random
from typing import TYPE_CHECKING

import architect
import tile
import time
import event_handler

from dungeon_features import Floor, PerfectMaze, PyramidMaze
from engine import Engine

if TYPE_CHECKING:
    pass


def make_egg_map(floor: Floor, eng: Engine, handler: event_handler.EventHandler):
    #reset the map to all wall
    architect.reset_map(floor, denseness=1.0)

    #choose a random starting point in the central third of the map and carve a random rectangle, 4x4 to 10x10
    egg_x = random.randint(int(floor.width/3), int(floor.width*2/3))
    egg_y = random.randint(int(floor.height/3), int(floor.height*2/3))
    egg_width, egg_height = random.randint(4,10), random.randint(4, 10)

    floor.tiles[egg_x:egg_x+egg_width, egg_y:egg_y+egg_height] = tile.floor
    render_and_sleep(.15, eng, handler)

    #smooth it out a bit
    smoothing_passes = random.randint(3, 8)
    for i in range(smoothing_passes):
        architect.smooth_it_out(floor, smoothness=7)
        render_and_sleep(.15, eng, handler)

    #make some long corridors
    corrs = random.randint(3, 8)
    for i in range(corrs):
        length = random.randint(30, 40)
        architect.random_corridor(floor, length=length)
        render_and_sleep(.07, eng, handler)

    #some medium corridors
    corrs = random.randint(8, 14)
    for i in range(corrs):
        length = random.randint(20, 30)
        architect.random_corridor(floor, length=length)
        render_and_sleep(.05, eng, handler)

    #and some short corridors
    corrs = random.randint(50, 60)
    for i in range(corrs):
        length = random.randint(10, 20)
        architect.random_corridor(floor, length=length)
        render_and_sleep(.03, eng, handler)

def random_floor(floor: Floor):
    #reset floor with denseness between .2 and .8
    architect.reset_map(floor, float(random.randint(3,7)/10))

    #randomly decide smoothness level and how many times to smooth the floor
    smoothing_passes, smoothness = random.randint(2, 5), random.randint(4,6)
    for i in range(smoothing_passes):
        architect.smooth_it_out(floor, smoothness)

    #make between 1 and 3 mazes
    mazes = random.randint(1,3)
    for i in range(mazes):
        #randomly determine maze start and size
        searching = True
        maze_x, maze_y, maze_width, maze_height = 0,0,0,0

        #TODO fiddle with ranges, allow larger but make sure there's enough room to build all mazes and no overlap
        while searching:
            maze_x, maze_y = random.randint(1, floor.width-2), random.randint(1, floor.height-2)
            maze_width, maze_height = random.randint(10, 30), random.randint(10,30)
            if  maze_x + maze_width < floor.width - 2 and maze_y + maze_height < floor.height - 2:
                searching = False

        #50/50 of making pyramid maze vs perfect maze
        if random.random() <.5:
            maze = PerfectMaze(maze_width, maze_height)
            floor.tiles[maze_x:maze_x + maze_width, maze_y:maze_y + maze_height] = maze.tiles
        else:
            maze = PyramidMaze(maze_width, maze_height)
            floor.tiles[maze_x:maze_x + maze_width, maze_y:maze_y + maze_height] = maze.tiles


#renders the floor then waits for t seconds
def render_and_sleep(t: float, eng: Engine, handler: event_handler.EventHandler):
    handler.on_render()
    eng.context.present(eng.console)
    time.sleep(t)