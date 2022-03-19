from __future__ import annotations

import random
from typing import TYPE_CHECKING

import architect
import tile_types
import time
import numpy as np
import entity_maker

if TYPE_CHECKING:
    pass

BAD_PAIRS = [{'top_left', 'bot_right'}, {'top_right', 'bot_left'}]


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
        architect.smooth_it_out(floor, smoothness=7)

    for i in range(len(eggs)-1):
        architect.corridor_between(floor, eggs[i].x, eggs[i].y, eggs[i+1].x, eggs[i+1].y)
    tick = time.perf_counter()
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
    tock = time.perf_counter()
    print(f"making the corridors took {tock-tick:4f} seconds")


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


def make_floor(width: int, height: int, player: entity_maker.Player = None) -> architect.Floor:

    floor = architect.Floor(width, height)
    if player is not None:
        floor.entities.append(player)

    x_divider = random.randint(20, width-20)
    y_divider = random.randint(20, height-20)

    floor.features['top_left'] = architect.Feature(x_divider+1, y_divider+1, 0, 0)
    floor.features['top_right'] = architect.Feature(width-x_divider, y_divider+1, x_divider, 0)
    floor.features['bot_left'] = architect.Feature(x_divider+1, height-y_divider, 0, y_divider)
    floor.features['bot_right'] = architect.Feature(width-x_divider, height-y_divider, x_divider, y_divider)

    # TODO make this, along with everything else, a probability table based on depth
    feature_types = ['maze', 'cavern', 'winding', 'egg']

    maze_feature: str = ''
    non_mazes = []

    # feature is the name of the feature: i.e. 'top_left'.  cur_feature is the value held at that key
    for feature in floor.features:
        feature_type = random.choice(feature_types)
        cur_feature = floor.features[feature]
        tick = time.perf_counter()

        # dictionaries only give a view of their values or smthng
        if feature_type == 'maze':
            floor.features[feature] = architect.make_maze(cur_feature.width, cur_feature.height, cur_feature.x, cur_feature.y)
            maze_feature = feature
            make_maze_exit(maze=floor.features[feature], location=feature)
            feature_types.remove('maze')

        else:
            non_mazes.append(feature)

            if feature_type == 'winding':
                make_winding_map(cur_feature)
            elif feature_type == 'cavern':
                make_cavern_map(cur_feature, .5, 5, 6)
            elif feature_type == 'egg':
                make_egg_map(cur_feature)
                stair_coords = random.choice(np.argwhere(cur_feature.tiles == tile_types.floor))
                cur_feature.tiles[stair_coords[0], stair_coords[1]] = tile_types.down_stairs

        tock = time.perf_counter()
        print(f"{feature_type} of size {cur_feature.width}x{cur_feature.height} took {tock-tick:4f} seconds.")

    # set the floor tiles from its newly built features
    for feature in floor.features.values():
        floor.tiles[feature.x:feature.x+feature.width , feature.y:feature.y+feature.height] = feature.tiles

    # connect non-maze and non-diagonal features (two times each, loop double checks pairs)
    for feature_one in floor.features:
        for feature_two in floor.features:
            if feature_one == feature_two:
                continue
            if {feature_one, feature_two} not in BAD_PAIRS:
                if feature_one is maze_feature:
                    xy_one = [floor.features[feature_one].ent_x, floor.features[feature_one].ent_y]
                else:
                    xy_one = random.choice(np.argwhere(floor.features[feature_one].tiles == tile_types.floor))
                x1, y1 = xy_one[0] + floor.features[feature_one].x, xy_one[1] + floor.features[feature_one].y
                if feature_two is maze_feature:
                    xy_two = [floor.features[feature_two].ent_x, floor.features[feature_two].ent_y]
                else:
                    xy_two = random.choice(np.argwhere(floor.features[feature_two].tiles == tile_types.floor))
                x2, y2 = xy_two[0] + floor.features[feature_two].x, xy_two[1] + floor.features[feature_two].y
                architect.corridor_between(floor, x1, y1, x2, y2)

    stair_count = 2 if not maze_feature == '' else 3

    for i in range(stair_count):
        choice = random.choice(non_mazes)
        stair_coords = random.choice(np.argwhere(floor.features[choice].tiles == tile_types.floor))
        floor.tiles[stair_coords[0]+floor.features[choice].x, stair_coords[1]+floor.features[choice].y] = tile_types.down_stairs

    # add nu piles to every feature, more to maze features.  then move entities from features to parent floor
    for feature_name in floor.features:
        feature = floor.features[feature_name]

        if feature_name is maze_feature:
            architect.add_nu_piles(feature, 40)
        else:
            architect.add_nu_piles(feature, 15)

        for entity in feature.entities:
            entity.x += feature.x
            entity.y += feature.y
            floor.entities.append(entity)
            feature.entities.remove(entity)

    return floor


def make_maze_exit(maze: architect.Maze, location: str):
    x1, y1, x2, y2 = maze.ent_x, maze.ent_y, maze.ext_x, maze.ext_y

    # based on location see if we need to swap entrance and exit
    if location == 'top_left':
        if x1 == 0 or y1 == 0:
            maze.ent_x, maze.ent_y, maze.ext_x, maze.ext_y = x2, y2, x1, y1
    elif location == 'top_right':
        if x1 == maze.width-1 or y1 == 0:
            maze.ent_x, maze.ent_y, maze.ext_x, maze.ext_y = x2, y2, x1, y1
    elif location == 'bot_left':
        if x1 == 0 or y1 == maze.height-1:
            maze.ent_x, maze.ent_y, maze.ext_x, maze.ext_y = x2, y2, x1, y1
    elif location == 'bot_right':
        if x1 == maze.width-1 or y1 == maze.height-1:
            maze.ent_x, maze.ent_y, maze.ext_x, maze.ext_y = x2, y2, x1, y1

    # exit is a down stairs with a big nu pile next to it
    maze.tiles[maze.ext_x, maze.ext_y] = tile_types.down_stairs
    for x, y in architect.neighbor_coords(maze.ext_x, maze.ext_y):
        if maze.in_bounds(x, y) and maze.tiles[x, y] == tile_types.floor:
            maze.entities.append(entity_maker.NuPile(maze, x, y, 100))
