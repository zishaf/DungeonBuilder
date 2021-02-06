import random

import numpy as np
import tcod.console
import tile


class Floor():
    def __init__(self, width: int, height: int):
        self.tiles = np.full((width, height), fill_value=tile.wall, order="F")
        self.width, self.height = width, height

    def in_bounds(self, x, y) -> bool:
        return 0 < x < self.width-1 and 0 < y < self.height-1

    def cells_centered_on(self, x: int, y: int, r: int = 1) -> np.ndarray:
        # gets slice of floor tiles based on radius. uses min, max to avoid out of bounds tiles in one fancy line
        return self.tiles[max(x - r, 0): min(x + r + 1, self.width), max(y - r, 0): min(y + r + 1, self.height)]

    def diagonal_walls(self, x: int, y: int, r: int = 1) -> int:
        # counts walls in given radius of cells centered on x, y.  this is my favorite line of code
        return np.count_nonzero(self.cells_centered_on(x, y, r).flatten() == tile.wall)

    def adjacent_tiles(self, x, y) -> np.ndarray:
        #a list of the tiles above, below, left, and right of x and y
        return [self.tiles[x - 1, y], self.tiles[x + 1, y], self.tiles[x, y - 1], self.tiles[x, y + 1]]

    def cardinal_walls(self, x: int, y: int) -> int:
        return self.adjacent_tiles(x, y).count(tile.wall)

    def can_corridor(self, x: int, y: int, blobulousness: int = 0) -> bool:
        #can dig corridor if the tile is in bounds, is a wall, and has enough (>blobulousness) adjacent walls
        #awkward calculation with blobulation because I like the var name and think it should start from 0
        return self.in_bounds(x, y) and self.tiles[x, y] == tile.wall and self.cardinal_walls(x, y) > 2 - blobulousness

    # TODO refactor the choices list to avoid looping through at start
    def valid_starts(self):
        #yield statement should make a generator object, probably doesn't actually do anything with recast to list
        #valid starts are attached to existing dungeon features
        for x in range(1, self.width - 1):
            for y in range(1, self.height - 1):
                if self.cardinal_walls(x, y) == 3 and self.tiles[x, y] != tile.floor:
                    yield (x, y)

    def render(self, console: tcod.console.Console):
        console.tiles_rgb[0:self.width, 0:self.height] = self.tiles["graphic"]

class PyramidMaze:
    def __init__(self, width: int, height: int):
        self.width, self.height = width, height
        self.tiles = np.full((width, height), fill_value=tile.wall, order="F")
        self.carve()

    #TODO pretty up this incomprehensible mess
    def carve(self):
        #sets a ring of floor tiles every two tiles
        for i in range(1, min(int(self.width/2),int(self.height/2)),2):
            self.tiles[i:self.width - i, i] = tile.floor                    # top
            self.tiles[i:self.width - i, self.height - i - 1] = tile.floor  # bottom
            self.tiles[i, i:self.height - i] = tile.floor                   # left
            self.tiles[self.width - i - 1, i:self.height - i] = tile.floor  # right
            self.make_passage(i)

    def make_passage(self, i: int):
        #carves one random tile between two rings, equal chance for each tile, won't choose a corner
        walls = {
            "top"   : self.tiles[i + 2:self.width - i - 2, i + 1],
            "bottom": self.tiles[i + 2:self.width - i - 2, self.height - i - 2],
            "left"  : self.tiles[i + 1, i + 2:self.height - i - 2],
            "right" : self.tiles[self.width - i - 2, i + 2:self.height - i - 2]
        }

        #don't carve if any list has length 0, that means center has been reached
        if all(len(lst) > 0 for lst in walls.values()):

            #chicanery with lists' total length and slices so I can use view of array instead of copy
            choice = random.randrange(0, sum(len(lst) for lst in walls.values()))

            for wall in walls.values():
                if choice < len(wall):
                    wall[choice] = tile.floor
                    return
                else:
                    choice -= (len(wall))

        """ TEST CHOICES HIGHLIGHTER
        self.tiles[i + 2:self.width - i - 2, i + 1] = tile.new_tile(walkable=True, transparent=True, graphic=(ord("!"), (255, 255, 255), (0, 0, 0)))
        self.tiles[i + 2:self.width - i - 2, self.height - i - 2] = tile.new_tile(walkable=True, transparent=True, graphic=(ord("!"), (255, 255, 255), (0, 0, 0)))
        self.tiles[i + 1, i + 2:self.height - i - 2] = tile.new_tile(walkable=True, transparent=True, graphic=(ord("!"), (255, 255, 255), (0, 0, 0)))
        self.tiles[self.width - i - 2, i + 2:self.height - i - 2] = tile.new_tile(walkable=True, transparent=True, graphic=(ord("!"), (255, 255, 255), (0, 0, 0)))
        """

    #doesn't work
    def make_entrance(self):
        self.make_passage(-1)