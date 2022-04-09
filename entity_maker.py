from __future__ import annotations

import tile_types
import colors
from tcod import path
from typing import Tuple, TYPE_CHECKING
import numpy as np

if TYPE_CHECKING:
    from architect import Floor, Feature


class Entity:
    def __init__(self, parent: Floor, x: int = None, y: int = None, graphic: tile_types.graphic_dt = None):
        self.parent = parent
        self.x, self.y = x, y
        self.graphic = graphic
        self.blocks_movement = False
        self.nu = None
        self.flags = []

    def on_collide(self, collider: Entity):
        pass


class Player(Entity):
    def __init__(self, parent: Floor, x: int = None, y: int = None, nu: int = 300):
        super().__init__(parent, x, y, (64, colors.ORANGE, colors.DARK_GREY))
        self.nu = nu
        self.blocks_movement = True

    # TODO will bump enemies and then teleport to the next step
    # noinspection PyTypeChecker
    def path_to(self, dest_x, dest_y) -> list[Tuple[int, int]]:
        cost = np.array(self.parent.tiles["walkable"], dtype=np.int8)

        graph = path.SimpleGraph(cost=cost, cardinal=1, diagonal=0)
        pathfinder = path.Pathfinder(graph)

        pathfinder.add_root((self.x, self.y))  # starting position

        # compute path and remove starting point
        steps: list[list[int]] = pathfinder.path_to((dest_x, dest_y))[1:].tolist()

        # convert from List of lists to list of Tuples
        return [(index[0], index[1]) for index in steps]


class Monster(Entity):
    def __init__(self, parent: Floor, x: int, y: int):
        super().__init__(parent, x, y, (2, colors.LIGHT_GREEN, colors.DARK_GREY))
        self.nu = 10
        self.blocks_movement = True

    def on_collide(self, collider: Entity):
        if type(collider) == Player:
            self.nu -= 10
            if self.nu <= 0:
                self.die()

    def die(self):
        self.parent.entities.remove(self)
        self.parent.entities.append(NuPile(self.parent, self.x, self.y, 5))

    def take_turn(self) -> None:
        pass


class NuPile(Entity):
    def __init__(self, parent: Feature, x: int, y: int, amt: int):
        super().__init__(parent, x, y, (15, colors.GOLD, colors.DARK_GREY))
        self.amt = amt

    def on_collide(self, collider: Entity):
        if type(collider) == Player:
            collider.nu += self.amt
            self.parent.entities.remove(self)
