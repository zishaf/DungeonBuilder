from __future__ import annotations
from typing import TYPE_CHECKING

import random
import tile_types

if TYPE_CHECKING:
    from engine import Engine
    from entity_maker import Monster

words = ['Ouch!', 'Fuck!', 'Shit!', "Got'em", 'Yowzers', 'Bop!']


def rook_target(engine: Engine, monster: Monster):
    # store player and monster coords for convenient access
    p_x, p_y, m_x, m_y = engine.player.x, engine.player.y, monster.x, monster.y

    # the direction the monster is aimed, will
    dx, dy = 0, 0

    # if the y coords are closer than x, move horizontally
    if abs(p_x - m_x) > abs(p_y - m_y):
        dx = 1 if p_x > m_x else -1
    else:
        dy = 1 if p_y > m_y else -1

    # walk in the target direction until a wall is hit or 8 squares
    distance = 0
    while engine.game_map.tiles[m_x, m_y] == tile_types.floor and distance < 8:
        distance += 1
        m_x += dx
        m_y += dy
        monster.target_tiles.append((m_x, m_y))


def bishop_target(engine: Engine, monster: Monster):
    # store player and monster coords for convenient access
    p_x, p_y, m_x, m_y = engine.player.x, engine.player.y, monster.x, monster.y

    # move both horizontally and vertically towards player (who knows what to do on zero?)
    dx = 1 if m_x < p_x else -1
    dy = 1 if m_y < p_y else -1

    # walk in the target direction until a wall is hit or 8 squares
    distance = 0
    while engine.game_map.tiles[m_x, m_y] == tile_types.floor and distance < 8:
        distance += 1
        m_x += dx
        m_y += dy
        monster.target_tiles.append((m_x, m_y))


def move_to_target(engine: Engine, monster: Monster):
    for (x, y) in monster.target_tiles:
        if engine.game_map.tiles[x, y] == tile_types.wall:
            monster.target_tiles = []
            return

        for entity in engine.entities:
            if x == entity.x and y == entity.y:
                engine.log.add_message(random.choice(words) + ' (-5 nu)')
                entity.on_collide(entity)
                monster.target_tiles = []
                return

        monster.x, monster.y = x, y
    monster.target_tiles = []
