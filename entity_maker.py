from __future__ import annotations

import tile
import colors
from tcod import path
from typing import Tuple, TYPE_CHECKING
import numpy as np

if TYPE_CHECKING:
    from architect import Floor

class Entity():
    def __init__(self, parent: Floor, x: int = None, y: int = None, graphic: tile.graphic_dt = None):
        self.parent = parent
        self.x, self.y = x, y
        self.graphic = graphic
        self.blocks_movement = False

    def on_collide(self):
        pass

class Player(Entity):
    def __init__(self, parent: Floor, x: int = None, y: int = None, nu = 1000):
        super().__init__(parent, x, y, (64, colors.ORANGE, colors.DARK_GREY))
        self.nu = nu
        self.blocks_movement = True
        self.flags = {
            "see_through_walls": False,
            "one_eyed": False,
            "see_stairs": False
        }

    def move(self, dest_x, dest_y) -> bool:
        #can only move to floors
        if self.parent.tiles[dest_x, dest_y]["walkable"]:
            for entity in self.parent.entities:
                if (dest_x, dest_y) == (entity.x, entity.y):
                    entity.on_collide(self)
                    if entity.blocks_movement:
                        self.nu -= 1
                        return False
            self.x, self.y = dest_x, dest_y
            self.nu -= 1
            return True
        return False

    #TODO will bump enemies and then teleport to the next step
    def auto_run(self, dest_x, dest_y) -> list[Tuple[int, int]]:
        cost = np.array(self.parent.tiles["walkable"], dtype=np.int8)

        graph = path.SimpleGraph(cost=cost, cardinal=1, diagonal=0)
        pathfinder = path.Pathfinder(graph)

        pathfinder.add_root((self.x, self.y))  # starting position

        # compute path and remove starting point
        steps: List[List[int]] = pathfinder.path_to((dest_x, dest_y))[1:].tolist()

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
    def __init__(self, parent: Floor, x: int, y: int, amt: int):
        super().__init__(parent, x, y, (15, colors.GOLD, colors.DARK_GREY))
        self.amt = amt

    def on_collide(self, collider: Entity):
        if type(collider) == Player:
            collider.nu += self.amt
            self.parent.entities.remove(self)
