from __future__ import annotations

import numpy as np
import tile_types
import colors
from tcod import path
from typing import Tuple, TYPE_CHECKING
import monster_ai
import random

if TYPE_CHECKING:
    from engine import Engine


class Entity:
    def __init__(self, parent: Engine, x: int = None, y: int = None, graphic: tile_types.graphic_dt = None):
        self.parent = parent
        self.x, self.y = x, y
        self.graphic = graphic
        self.blocks_movement = False
        self.nu = None
        self.flags = []

    def on_collide(self, collider: Entity):
        pass


class Actor(Entity):
    def __init__(self, parent: Engine, graphic: tile_types.graphic_dt, x: int = None, y: int = None, nu: int = 300):
        super().__init__(parent, x, y, graphic)
        self.nu = nu
        self.blocks_movement = True

    # TODO will bump enemies and then teleport to the next step
    # noinspection PyTypeChecker
    def path_to(self, dest_x, dest_y) -> list[Tuple[int, int]]:
        cost = np.array(self.parent.game_map.tiles["walkable"], dtype=np.int8)

        graph = path.SimpleGraph(cost=cost, cardinal=1, diagonal=0)
        pathfinder = path.Pathfinder(graph)

        pathfinder.add_root((self.x, self.y))  # starting position

        # compute path and remove starting point
        steps: list[list[int]] = pathfinder.path_to((dest_x, dest_y))[1:].tolist()

        # convert from List of lists to list of Tuples
        return [(index[0], index[1]) for index in steps]

    def on_collide(self, collider: Entity):
        raise NotImplementedError

    def die(self):
        raise NotImplementedError


# TODO implement on_collide, die
class Player(Actor):
    def __init__(self, parent: Engine, x: int = None, y: int = None, nu: int = 300):
        super().__init__(parent, (64, colors.ORANGE, colors.DARK_GREY), x, y, nu)

    def on_collide(self, collider: Entity):
        self.nu -= 5


class Monster(Actor):
    def __init__(self, parent: Engine, x: int, y: int):
        super().__init__(parent, (2, colors.LIGHT_GREEN, colors.DARK_GREY), x, y, 10)
        self.target_tiles = []
        self.viewshed = self.parent.calculate_viewshed(self)

    def on_collide(self, collider: Entity):
        if type(collider) == Player:
            self.nu -= 10
            if self.nu <= 0:
                self.die()

    def die(self):
        self.parent.entities.remove(self)
        self.parent.entities.append(NuPile(self.parent, self.x, self.y, 5))

    def take_turn(self) -> None:
        if self.target_tiles:
            monster_ai.move_to_target(self)
        elif [self.parent.player.x, self.parent.player.y] in self.viewshed:
            if random.random() < 0.5:
                monster_ai.rook_target(self)
            else:
                monster_ai.bishop_target(self)

class NuPile(Entity):
    def __init__(self, parent: Engine, x: int, y: int, amt: int):
        super().__init__(parent, x, y, (15, colors.GOLD, colors.DARK_GREY))
        self.amt = amt

    def on_collide(self, collider: Entity):
        if type(collider) is Player:
            collider.nu += self.amt
            self.parent.entities.remove(self)
