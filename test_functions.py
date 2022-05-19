from __future__ import annotations

import random

import architect
import tile_types
import time
import numpy as np


# TODO if you're so in love with eggs, make them a Feature
class Egg:
    # egg is comprised of center point, width and height radiuses, and how many smoothness passes it will get
    def __init__(self, x, y, width, height, passes):
        self.x, self.y, self.width, self.height, self.passes = x, y, width, height, passes

        # the leftmost, etc. points will be derived.  passes/2 is how much size is added after all passes
        self.left = x - width - (passes / 2)
        self.right = x + width + (passes / 2)
        self.top = y + height + (passes / 2)
        self.bottom = y - height - (passes / 2)

    # TODO sometimes intersecting eggs are still created, investigate
    def intersects(self, egg: Egg) -> bool:
        # if left or right is in the middle of the egg and top or bottom is in the middle of the egg it intersects
        if egg.left <= self.left <= egg.right or egg.left <= self.right <= egg.right:
            if egg.bottom <= self.top <= egg.top or egg.bottom <= self.bottom <= egg.top:
                return True
        return False


# TODO ensure floor is linked using flood fill
def make_egg_map(floor: architect.Feature):
    # reset the map to all wall
    architect.reset_map(floor, denseness=1.0)

    # we want between 1 and 3 eggs, initialize the blank list of them
    egg_count = random.randint(1, 4)
    eggs = []

    # randomly determine how many times we'll smooth it out
    smoothing_passes = random.randint(3, 8)

    while len(eggs) < egg_count:
        # try a random starting point, width, and height in the central area
        egg_x = random.randint(int(floor.width / 4), int(floor.width * 3 / 4))
        egg_y = random.randint(int(floor.height / 4), int(floor.height * 3 / 4))
        egg_width, egg_height = random.randint(2, 5), random.randint(2, 5)

        new_egg = Egg(egg_x, egg_y, egg_width, egg_height, smoothing_passes)
        # compare corners against corners of other eggs to avoid intersection
        if not any(egg.intersects(new_egg) for egg in eggs):
            eggs.append(new_egg)

    # carve out initial rectangles for the eggs
    for egg in eggs:
        floor.tiles[egg.x - egg.width:egg.x + egg.width, egg.y - egg.height:egg.y + egg.height] = tile_types.floor

    # smooth it out a bit
    for i in range(smoothing_passes):
        architect.smooth_it_out(floor)

    for i in range(len(eggs)-1):
        architect.corridor_between(floor, eggs[i].x, eggs[i].y, eggs[i+1].x, eggs[i+1].y)

    # make some long corridors
    corrs = random.randint(3, 8)
    for i in range(corrs):
        length = random.randint(20, 30)
        if not architect.random_corridor(floor, length=length):
            break

    # some medium corridors
    corrs = random.randint(5, 12)
    for i in range(corrs):
        length = random.randint(15, 20)
        if not architect.random_corridor(floor, length=length):
            break

    # and some short corridors
    corrs = random.randint(20, 30)
    for i in range(corrs):
        length = random.randint(8, 15)
        if not architect.random_corridor(floor, length=length):
            break


def make_cavern_map(floor: architect.Feature, denseness: float, smoothness: int, passes: int):
    # initialize the caverns
    architect.reset_map(floor, denseness)
    for i in range(passes):
        architect.smooth_it_out(floor, smoothness)

    # connect adjacent floor segments
    architect.connect_adjacent_segments(floor)

    # find the new floor segments and walls surrounding them
    (floor_segments, boundaries) = architect.floor_segments(floor)

    # find segments that are less than a 100th of the whole map
    to_remove = set()
    for segment in floor_segments:
        if len(segment) < floor.width * floor.height / 100:
            to_remove.add(segment)

    # turn the small floor segments to walls
    for remove in to_remove:
        for (x, y) in remove:
            floor.tiles[x, y] = tile_types.wall
        floor_segments.remove(remove)
        # render_and_sleep(.5, eng, handler)

    floor_segments = tuple(floor_segments)

    # build random corridors to connect all remaining floor segments
    for i in range(len(floor_segments) - 1):
        (startx, starty) = random.choice(floor_segments[i])
        (endx, endy) = random.choice(floor_segments[i + 1])
        architect.corridor_between(floor, startx, starty, endx, endy)
        # render_and_sleep(.5, eng, handler)

    architect.fill_caverns(floor, 4)


def make_winding_map(floor: architect.Feature):
    architect.reset_map(floor)
    floor_changed = True

    # keep smoothing out the map until it reaches static state
    # TODO sometimes this goes infinite and smooths back and forth
    bail_out = 0

    tick = time.perf_counter()
    while floor_changed and bail_out < 60:
        bail_out += 1
        prev_floor = np.copy(floor.tiles)
        architect.smooth_it_out(floor)
        if np.array_equiv(floor.tiles, prev_floor):
            floor_changed = False
    tock = time.perf_counter()
    print(f'smoothing was {tock-tick:.4f}')

    tick = time.perf_counter()
    # build a bunch of corridors
    for i in range(20):
        corr_length = random.randint(10, 21)
        if not architect.random_corridor(floor, corr_length):
            break
    tock = time.perf_counter()
    print(f'corridors was {tock - tick:.4f}')

    tick = time.perf_counter()
    architect.connect_adjacent_segments(floor)
    tock = time.perf_counter()
    print(f'connecting was {tock - tick:.4f}')

    architect.fill_caverns(floor)
