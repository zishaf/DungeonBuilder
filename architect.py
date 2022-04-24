from __future__ import annotations


import random
import time

import numpy as np
import tile_types

from itertools import product
from typing import Tuple, List
from entity_maker import NuPile, Monster


def neighbor_coords(x: int, y: int) -> List[tuple[int, int]]:
    return [(x - 1, y), (x + 1, y), (x, y - 1), (x, y + 1)]


class Feature:
    def __init__(self, width: int, height: int, x: int = 0, y: int = 0, entities: list = None):
        self.entities = [] if entities is None else entities
        self.tiles = np.full((width, height), fill_value=tile_types.wall, order="F")
        self.width, self.height = width, height
        self.x, self.y = x, y
        self.visible, self.explored = None, None

    def in_bounds(self, x, y) -> bool:
        return 0 < x < self.width - 1 and 0 < y < self.height - 1

    """def cells_centered_on(self, x: int, y: int, r: int = 1) -> np.ndarray:
        # gets slice of floor tiles based on radius. uses min, max to avoid out of bounds tiles in one fancy line
        return self.tiles[max(x - r, 0): min(x + r + 1, self.width), max(y - r, 0): min(y + r + 1, self.height)]"""

    def cells_centered_on(self, x: int, y: int, r: int = 1) -> np.ndarray:
        return self.tiles[x - r:x + r + 1, y - r: y + r + 1]

    def diagonal_tile_count(self, x: int, y: int, r: int = 1, tile_type: tile_types.tile_dt = tile_types.wall) -> int:
        # counts walls in given radius of cells centered on x, y
        return np.count_nonzero(self.cells_centered_on(x, y, r) == tile_type)

    def adjacent_tiles(self, x, y) -> np.ndarray:
        return np.asarray([self.tiles[i, j] for (i, j) in neighbor_coords(x, y)]) if self.in_bounds(x, y) else None

    def cardinal_walls(self, x: int, y: int) -> int:
        return np.count_nonzero(self.adjacent_tiles(x, y) == tile_types.wall)

    def hide_tiles(self):
        self.visible = np.zeros((self.width, self.height), order="F", dtype=bool)
        self.explored = np.zeros((self.width, self.height), order="F", dtype=bool)

    def reveal_tiles(self):
        self.visible = np.ones((self.width, self.height), order="F", dtype=bool)
        self.explored = np.ones((self.width, self.height), order="F", dtype=bool)

    def can_corridor(self, x: int, y: int, blobulousness: int = 0) -> bool:
        # can dig corridor if the tile is in bounds, is a wall, and has enough adjacent walls
        # awkward calculation with blobulation because I like the var name and think it should start from 0
        return self.in_bounds(x, y) and self.tiles[x, y] == tile_types.wall and self.cardinal_walls(x, y) > 2 - blobulousness

    def coords_of_tile_type(self, tile_type: tile_types.tile_dt) -> np.ndarray:
        return np.argwhere(self.tiles == tile_type)


class Floor(Feature):
    def __init__(self, width: int, height: int, entities=None, features=None):
        super().__init__(width, height)
        self.features = [] if features is None else features
        self.features = {
            'top_left': None,
            'top_right': None,
            'bot_left': None,
            'bot_right': None
        }
        self.hide_tiles()


class Pyramid(Feature):
    def __init__(self, width: int, height: int, x: int = 0, y: int = 0):
        super().__init__(width, height, x, y)
        self.carve()

    def carve(self):
        # sets a ring of floor tiles every two tiles, stops at half of width or height
        for i in range(1, min(int(self.width / 2), int(self.height / 2)), 2):
            # make the 4 walls that form a ring
            self.tiles[i:self.width - i, i] = tile_types.floor  # top
            self.tiles[i:self.width - i, self.height - i - 1] = tile_types.floor  # bottom
            self.tiles[i, i:self.height - i] = tile_types.floor  # left
            self.tiles[self.width - i - 1, i:self.height - i] = tile_types.floor  # right
            self.make_passage(i)

    def make_passage(self, i: int):
        # carves one random tile between two rings, equal chance for each tile, won't choose a corner
        walls = {
            "top": self.tiles[i + 2:self.width - i - 2, i + 1],
            "bottom": self.tiles[i + 2:self.width - i - 2, self.height - i - 2],
            "left": self.tiles[i + 1, i + 2:self.height - i - 2],
            "right": self.tiles[self.width - i - 2, i + 2:self.height - i - 2]
        }

        # don't carve if any list has length 0, that means center has been reached
        if all(len(lst) > 0 for lst in walls.values()):

            # chicanery with lists' total length and slices so I can use view of array instead of copy
            choice = random.randrange(0, sum(len(lst) for lst in walls.values()))

            for wall in walls.values():
                if choice < len(wall):
                    wall[choice] = tile_types.floor
                    return
                else:
                    choice -= (len(wall))


# TODO Move mazes entrances, exits.  The creation of those will be left to a "feature connector" function
class Maze(Feature):
    def __init__(self, width: int, height: int, x: int = 0, y: int = 0):
        super().__init__(width, height, x, y)
        self.tiles = np.full((width, height), fill_value=tile_types.floor, order="F")
        self.fill_border()
        self.ent_x, self.ent_y, self.ext_x, self.ext_y = None, None, None, None

    def fill_border(self):
        # use a step of width/height - 1 to get two edge values in one pass. Save two lines! Minus one for the comment
        self.tiles[0:self.width, 0:self.height:self.height - 1] = tile_types.wall
        self.tiles[0:self.width:self.width - 1, 0:self.height] = tile_types.wall

    # TODO rewooooooork
    def add_entrances(self) -> tuple[tuple[int, int], tuple[int, int]]:
        wall_one_choices = []
        wall_two_choices = []
        if random.random() < 0.5:
            for y in range(1, self.height - 1):
                if self.tiles[1, y] == tile_types.floor:
                    wall_one_choices.append((0, y))
                if self.tiles[self.width - 2, y] == tile_types.floor:
                    wall_two_choices.append((self.width - 1, y))
        else:
            for x in range(1, self.width - 1):
                if self.tiles[x, 1] == tile_types.floor:
                    wall_one_choices.append((x, 0))
                if self.tiles[x, self.height - 2] == tile_types.floor:
                    wall_two_choices.append((x, self.height - 1))

        ent_x, ent_y = random.choice(wall_one_choices)
        ext_x, ext_y = random.choice(wall_two_choices)

        self.tiles[ent_x, ent_y] = tile_types.floor
        self.tiles[ext_x, ext_y] = tile_types.floor

        return (ent_x, ent_y), (ext_x, ext_y)


class PerfectMaze(Maze):
    def __init__(self, width: int, height: int, x: int = 0, y: int = 0):
        super().__init__(width, height, x, y)

        self.add_walls()
        self.clean_2x2()
        (self.ent_x, self.ent_y), (self.ext_x, self.ext_y) = self.add_entrances()

    def add_walls(self):
        choices = []

        # TODO change the directions' order to up, right, down, left
        # start will be the outermost ring, excluding corners. add x, y and direction 1,2,3,4 as up,down,left,right
        for x in range(1, self.width - 1):
            choices.extend([(x, 1, 3), (x, self.height - 2, 1)])
        for y in range(1, self.height - 1):
            choices.extend([(1, y, 2), (self.width - 2, y, 4)])

        while choices:
            x, y, direction = random.choice(choices)
            choices.remove((x, y, direction))
            if np.count_nonzero(self.adjacent_tiles(x, y) == tile_types.wall) == 1 \
                    and self.tiles[x, y] == tile_types.floor \
                    and self.check_diagonals(x, y, direction):
                self.tiles[x, y] = tile_types.wall
                choices.extend([(x + 1, y, 2), (x - 1, y, 4), (x, y + 1, 3), (x, y - 1, 1)])

    def check_diagonals(self, x, y, direction) -> bool:
        if direction == 1:
            return self.tiles[x - 1, y - 1] == tile_types.floor and self.tiles[x + 1, y - 1] == tile_types.floor
        elif direction == 3:
            return self.tiles[x - 1, y + 1] == tile_types.floor and self.tiles[x + 1, y + 1] == tile_types.floor
        elif direction == 2:
            return self.tiles[x + 1, y + 1] == tile_types.floor and self.tiles[x + 1, y - 1] == tile_types.floor
        elif direction == 4:
            return self.tiles[x - 1, y + 1] == tile_types.floor and self.tiles[x - 1, y - 1] == tile_types.floor

    # any 2x2 of floor tiles should have one corner filled to make good, claustrophobic hallways
    def clean_2x2(self):
        for x in range(1, self.width - 1):
            for y in range(1, self.height - 1):
                if all(i == tile_types.floor for i in self.tiles[x:x + 2, y:y + 2].flatten()):
                    self.fill_corner(x, y)

    # picks a corner to fill that won't block off the maze
    def fill_corner(self, x: int, y: int):
        corners = []
        if self.tiles[x - 1, y] == tile_types.wall and self.tiles[x, y - 1] == tile_types.wall:
            corners.append((x, y))
        if self.tiles[x - 1, y + 1] == tile_types.wall and self.tiles[x, y + 2] == tile_types.wall:
            corners.append((x, y + 1))
        if self.tiles[x + 1, y - 1] == tile_types.wall and self.tiles[x + 2, y] == tile_types.wall:
            corners.append((x + 1, y))
        if self.tiles[x + 2, y + 1] == tile_types.wall and self.tiles[x + 1, y + 2] == tile_types.wall:
            corners.append((x + 1, y + 1))
        if corners:
            x, y = random.choice(corners)
            self.tiles[x, y] = tile_types.wall


# TODO BraidMazes could be loopier if we find a way to remove some 2x2s that are counting as loops
class BraidMaze(Maze):
    def __init__(self, width: int, height: int, x: int = 0, y: int = 0):
        super().__init__(width, height, x, y)
        self.add_walls()
        (self.ent_x, self.ent_y), (self.ext_x, self.ext_y) = self.add_entrances()

    def add_walls(self):
        # make a list of tuples out of all combinations of coordinates (except outer walls) and shuffle it
        floor_spaces = list(product(range(1, self.width - 1), range(1, self.height - 1)))
        random.shuffle(floor_spaces)

        # try to add a wall at every coordinate if it will not cause any dead ends out of neighboring floor tiles
        while floor_spaces:
            x, y = floor_spaces.pop()
            if not any(self.causes_dead_ends(i, j) for (i, j) in neighbor_coords(x, y)):
                self.tiles[x, y] = tile_types.wall
        # connect the floor
        connect_adjacent_segments(self)

    def causes_dead_ends(self, x: int, y: int) -> bool:
        return self.tiles[x, y] == tile_types.floor and self.cardinal_walls(x, y) > 1


def smooth_it_out(floor: Feature, smoothness: int = 5):
    # converts each cell to its most common neighbor, a higher smoothness means fewer walls
    new_floor = floor.tiles.copy(order="F")
    time.perf_counter()
    for x in range(1, floor.width - 1):
        for y in range(1, floor.height - 1):
            new_floor[x, y] = tile_types.wall if floor.diagonal_tile_count(x, y) >= smoothness else tile_types.floor
    floor.tiles = new_floor


def new_smooth(feature: Feature, smoothness: int = 5):
    tick = time.perf_counter()

    bogdown=1

    smoothed_floor = np.full((feature.width, feature.height), tile_types.wall, dtype=tile_types.tile_dt, order='F')
    for (x, y), tile in np.ndenumerate(feature.tiles[1:feature.width-1, 1:feature.height-1]):
        bogdown+=1
        """if feature.diagonal_tile_count(x+1, y+1) < smoothness:
            smoothed_floor[x+1, y+1] = tile_types.floor"""

    feature.tiles = smoothed_floor

    tock = time.perf_counter()
    print(f"new smooth in {tock - tick:4f} sec")


def fill_caverns(floor: Feature, radius: int = 2):
    # make wall tiles anywhere there are no other wall tiles within the given radius
    new_floor = floor.tiles.copy(order="F")

    for xy in floor.coords_of_tile_type(tile_types.floor):
        if floor.diagonal_tile_count(xy[0], xy[1], r=radius) == 0:
            new_floor[xy[0], xy[1]] = tile_types.wall

    floor.tiles = new_floor


def reset_map(floor: Feature, denseness: float = 0.5):
    # randomly assigns every non-edge tile as wall or floor
    for x in range(1, floor.width - 1):
        for y in range(1, floor.height - 1):
            floor.tiles[x, y] = tile_types.wall if random.random() < denseness else tile_types.floor


def fast_corridor(floor: Feature, length: int) -> bool:
    # make a set of possible starting points
    starts = list(floor.valid_starts())
    random.shuffle(starts)
    # pop random coords as starting points and see if a corridor can be made
    while starts:
        # get our starting point
        x, y = starts.pop()

        # the current corridor will store the coordinates, the dests will store corresponding available directions
        curr_corr: list[Tuple[int, int]] = [(x, y)]
        directions: list[List] = [[0, 1, 2, 3]]

        # randomly walk until corridor is long enough or impossible
        while curr_corr and len(curr_corr) < length:
            x, y = curr_corr[-1]
            # make a list of the adjacent tiles as possible destinations
            cardinals = [(x, y + 1), (x + 1, y), (x, y - 1), (x - 1, y)]

            # if there are no more directions to try then we've reached a dead end, remove the most recent tile
            if not directions[-1]:
                curr_corr.pop()
                directions.pop()

            else:
                # pop arbitrarily from most recent direction set and compare with cardinals to set x and y destination
                direction = random.choice(directions[-1])
                directions[-1].remove(direction)
                x_dest, y_dest = cardinals[direction]

                # make sets from current corridor squares and adjacent tiles and finds length of overlap
                destination_tiles = {(x_dest, y_dest + 1), (x_dest + 1, y_dest), (x_dest, y_dest - 1),
                                     (x_dest - 1, y_dest)}
                overlapping_tiles = len(set(curr_corr) & destination_tiles)

                # check that destination is in bounds, surrounded by walls, and only touches one tile of the corridor
                if floor.in_bounds(x_dest, y_dest) and floor.cardinal_walls(x_dest,
                                                                            y_dest) == 4 and overlapping_tiles == 1:
                    # if so, we add the destination to the corridor with a fresh set of available directions
                    curr_corr.append((x_dest, y_dest))
                    directions.append([0, 1, 2, 3])
                    # remove the opposite direction from possible ways this can go
                    directions[-1].remove((direction + 2) % 4)

        # if the corridor is long make all the tiles floors
        if len(curr_corr) == length:
            for x, y in curr_corr:
                floor.tiles[x, y] = tile_types.floor
            return True

    # no start worked
    return False


# TODO rework random_corridor/tunnel function with stack, currently hangs on hard-to-find tunnels
def random_corridor(floor: Feature, length: int, blobulousness: int = 0) -> bool:
    # make a list of all possible starting points and shuffle it
    wall_coords = floor.coords_of_tile_type(tile_types.wall)
    starts = []
    for xy in wall_coords:
        if floor.in_bounds(xy[0], xy[1]) and floor.cardinal_walls(xy[0], xy[1]) == 3:
            starts.append((xy[0], xy[1]))
    random.shuffle(starts)

    # try to tunnel a corridor with length-1 since x,y will be the first tile
    while starts:
        x, y = starts.pop()
        if tunnel(floor, length - 1, x, y, blobulousness):
            return True
    return False


def tunnel(floor: Feature, length: int, x: int, y: int, blobulousness: int = 0) -> bool:
    # mark our tile
    floor.tiles[x, y] = tile_types.floor

    # return true if we've reached target length
    if length == 0:
        return True

    # this line makes it so a corridor will loop on to itself for the last possible tile, and be slightly less strict.
    b = blobulousness + 1 if length == 1 else blobulousness

    # add all neighbors to destinations, shuffle the list to build in random direction
    dests = neighbor_coords(x, y)
    random.shuffle(dests)

    # check all destinations and return true if they reach their conclusion, else reset the tile
    for destx, desty in dests:
        if floor.can_corridor(destx, desty, b):
            if tunnel(floor, length - 1, destx, desty, b):
                return True
            else:
                floor.tiles[destx, desty] = tile_types.wall

    # reset the starting tile if all fails and return false
    floor.tiles[x, y] = tile_types.wall

    return False


# TODO make it a scan line fill so it's faster!
def flood_fill_floor(floor: Feature, x: int, y: int, ) -> (tuple[Tuple[int, int]], tuple[Tuple[int, int]]):
    # flood fill will default to look for its starting tile if no value is given
    # if tile_type is None: tile_type = floor.tiles[x, y]

    # will call flood_fill on a tiles in the stack and add them to filled
    stack: list[Tuple[int, int]] = [(x, y)]
    filled: set[Tuple[int, int]] = set()
    boundaries: set[Tuple[int, int]] = set()

    # check coords to see if they are unmarked floors, if it's a wall it's a boundry and stored seperately
    while stack:
        x, y = stack.pop()
        if floor.tiles[x, y] == tile_types.wall:
            boundaries.add((x, y))

        elif (x, y) not in filled:
            filled.add((x, y))
            stack.extend([(x - 1, y), (x + 1, y), (x, y - 1), (x, y + 1)])

    return tuple(filled), tuple(boundaries)


def corridor_between(floor: Feature, startx: int, starty: int, endx: int, endy: int):
    if floor.tiles[startx, starty] == tile_types.wall:
        floor.tiles[startx, starty] = tile_types.floor

    if startx == endx and starty == endy:
        return

    choices = list()
    left, right, up, down = (startx - 1, starty), (startx + 1, starty), (startx, starty - 1), (startx, starty + 1)

    if starty == endy and abs(startx - endx) > 2:
        choices.append(up)
        choices.append(down)

    if startx == endx and abs(starty - endy) > 2:
        choices.append(left)
        choices.append(right)

    if endx < startx: choices.append(left)
    if endx > startx: choices.append(right)
    if endy < starty: choices.append(up)
    if endy > starty: choices.append(down)
    dest = random.choice(choices)

    if dest is up and starty > 1: starty -= 1
    if dest is right and startx < floor.width - 2: startx += 1
    if dest is down and starty < floor.height - 2: starty += 1
    if dest is left and startx > 1: startx -= 1

    corridor_between(floor, startx, starty, endx, endy)


# returns the coordinates (in order) above, right, below, and left of the given coordinates
def cardinal_coords(x, y) -> list[Tuple[int, int]]:
    return [(x, y + 1), (x + 1, y), (x, y - 1), (x - 1, y)]


# TODO make different maze types available
def make_maze(width: int, height: int, x: int, y: int) -> Maze:
    # if either of the corners is out of bounds, don't make a maze
    if random.random() < 0.5:
        maze = PerfectMaze(width, height, x, y)
    else:
        maze = BraidMaze(width, height, x, y)

    return maze


def make_new_maze_floor(floor: Feature) -> Maze:
    # 50/50 of perfect maze or braid maze for the floor
    if random.random() < 0.5:
        maze = PerfectMaze(floor.width - 2, floor.height - 2, 1, 1)
    else:
        maze = BraidMaze(floor.width - 2, floor.height - 2, 1, 1)

    floor.tiles[1:floor.width - 1, 1:floor.height - 1] = maze.tiles
    floor.hide_tiles()

    # add_nu_piles(floor)

    return maze


def floor_segments(floor: Feature) -> (set[tuple[Tuple[int, int]]], set[tuple[Tuple[int, int]]]):
    segments = set()
    boundaries = set()

    for x in range(1, floor.width - 1):
        for y in range(1, floor.height - 1):
            if floor.tiles[x, y] == tile_types.floor and not segments_contain(segments, x, y):
                (floors, walls) = flood_fill_floor(floor, x, y)
                segments.add(floors)
                boundaries.add(walls)
    return segments, boundaries


def segments_contain(segments: set[tuple[Tuple[int, int]]], x: int, y: int) -> bool:
    for segment in segments:
        if (x, y) in segment:
            return True
    return False


# TODO there's probably a clever way to update the segments/boundaries as we go and reduce future flood fill calls
def connect_adjacent_segments(floor: Feature) -> (set[tuple[Tuple[int, int]]], set[tuple[Tuple[int, int]]]):
    # find the floor segments and their boundaries
    (segments, boundaries) = floor_segments(floor)
    boundaries = list(boundaries)

    # a nested loop to compare all segment boundaries against all others
    for i, boundary_one in enumerate(boundaries):
        for j in range(i + 1, len(boundaries)):
            boundary_two = boundaries[j]
            # if there's any overlap, add pick a random tile from the overlap to make the connection
            if set(boundary_one).intersection(set(boundary_two)):
                (x, y) = random.choice(tuple(set(boundary_one).intersection(set(boundary_two))))
                floor.tiles[x, y] = tile_types.floor


# TODO find recatngles of a certain area, also store max in case. Also width/height are swapped I think. Also find y
# return x, y of top left and width, height
def find_rectangle(floor: Feature) -> Tuple[int, int, int, int]:
    max_x, max_y, max_width, max_height, max_area = -1, -1, -1, -1, -1

    # use slices to cut off top+bottom, left+right of floor
    inner_values = floor.tiles[1:-1, 1:-1]

    # Initialize first row, 1s for walls and 0s for floors
    histogram = []
    for square in inner_values[0]:
        if square == tile_types.wall:
            histogram.append(1)
        else:
            histogram.append(0)

    for i in range(1, len(inner_values)):
        for j in range(len(inner_values[i])):
            # if it's a wall the histogram gains one height, otherwise the height it reset to 0
            if (inner_values[i][j]) == tile_types.wall:
                histogram[j] += 1
            else:
                histogram[j] = 0

        # Update result if area with current
        # row (as last row) of rectangle) is more
        (x, width, height, area) = max_histogram(histogram)
        if area > max_area:
            max_x, max_width, max_height, max_area = x, width, height, area
            max_y = (i + 1) - max_height

    # this is actually width, height, x, y
    return max_height, max_width, max_y + 1, max_x + 1


# return x, width, height
def max_histogram(heights: list[int]) -> Tuple[int, int, int, int]:
    x, max_width, max_height, max_area = -1, -1, -1, -1
    stack = []  # pair: (index, height)

    # loop through histogram
    for i, h in enumerate(heights):
        start = i
        # if you encounter a taller column than the top of the stack
        while stack and stack[-1][1] > h:
            # measure the largest histogram from the top of the stack
            index, height = stack.pop()
            width = i - index
            if height > 4 and width > 4 and (width * height) > max_area:
                max_width, max_height, x, max_area = width, h, index, width * height
            # update the left index
            start = index
        stack.append((start, h))

    # all the indices that never found a taller point get measured to see if they're the largest
    for i, h in stack:
        width = len(heights) - i
        if h > 4 and width > 4 and (width * h) > max_area:
            max_width, max_height, x, max_area = width, h, i, width * h

    return x, max_width, max_height, max_area


def make_max_maze(floor: Feature):
    make_maze(floor, *find_rectangle(floor))


# TODO nu piles can spawn on the same tile.  is this okay??
def add_entities(floor: Feature, num: int = 15):
    num_added = 0
    while num_added < num:
        floor_tiles = floor.coords_of_tile_type(tile_types.floor)
        coords = random.choice(floor_tiles)
        if random.random() < .5:
            floor.entities.append(NuPile(floor, coords[0], coords[1], random.randint(10, 20)))
        else:
            floor.entities.append(Monster(floor, coords[0], coords[1]))
        num_added += 1


def game_of_life_cycle(feature: Feature, live_tile: tile_types.tile_dt, dead_tile: tile_types.tile_dt):

    # store a copy of the floor tiles to modify without changing adjacency counts
    new_floor = feature.tiles.copy(order="F")

    # find all instances of live_tile in the feature
    live_tile_indices = np.argwhere(feature.tiles == live_tile)
    check_tiles = set()

    # add the coordinates of each live tile and all surrounding tiles to the set to check adjacency
    for tile in live_tile_indices:
        x, y = tile[0], tile[1]
        check_tiles.update([(x-1, y-1), (x, y-1), (x+1, y-1), (x-1, y), (x, y), (x+1, y), (x-1, y+1), (x, y+1), (x+1, y+1)])

    # check each tile's neighbors to see how many instances of live_tile there are
    for x, y in check_tiles:
        if feature.tiles[x, y] == live_tile:
            # if there aren't 3 or 4 in the 3x3 it dies
            if not 3 <= feature.diagonal_tile_count(x, y, tile_type=live_tile) <= 4:
                new_floor[x, y] = dead_tile
        elif feature.tiles[x, y] == dead_tile:
            # if a dead tile has 3 live neighbors it changes to a live tile
            if feature.diagonal_tile_count(x, y, tile_type=live_tile) == 3:
                new_floor[x, y] = live_tile

    feature.tiles = new_floor
