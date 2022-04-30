from __future__ import annotations
from typing import TYPE_CHECKING

import random

if TYPE_CHECKING:
    from engine import Engine
    from entity_maker import Monster


def rook_target(engine: Engine, monster: Monster):
    p_x, p_y = engine.player.x, engine.player.y
    if [p_x, p_y] in engine.viewshed(monster):
        dest_x, dest_y = monster.path_to(p_x, p_y)[0]
        if p_x == dest_x and p_y == dest_y:
            engine.player.nu -= 5
            words = ['Ouch!', 'Fuck!', 'Shit!', "Got'em", 'Yowzers', 'Bop!']
            engine.log.add_message(random.choice(words) + ' (-5 nu)')
        else:
            engine.move_entity(dest_x, dest_y, monster)

