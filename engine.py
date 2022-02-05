from architect import Floor
import tcod
from message_log import MessageLog
from entity_maker import Player
from tcod.map import compute_fov
import numpy as np

#TODO add player, nu, and flickering halls

MAP_Y_OFFEST = 3
MAP_X_OFFSET = 0

class Engine:

    def __init__(self, context, console: tcod.console.Console):
        #make a new game map and default event handler
        self.log = MessageLog()
        self.console = console
        self.context = context
        self.game_map = Floor(console.width - MAP_X_OFFSET, console.height - MAP_Y_OFFEST)
        self.player = Player(self.game_map)
        self.game_map.entities.append(self.player)

    def update_fov(self) -> None:
        self.game_map.visible[:] = compute_fov(
            self.transparent_tiles(),
            (self.player.x, self.player.y),
            radius=8,
            light_walls=True,
            algorithm=tcod.FOV_DIAMOND
        )

        self.game_map.explored |= self.game_map.visible

    def transparent_tiles(self) -> np.ndarray:
        transparent = np.ones((self.game_map.width, self.game_map.height), order="F") \
            if self.player.flags["see_through_walls"] else self.game_map.tiles["transparent"]

        if self.player.flags["one_eyed"]:
            new_transparent = np.zeros((self.game_map.width, self.game_map.height), order="F")
            new_transparent[:, self.player.y] = transparent[:, self.player.y]
            new_transparent[self.player.x, :] = transparent[self.player.x, :]
            transparent = new_transparent

        return transparent