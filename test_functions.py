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


class Egg():
    # egg is comprised of center point, width and height radiuses, and how many smoothness passes it will get
    def __init__(self, x, y, width, height, passes):
        self.x, self.y, self.width, self.height, self.passes = x, y, width, height, passes

        # the leftmost, etc. points will be derived.  passes/2 is how much size is added after all passes
        self.left = x - width - (passes / 2)
        self.right = x + width + (passes / 2)
        self.top = y + height + (passes / 2)
        self.bottom = y - height - (passes / 2)

    #TODO sometimes intersecting eggs are still created, investigate
    def intersects(self, egg: Egg) -> bool:
        # if left or right is in the middle of the egg and top or bottom is in the middle of the egg it intersects
        if egg.left <= self.left <= egg.right or egg.left <= self.right <= egg.right:
            if egg.bottom <= self.top <= egg.top or egg.bottom <= self.bottom <= egg.top:
                return True
        return False


def make_egg_map(floor: Floor, eng: Engine, handler: event_handler.EventHandler):
    #reset the map to all wall
    architect.reset_map(floor, denseness=1.0)

    #we want between 1 and 3 eggs, initialize the blank list of them
    egg_count = random.randint(1, 4)
    eggs = []

    #randomly determine how many times we'll smooth it out
    smoothing_passes = random.randint(3, 8)


    while len(eggs) < egg_count:
        #try a random starting point, width, and height in the central area
        egg_x = random.randint(int(floor.width / 4), int(floor.width * 3 / 4))
        egg_y = random.randint(int(floor.height / 4), int(floor.height * 3 / 4))
        egg_width, egg_height = random.randint(2, 5), random.randint(2, 5)

        new_egg = Egg(egg_x, egg_y, egg_width, egg_height, smoothing_passes)
        #compare corners against corners of other eggs to avoid intersection
        if not any(egg.intersects(new_egg) for egg in eggs):
            eggs.append(new_egg)

    #carve out initial rectangles for the eggs
    for egg in eggs:
        floor.tiles[egg.x-egg.width:egg.x+egg.width, egg.y-egg_height:egg.y+egg.height] = tile.floor
    render_and_sleep(.15, eng, handler)

    #smooth it out a bit
    for i in range(smoothing_passes):
        architect.smooth_it_out(floor, smoothness=7)
        render_and_sleep(.15, eng, handler)

    #make some long corridors
    corrs = random.randint(3, 8)
    for i in range(corrs):
        length = random.randint(30, 40)
        architect.random_corridor(floor, length=length)
        render_and_sleep(.05, eng, handler)

    #some medium corridors
    corrs = random.randint(8, 14)
    for i in range(corrs):
        length = random.randint(20, 30)
        architect.random_corridor(floor, length=length)
        render_and_sleep(.03, eng, handler)

    #and some short corridors
    corrs = random.randint(30, 40)
    for i in range(corrs):
        length = random.randint(10, 20)
        architect.random_corridor(floor, length=length)
        render_and_sleep(.01, eng, handler)


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
        maze = PerfectMaze(maze_width, maze_height) if random.random() <.5 else PyramidMaze(maze_width, maze_height)

        floor.tiles[maze_x:maze_x + maze_width, maze_y:maze_y + maze_height] = maze.tiles


#renders the floor then waits for t seconds
def render_and_sleep(t: float, eng: Engine, handler: event_handler.EventHandler):
    handler.on_render()
    eng.context.present(eng.console)
    time.sleep(t)


def make_cavern_map(floor: Floor, denseness: float, smoothness: int, passes: int, eng: Engine, handler: event_handler.EventHandler):
    #initialize the caverns
    architect.reset_map(floor, denseness)
    for i in range(passes):
        architect.smooth_it_out(floor, smoothness)
        render_and_sleep(.1, eng, handler)

    #connect adjacent floor segments
    architect.connect_adjacent_segments(floor)

    #find the new floor segments and walls surrounding them
    (floor_segments, boundaries) = architect.floor_segments(floor)

    #find segments that are less than a 100th of the whole map
    to_remove = set()
    for segment in floor_segments:
        if len(segment) < floor.width*floor.height/100:
            to_remove.add(segment)

    #turn the small floor segments to walls
    for remove in to_remove:
        for (x, y) in remove:
            floor.tiles[x, y] = tile.wall
        floor_segments.remove(remove)
        render_and_sleep(.5, eng, handler)

    floor_segments = tuple(floor_segments)

    #build random corridors to connect all remaining floor segments
    for i in range(len(floor_segments) - 1):
        (startx, starty) = random.choice(floor_segments[i])
        (endx, endy) = random.choice(floor_segments[i+1])
        architect.corridor_between(floor, startx, starty, endx, endy)
        render_and_sleep(.5, eng, handler)

    architect.fill_caverns(floor, 4)


def make_winding_map(floor: Floor, eng: Engine, handler: event_handler.EventHandler):
    architect.reset_map(floor)
    floor_changed = True

    #keep smoothing out the map until it reaches static state
    #TODO sometimes this goes infinite and smooths back and forth
    while floor_changed:
        prev_floor = floor.tiles.copy()
        architect.smooth_it_out(floor)
        render_and_sleep(.05, eng, handler)
        if (floor.tiles == prev_floor).all():
            floor_changed = False

    #build a bunch of corridors
    for i in range(20):
        render_and_sleep(.05, eng, handler)
        corr_length = random.randint(10, 21)
        architect.random_corridor(floor, corr_length)

    render_and_sleep(.2, eng, handler)
    architect.connect_adjacent_segments(floor)

    render_and_sleep(.3, eng, handler)
    architect.fill_caverns(floor)
