import random
from typing import Tuple

import tile
from dungeon_features import Floor, PerfectMaze, PyramidMaze

def smooth_it_out(floor: Floor, smoothness: int = 5):
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
    #make a list of all possible starting points and shuffle it
    starts = list(floor.valid_starts())
    random.shuffle(starts)

    # Shit takes too long.  faster to find easy corridors without all the overhead.  might help on long ones though
    """candidates = []
    #selective flood fill will cull the starts with trying_corridor down to spacious candidates
    for x, y in starts:
        if len(flood_fill(floor, x, y, trying_corridor=starts)) > 3 * length:
            candidates.append((x, y))"""

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

#TODO make it a scan line fill so it's faster!
def flood_fill_floor(floor:Floor, x: int, y: int,) -> (tuple[Tuple[int, int]], tuple[Tuple[int, int]]):
    #flood fill will default to look for its starting tile if no value is given
    #if tile_type is None: tile_type = floor.tiles[x, y]

    #will call flood_fill on a tiles in the stack and add them to filled
    stack: list(Tuple[int, int]) = [(x, y)]
    filled: set(Tuple[int, int]) = set()
    boundaries: set(Tuple[int, int]) = set()

    #check coords to see if they are unmarked floors, if it's a wall it's a boundry and stored seperately
    while stack:
        x, y = stack.pop()
        if floor.tiles[x, y] == tile.wall:
            boundaries.add((x, y))

        elif (x, y) not in filled:
            filled.add((x, y))
            stack.extend([(x-1, y), (x+1, y), (x, y-1), (x,y+1)])

    return (tuple(filled), tuple(boundaries))

#TODO out of bounds check needed
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

#returns the coordinates (in order) above, right, below, and left of the given coordinates
def cardinal_coords(x, y) -> list[Tuple[int, int]]:
    return [(x, y+1), (x+1, y), (x, y-1), (x-1, y)]

#TODO make different maze types available
def make_maze(floor: Floor, width: int, height: int, x: int, y: int):

    #if either of the corners is out of bounds, don't make a maze
    if not(floor.in_bounds(x,y) and floor.in_bounds(x+width-1, y+height-1)):
        return

    maze = PerfectMaze(width, height)
    floor.tiles[x:x + width, y:y + height] = maze.tiles

def floor_segments(floor: Floor) -> (set[tuple[Tuple[int, int]]], set[tuple[Tuple[int, int]]]):
    segments = set()
    boundaries = set()

    for x in range (1, floor.width-1):
        for y in range (1, floor.height-1):
            if floor.tiles[x, y] == tile.floor and not segments_contain(segments, x, y):
                (floors, walls) = flood_fill_floor(floor, x, y)
                segments.add(floors)
                boundaries.add(walls)
    return (segments, boundaries)

def segments_contain(segments: set[tuple[Tuple[int, int]]], x: int, y: int) -> bool:
    for segment in segments:
        if (x, y) in segment:
            return True
    return False

#TODO there's probably a clever way to update the segments/boundaries as we go and reduce future flood fill calls
#TODO also it's double checking segments against themselves.  probably need to enumerate the nested loop
def connect_adjacent_segments(floor: Floor) -> (set[tuple[Tuple[int, int]]], set[tuple[Tuple[int, int]]]):
    #find the floor segments and their boundaries
    (segments, boundaries) = floor_segments(floor)

    #a nested loop to compare all segment boundaries against all others
    for boundary_one in boundaries:
        for boundary_two in boundaries:
            if boundary_one == boundary_two:
                #back to start if we're comparing someting to itself
                continue
            #if there's any overlap, add pick a random tile from the overlap to make the connection
            if set(boundary_one).intersection(set(boundary_two)):
                (x, y) = random.choice(tuple(set(boundary_one).intersection(set(boundary_two))))
                floor.tiles[x, y] = tile.floor

#TODO find recatngles of a certain area, also store max in case. Also width/height are swapped I think. Also find y
#return x, y of top left and width, height
def find_rectangle(floor: Floor) -> Tuple[int, int, int, int]:
    max_x, max_y, max_width, max_height, max_area = -1, -1, -1, -1, -1

    #use slices to cut off top+bottom, left+right of floor
    inner_values = floor.tiles[1:-1, 1:-1]

    # Initialize first row, 1s for walls and 0s for floors
    histogram = []
    for square in inner_values[0]:
        if square == tile.wall:
            histogram.append(1)
        else:
            histogram.append(0)

    for i in range(1, len(inner_values)):
        for j in range(len(inner_values[i])):
            # if it's a wall the histogram gains one height, otherwise the height it reset to 0
            if (inner_values[i][j]) == tile.wall:
                histogram[j] += 1
            else:
                histogram[j] = 0

        # Update result if area with current
        # row (as last row) of rectangle) is more
        (x, width, height, area) = max_histogram(histogram)
        if area > max_area:
            max_x, max_width, max_height, max_area = x, width, height, area
            max_y = (i + 1) - max_height

    #this is actually width, height, x, y
    return (max_height, max_width, max_y+1, max_x+1)

#return x, width, height
def max_histogram(heights: list[int]) -> Tuple[int, int, int, int]:
    x, max_width, max_height, max_area = -1, -1, -1, -1
    stack = [] # pair: (index, height)

    #loop through histogram
    for i, h in enumerate(heights):
        start = i
        #if you encounter a taller column than the top of the stack
        while stack and stack[-1][1] > h:
            #measure the largest histogram from the top of the stack
            index, height = stack.pop()
            width = i - index
            if height > 4 and width > 4 and (width * height) > max_area:
                max_width, max_height, x, max_area = width, h, index, width*height
            #update the left index
            start = index
        stack.append((start, h))

    #all the indices that never found a taller point get measured to see if they're the largest
    for i, h in stack:
        width = len(heights) - i
        if h > 4 and width > 4 and (width * h) > max_area:
            max_width, max_height, x, max_area = width, h, i, width*h

    return (x, max_width, max_height, max_area)

def make_max_maze(floor: Floor):
    make_maze(floor, *find_rectangle(floor))

#The function only works if it's lucky, otherwise it hangs, consider helping it find its destination instead of pure
#random walking
"""
def random_walk_between(floor: Floor, x1 : int, y1 : int, x2 : int, y2 :int) -> bool:
    #random walk can't start on a floor tile or be length 1
    if floor.tiles[x1, y1] == tile.floor or (x1 == x2 and y1 == y2):
        return False

    #the walked tiles list contains each visited coordinate, we have a list of lists to track directions we can try from
    #each walked tile
    walked_tiles: list(Tuple[int, int]) = [(x1, y1)]
    untried_directions: list(list(int)) = [[0, 1, 2, 3]]

    #mark the first tile as a floor
    floor.tiles[x1, y1] = tile.floor

    while walked_tiles:
        #if there are no more available directions for this tile, remove it from our walk and reset it to wall
        if len(untried_directions[-1]) == 0:
            undo_x, undo_y = walked_tiles.pop()
            floor.tiles[undo_x, undo_y] = tile.wall
            untried_directions.pop()
            continue

        #find our current coordinates and their neighbors (possible_dests)
        cur_x, cur_y = walked_tiles[-1]
        possible_dests = cardinal_coords(cur_x, cur_y)

        #randomly choose a direction, find corresponding destination, then adjust possible directions for future
        chosen_direction = random.choice(untried_directions[-1])
        untried_directions[-1].remove(chosen_direction)
        dest_x, dest_y = possible_dests[chosen_direction]

        #if we've reached the final destination, mark it as a floor and break
        if dest_x == x2 and dest_y == y2:
            floor.tiles[dest_x, dest_y] = tile.floor
            break

        #otherwise, if the tile is in bounds, a wall, and surrounded by walls, walk there
        if floor.can_corridor(dest_x, dest_y):
            #mark it a floor, add it to the list of walked tiles, and all 4 directions as possibilities
            floor.tiles[dest_x, dest_y] = tile.floor
            walked_tiles.append((dest_x, dest_y))
            untried_directions.append([0,1,2,3])

    return True if walked_tiles else False
"""