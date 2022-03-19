import random

import entity_maker
import tile_types
from architect import Floor
import tcod
import test_functions
from message_log import MessageLog
from entity_maker import Player
from tcod.map import compute_fov
import numpy as np
import colors

# TODO add player, nu, and flickering halls

GAME_MAP_WIDTH, GAME_MAP_HEIGHT = 136, 92


class Engine:
    def __init__(self, context, console: tcod.console.Console):
        # make a new game map and default event handler
        self.log = MessageLog()
        self.console = console
        self.context = context
        self.game_map = Floor(GAME_MAP_WIDTH, GAME_MAP_HEIGHT)
        self.player = Player(self.game_map)
        self.game_map.entities.append(self.player)
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

    def make_new_game_map(self) -> None:
        self.game_map = test_functions.make_floor(self.game_map.width, self.game_map.height, player=self.player)
        self.place_player()

        # check if the player has the ability to see stairs and reveal the staircase if so
        if self.player.flags["see_stairs"]:
            # check if the player has the ability to see stairs and reveal the staircase if so
            for xy in self.game_map.coords_of_tile_type(tile_types.down_stairs):
                self.game_map.explored[xy[0], xy[1]] = True

        self.log.add_message("Welcome to the Crystal Caves", colors.CRYSTAL)

    def transparent_tiles(self) -> np.ndarray:
        transparent = np.ones((self.game_map.width, self.game_map.height), order="F") \
            if self.player.flags["see_through_walls"] else self.game_map.tiles["transparent"]

        if self.player.flags["one_eyed"]:
            new_transparent = np.zeros((self.game_map.width, self.game_map.height), order="F")
            new_transparent[:, self.player.y] = transparent[:, self.player.y]
            new_transparent[self.player.x, :] = transparent[self.player.x, :]
            transparent = new_transparent

        return transparent

    def player_dead(self) -> bool:
        return self.player.nu <= 0

    def teleport_player(self) -> bool:
        new_xy = random.choice(self.game_map.coords_of_tile_type(tile_types.floor))
        self.player.x, self.player.y = new_xy[0], new_xy[1]
        self.player.nu -= 1
        return True

    def move_player(self, dest_x, dest_y) -> bool:
        # can only move to floors
        if self.game_map.tiles[dest_x, dest_y]["walkable"]:
            if self.player.flags["teleportitis"] and random.random() < .01:
                self.teleport_player()
            for entity in self.game_map.entities:
                if (dest_x, dest_y) == (entity.x, entity.y):
                    if isinstance(entity, entity_maker.NuPile):
                        self.player.nu += entity.amt
                        self.game_map.entities.remove(entity)
                    if entity.blocks_movement:
                        self.player.nu -= 1
                        return False
            self.player.x, self.player.y = dest_x, dest_y
            self.player.nu -= 1
            return True
        return False

    def place_player(self) -> bool:
        floor_tiles: list = self.game_map.coords_of_tile_type(tile_types.floor).tolist()
        down_stairs = self.game_map.coords_of_tile_type(tile_types.down_stairs)

        while floor_tiles:
            xy = random.choice(floor_tiles)
            self.player.x, self.player.y = xy[0], xy[1]
            good_location = True

            for stair_xy in down_stairs:
                if len(self.player.path_to(stair_xy[0], stair_xy[1])) < 20:
                    good_location = False

            if good_location:
                return True

            floor_tiles.remove(xy)

        return False
