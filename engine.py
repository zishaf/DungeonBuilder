import random

import entity_maker
import tile_types
import architect
from architect import Floor, Feature
import tcod
import test_functions
from message_log import MessageLog
from entity_maker import Entity, Player
from tcod.map import compute_fov
import numpy as np
import colors
import time

# TODO add player, nu, and flickering halls

GAME_MAP_WIDTH, GAME_MAP_HEIGHT = 136, 92
BAD_PAIRS = [{'top_left', 'bot_right'}, {'top_right', 'bot_left'}]


class Engine:
    def __init__(self, context, console: tcod.console.Console):
        # make a new game map and default event handler
        self.log = MessageLog()
        self.console = console
        self.context = context
        self.game_map = Floor(GAME_MAP_WIDTH, GAME_MAP_HEIGHT)
        self.player = Player(self)
        self.entities: list[Entity] = [self.player]
        self.depth = 1

    def update_fov(self) -> None:
        self.game_map.visible[:] = compute_fov(
            self.transparent_tiles(),
            (self.player.x, self.player.y),
            radius=11,
            light_walls=True,
            algorithm=tcod.FOV_DIAMOND
        )

        self.game_map.explored |= self.game_map.visible

    def viewshed(self, monster: entity_maker.Monster) -> list:
        # floor = np.zeros((self.game_map.width, self.game_map.height), order="F", dtype=bool)
        viewshed = compute_fov(
            self.transparent_tiles(),
            (monster.x, monster.y),
            radius=10,
            light_walls=True,
            algorithm=tcod.FOV_DIAMOND
        )
        coords = np.argwhere(viewshed == 1).tolist()
        return coords

    def make_new_game_map(self) -> None:
        self.game_map = self.make_floor(self.game_map.width, self.game_map.height)
        self.place_player()
        self.add_entities()

        # check if the player has the ability to see stairs and reveal the staircase if so
        if 'see_stairs' in self.player.flags:
            # check if the player has the ability to see stairs and reveal the staircase if so
            for xy in self.game_map.coords_of_tile_type(tile_types.down_stairs):
                self.game_map.explored[xy[0], xy[1]] = True

        self.log.add_message("Welcome to the Crystal Caves", colors.CRYSTAL)

    def transparent_tiles(self) -> np.ndarray:
        transparent = np.ones((self.game_map.width, self.game_map.height), order="F") \
            if 'see_through_walls' in self.player.flags else self.game_map.tiles["transparent"]

        if 'one_eyed' in self.player.flags:
            new_transparent = np.zeros((self.game_map.width, self.game_map.height), order="F")
            new_transparent[:, self.player.y] = transparent[:, self.player.y]
            new_transparent[self.player.x, :] = transparent[self.player.x, :]
            transparent = new_transparent

        return transparent

    def player_dead(self) -> bool:
        return self.player.nu <= 0

    # TODO check for collision
    def teleport_entity(self, entity: Entity):
        new_xy = random.choice(self.game_map.coords_of_tile_type(tile_types.floor))
        entity.x, entity.y = new_xy[0], new_xy[1]

    def move_entity(self, dest_x, dest_y, entity: Entity) -> bool:
        # can only move to walkable tiles
        if self.game_map.tiles[dest_x, dest_y]["walkable"]:
            # check if entity has teleportitis: 1/100 of teleporting them.  nu-free!!
            if 'teleportitis' in entity.flags and random.random() <= .01:
                self.teleport_entity(entity)

            # otherwise move entity and take nu if player
            else:
                blocked = False
                for e in self.entities:
                    if dest_x == e.x and dest_y == e.y and e.blocks_movement:
                        blocked = True
                        if entity is self.player:
                            self.player.nu -= 1
                        e.on_collide(entity)

                if not blocked:
                    # add walls if the entity has that "power"
                    if 'leave_walls' in entity.flags:
                        self.game_map.tiles[entity.x, entity.y] = tile_types.wall

                    entity.x, entity.y = dest_x, dest_y

                    if entity is self.player:
                        self.player.nu -= 1

                    return True

        # return false if the entity didn't move to destination (teleport too)
        return False

    def end_player_turn(self):
        # check for collision with other entities
        for entity in self.entities:
            if (self.player.x, self.player.y) == (entity.x, entity.y):
                if entity is not self.player:
                    entity.on_collide(self.player)

    def place_player(self) -> bool:
        floor_tiles = list(self.game_map.coords_of_tile_type(tile_types.floor))
        down_stairs = self.game_map.coords_of_tile_type(tile_types.down_stairs)

        while floor_tiles:
            # pick a random starting tile
            xy = random.choice(floor_tiles)
            self.player.x, self.player.y = xy[0], xy[1]
            good_location = True

            # see if any stair case is closer than 20 steps to the starting tile
            for stair_xy in down_stairs:
                if len(self.player.path_to(stair_xy[0], stair_xy[1])) < 20:
                    good_location = False

            # if no stair is close, return and leave the player on that tile
            if good_location:
                return True

            floor_tiles.remove(xy)

        return False

    def reveal_stairs(self) -> None:
        for xy in self.game_map.coords_of_tile_type(tile_types.down_stairs):
            self.game_map.explored[xy[0], xy[1]] = True

    def entities_of_type(self, t) -> list:
        return [monster for monster in self.entities if type(monster) == t]

    # TODO nu piles can spawn on the same tile.  is this okay??
    def add_entities(self):
        # add nu piles to every feature, more to maze features.  then move entities from features to parent floor
        for feature_name in self.game_map.features:
            feature = self.game_map.features[feature_name]

            i = 40 if type(feature) == architect.Maze else 15
            num_added = 0

            while num_added < i:
                floor_tiles = feature.coords_of_tile_type(tile_types.floor)
                coords = random.choice(floor_tiles)
                if random.random() < .5:
                    self.entities.append(entity_maker.NuPile(self, feature.x + coords[0], feature.y + coords[1],
                                                             random.randint(15, 30)))
                else:
                    self.entities.append(entity_maker.Monster(self, feature.x + coords[0], feature.y + coords[1]))
                num_added += 1

    def make_floor(self, width: int, height: int) -> Floor:

        floor = Floor(width, height)

        x_divider = random.randint(20, width - 20)
        y_divider = random.randint(20, height - 20)

        floor.features['top_left'] = Feature(x_divider + 1, y_divider + 1, 0, 0)
        floor.features['top_right'] = Feature(width - x_divider, y_divider + 1, x_divider, 0)
        floor.features['bot_left'] = Feature(x_divider + 1, height - y_divider, 0, y_divider)
        floor.features['bot_right'] = Feature(width - x_divider, height - y_divider, x_divider, y_divider)

        # TODO make this, along with everything else, a probability table based on depth
        # 'winding'
        feature_types = ['maze', 'cavern', 'egg']

        maze_feature: str = ''
        non_mazes = []

        # feature is the name of the feature: i.e. 'top_left'.  cur_feature is the value held at that key
        for feature in floor.features:
            feature_type = random.choice(feature_types)
            cur_feature = floor.features[feature]
            tick = time.perf_counter()

            # dictionaries only give a view of their values or smthng
            if feature_type == 'maze':
                floor.features[feature] = architect.make_maze(cur_feature.width, cur_feature.height, cur_feature.x,
                                                              cur_feature.y)
                maze_feature = feature
                self.make_maze_exit(maze=floor.features[feature], location=feature)
                feature_types.remove('maze')

            else:
                non_mazes.append(feature)

                if feature_type == 'winding':
                    test_functions.make_winding_map(cur_feature)
                elif feature_type == 'cavern':
                    test_functions.make_cavern_map(cur_feature, .5, 5, 6)
                elif feature_type == 'egg':
                    test_functions.make_egg_map(cur_feature)
                    stair_coords = random.choice(np.argwhere(cur_feature.tiles == tile_types.floor))
                    cur_feature.tiles[stair_coords[0], stair_coords[1]] = tile_types.down_stairs

            tock = time.perf_counter()
            print(f"{feature_type} of size {cur_feature.width}x{cur_feature.height} took {tock - tick:4f} seconds.")

        # set the floor tiles from its newly built features
        for feature in floor.features.values():
            floor.tiles[feature.x:feature.x + feature.width, feature.y:feature.y + feature.height] = feature.tiles

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
            floor.tiles[stair_coords[0] + floor.features[choice].x, stair_coords[1] + floor.features[
                choice].y] = tile_types.down_stairs

        return floor

    def make_maze_exit(self, maze: architect.Maze, location: str):
        x1, y1, x2, y2 = maze.ent_x, maze.ent_y, maze.ext_x, maze.ext_y

        # based on location see if we need to swap entrance and exit
        if location == 'top_left':
            if x1 == 0 or y1 == 0:
                maze.ent_x, maze.ent_y, maze.ext_x, maze.ext_y = x2, y2, x1, y1
        elif location == 'top_right':
            if x1 == maze.width - 1 or y1 == 0:
                maze.ent_x, maze.ent_y, maze.ext_x, maze.ext_y = x2, y2, x1, y1
        elif location == 'bot_left':
            if x1 == 0 or y1 == maze.height - 1:
                maze.ent_x, maze.ent_y, maze.ext_x, maze.ext_y = x2, y2, x1, y1
        elif location == 'bot_right':
            if x1 == maze.width - 1 or y1 == maze.height - 1:
                maze.ent_x, maze.ent_y, maze.ext_x, maze.ext_y = x2, y2, x1, y1

        # exit is a down stairs with a big nu pile next to it
        maze.tiles[maze.ext_x, maze.ext_y] = tile_types.down_stairs
        for x, y in architect.neighbor_coords(maze.ext_x, maze.ext_y):
            if maze.in_bounds(x, y) and maze.tiles[x, y] == tile_types.floor:
                self.entities.append(entity_maker.NuPile(self, maze.x + x, maze.y + y, 100))
