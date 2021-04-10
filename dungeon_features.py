import random

import numpy as np
import tcod.console
import tcod.path
import random
import tile

class Feature():
    pass

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
        #can dig corridor if the tile is in bounds, is a wall, and has enough adjacent walls
        #awkward calculation with blobulation because I like the var name and think it should start from 0
        return self.in_bounds(x, y) and self.tiles[x, y] == tile.wall and self.cardinal_walls(x, y) > 2 - blobulousness

    # TODO refactor the choices list to avoid looping through at start, i.e. tunnel intelligently
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

    def carve(self):
        #sets a ring of floor tiles every two tiles, stops at half of width or height
        for i in range(1, min(int(self.width/2),int(self.height/2)),2):
            #make the 4 walls that form a ring
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

class PerfectMaze:
    def __init__(self, width: int, height: int):
        self.width, self.height = width, height
        self.tiles = np.full((width, height), fill_value=tile.floor, order="F")
        self.fill_border()
        self.add_walls()
        self.add_entrances()
        self.clean_2x2()

    def fill_border(self):
        #use a step of width/height - 1 to get two values in one pass. Save two lines! Minus one for the comment
        self.tiles[0:self.width,0:self.height:self.height-1] = tile.wall
        self.tiles[0:self.width:self.width-1,0:self.height] = tile.wall

    def add_walls(self):
        choices = []

        #initial choices will be the outermost ring, excluding corners. add x, y and direction 1,2,3,4 as up,down,left,right
        for x in range(1, self.width - 1):
            choices.extend([(x,1,3),(x,self.height-2,1)])
        for y in range(1, self.height - 1):
            choices.extend([(1,y,2),(self.width-2,y,4)])

        while choices:
            x, y, dir = random.choice(choices)
            choices.remove((x, y, dir))
            if self.adjacent_tiles(x, y).count(tile.wall) == 1 and self.tiles[x, y] == tile.floor and self.check_diagonals(x, y, dir):
                self.tiles[x, y] = tile.wall
                choices.extend([(x+1, y, 2),(x-1, y, 4),(x,y+1, 3),(x,y-1, 1)])

    def add_entrances(self):
        wall_one_choices = []
        wall_two_choices = []
        if random.random() < 0.5:
            for y in range(1, self.height-1):
                if self.tiles[1, y] == tile.floor:
                    wall_one_choices.append((0, y))
                if self.tiles[self.width-2,y] == tile.floor:
                    wall_two_choices.append((self.width-1, y))
        else:
            for x in range(1, self.width-1):
                if self.tiles[x, 1] == tile.floor:
                    wall_one_choices.append((x, 0))
                if self.tiles[x, self.height-2] == tile.floor:
                    wall_two_choices.append((x, self.height-1))

        ent_x, ent_y = random.choice(wall_one_choices)
        ext_x, ext_y = random.choice(wall_two_choices)

        self.tiles[ent_x, ent_y] = tile.floor
        self.tiles[ext_x, ext_y] = tile.floor

    def check_diagonals(self, x, y, dir) -> bool:
        if dir == 1:
            return self.tiles[x-1, y-1] == tile.floor and self.tiles[x+1, y-1] == tile.floor
        elif dir == 3:
            return self.tiles[x-1, y+1] == tile.floor and self.tiles[x+1, y+1] == tile.floor
        elif dir == 2:
            return self.tiles[x+1, y+1] == tile.floor and self.tiles[x+1, y-1] == tile.floor
        elif dir == 4:
            return self.tiles[x-1, y+1] == tile.floor and self.tiles[x-1, y-1] == tile.floor

    def adjacent_tiles(self, x, y) -> np.ndarray:
        # a list of the tiles above, below, left, and right of x and y
        if self.in_bounds(x, y):
            return [self.tiles[x - 1, y], self.tiles[x + 1, y], self.tiles[x, y - 1], self.tiles[x, y + 1]]
        else: return []

    def in_bounds(self, x, y) -> bool:
        return 0 < x < self.width-1 and 0 < y < self.height-1

    def clean_2x2(self):
        for x in range(1, self.width-1):
            for y in range(1, self.height-1):
                if (all(i == tile.floor for i in self.tiles[x:x+2,y:y+2].flatten())):
                    self.fill_corner(x, y)

    def fill_corner(self, x: int, y: int):
        corners = []
        if self.tiles[x-1, y] == tile.wall and self.tiles[x, y-1] == tile.wall:
            corners.append((x, y))
        if self.tiles[x-1, y+1] == tile.wall and self.tiles[x, y+2] == tile.wall:
            corners.append((x, y+1))
        if self.tiles[x+1, y-1] == tile.wall and self.tiles[x+2, y] == tile.wall:
            corners.append((x+1, y))
        if self.tiles[x+2, y+1] == tile.wall and self.tiles[x+1, y+2] == tile.wall:
            corners.append((x+1, y+1))
        if corners:
            x, y = random.choice(corners)
            self.tiles[x, y] = tile.wall