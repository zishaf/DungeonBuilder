import random
from typing import Tuple

import tile
from dungeon_features import Floor, PerfectMaze, PyramidMaze

def smooth_it_out(floor: Floor, smoothness: int = 4):
    #converts each cell to its most common neighbor, a higher smoothness means fewer walls
    new_floor = floor.tiles.copy(order = "F")

    for x in range(1, floor.width - 1):
        for y in range(1, floor.height - 1):
            new_floor[x, y] = tile.wall if floor.diagonal_walls(x, y) >= smoothness else tile.floor

    floor.tiles = new_floor

def fill_caverns(floor: Floor, radius: int = 2):
    # make wall tiles anywhere there are no other wall tiles within the given radius
    new_floor = floor.tiles.copy(order = "F")
    
    for x in range(1, floor.width - 1):
        for y in range(1, floor.height - 1):
            if new_floor[x, y] == tile.floor and floor.diagonal_walls(x, y, r = radius) == 0 : new_floor[x, y] = tile.wall

    floor.tiles = new_floor

def reset_map(floor: Floor, denseness: float = 0.5):
    #randomly assigns every non-edge tile as wall or floor
    for x in range (1, floor.width-1):
        for y in range (1, floor.height-1):
            floor.tiles[x, y] = tile.wall if random.random() < denseness else tile.floor

# TODO rework random_corridor/tunnel function with stack, currently hangs on hard-to-find tunnels
def random_corridor(floor: Floor, length: int, blobulousness: int = 0) -> bool:
    #make a shuffled list of all possible starting points and tries to make corridors
    starts = list(floor.valid_starts())
    random.shuffle(starts)

    #try to tunnel a corridor with length-1 since x,y will be the first tile.
    while starts:
        x,y = starts.pop()
        if tunnel(floor, length - 1, x, y, blobulousness):
            return True
    return False

def tunnel(floor: Floor, length: int, x: int, y: int, blobulousness: int = 0) -> bool:
    #mark our tile
    floor.tiles[x, y] = tile.floor

    #return true if we've reached target length
    if length == 0: return True

    #this line makes it so a corridor will loop on to itself for the last possible tile, and be slightly less strict.
    b = blobulousness + 1 if length == 1 else blobulousness

    #add all neighbors to destinations, shuffle the list to build in random direction
    dests = [(x-1,y), (x+1,y), (x,y-1), (x,y+1)]
    random.shuffle(dests)

    #check all destinations and return true if they reach their conclusion, else reset the tile
    for destx, desty in dests:
        if floor.can_corridor(destx, desty, b):
            if tunnel(floor, length - 1, destx, desty, b):
                return True
            else:
                floor.tiles[destx, desty] = tile.wall

    #reset the starting tile if all fails and return false
    floor.tiles[x, y] = tile.wall

    return False

def flood_fill(floor:Floor, x: int, y: int, tile_type = None) -> list[Tuple[int, int]]:
    #flood fill will default to look for its starting tile if no value is given
    if tile_type is None: tile_type = floor.tiles[x, y]

    #will call flood_fill on a tiles in the stack and add them to filled
    stack: list(Tuple[int, int]) = [(x, y)]
    filled: list(Tuple[int, int]) = []

    #check all elements to see if they are in bounds, unmarked, and the right type
    while stack:
        x, y = stack.pop()
        if floor.in_bounds(x, y) and floor.tiles[x, y] == tile_type and (x, y) not in filled:
            #if it passes, mark it and add all its neighbors to the stack for checking
            filled.append((x, y))
            stack.extend([(x-1, y), (x+1, y), (x, y-1), (x,y+1)])

    return filled

def corridor_between(
        floor: Floor, startx: int, starty: int, endx: int, endy: int
):
    floor.tiles[startx, starty] = tile.floor

    if startx == endx and starty == endy:
        return

    choices = list()
    left, right, up, down = (startx - 1, starty), (startx + 1, starty), (startx, starty - 1), (startx, starty + 1)

    if starty == endy and abs(startx-endx) > 2:
        choices.append(up)
        choices.append(down)

    if startx == endx and abs(starty-endy) > 2:
        choices.append(left)
        choices.append(right)

    if endx < startx: choices.append(left)
    if endx > startx: choices.append(right)
    if endy < starty: choices.append(up)
    if endy > starty: choices.append(down)
    dest = random.choice(choices)

    if dest is up: starty -= 1
    if dest is right: startx += 1
    if dest is down: starty += 1
    if dest is left: startx -= 1

    corridor_between(floor, startx, starty, endx, endy)

#TODO make different maze types available
def make_maze(floor: Floor, width: int, height: int, x: int, y: int):

    #if either of the corners is out of bounds, don't make a maze
    if not(floor.in_bounds(x,y) and floor.in_bounds(x+width-1, y+height-1)):
        return

    maze = PerfectMaze(width, height)
    floor.tiles[x:x + width, y:y + height] = maze.tiles
