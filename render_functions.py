from __future__ import annotations

import random
import time

from engine import Engine
from tcod import CENTER, RIGHT, LEFT, BKGND_ALPHA
from typing import TYPE_CHECKING
import tile_types
import numpy as np
import settings
import colors
from main import WIDTH, HEIGHT

if TYPE_CHECKING:
    from god_bargains import GodBargain


def render_main_screen_player(engine: Engine):
    player_x, player_y = engine.player.x, engine.player.y
    if player_x - WIDTH//2 < 0:
        camera_x1, camera_x2 = 0, WIDTH
    elif player_x + WIDTH//2 > engine.game_map.width:
        camera_x1, camera_x2 = engine.game_map.width-WIDTH, engine.game_map.width
    else:
        camera_x1, camera_x2 = player_x - WIDTH//2, player_x + WIDTH//2
        if WIDTH % 2 == 1:
            camera_x2 += 1

    if player_y - HEIGHT//2 < 0:
        camera_y1, camera_y2 = 0, HEIGHT
    elif player_y + HEIGHT//2 > engine.game_map.height:
        camera_y1, camera_y2 = engine.game_map.height-HEIGHT, engine.game_map.height
    else:
        camera_y1, camera_y2 = player_y - HEIGHT//2, player_y + HEIGHT//2
        if HEIGHT % 2 == 1:
            camera_y2 += 1

    engine.console.tiles_rgb[0:WIDTH, 0:HEIGHT] = np.select(
        condlist=[engine.game_map.visible[camera_x1:camera_x2, camera_y1:camera_y2], engine.game_map.explored[camera_x1:camera_x2, camera_y1:camera_y2]],
        choicelist=[engine.game_map.tiles[camera_x1:camera_x2, camera_y1:camera_y2]["light"], engine.game_map.tiles[camera_x1:camera_x2, camera_y1:camera_y2]["dark"]],
        default=tile_types.SHROUD,
    )

    for entity in engine.game_map.entities:
        if engine.game_map.explored[entity.x, entity.y]:
            if entity.x in range(camera_x1, camera_x2) and entity.y in range(camera_y1, camera_y2):
                engine.console.tiles_rgb[entity.x-camera_x1, entity.y-camera_y1] = entity.graphic


def render_main_screen_map(engine: Engine):
    engine.console.tiles_rgb[0:engine.game_map.width, 0:engine.game_map.height] = np.select(
        condlist=[engine.game_map.explored],
        choicelist=[engine.game_map.tiles["light"]],
        default=tile_types.SHROUD,
    )


def render_ui_map_builder(engine: Engine):
    # print the bottom line instuctions
    engine.console.print(int(engine.game_map.width / 4), engine.game_map.height + 1,
                         "'I': instructions    'O': options",
                         fg=colors.ORANGE,
                         alignment=CENTER)

    # print the most recent action (if it exists)
    if engine.log.messages:
        engine.console.print(int(engine.game_map.width * 3 / 4), engine.game_map.height + 1,
                             engine.log.messages[-1].full_text,
                             fg=colors.LIGHT_GREEN,
                             alignment=CENTER
                             )


def render_entities_map(engine: Engine):
    for entity in engine.game_map.entities:
        if not entity.x or not entity.y:
            continue
        if engine.game_map.explored[entity.x, entity.y]:
            engine.console.tiles_rgb[entity.x, entity.y] = entity.graphic


def render_settings(engine: Engine):
    # draw a frame at 5,5 by default
    y_offset = 5

    draw_center_frame(engine, y_offset, "Settings")

    # print instrcutions
    engine.console.print(int(WIDTH / 2), y_offset + 2,
                         f"Use keys to increment options, hold shift to decrement",
                         fg=colors.ORANGE, alignment=CENTER)

    # increment offset b/c of instructions line, then loop through settings and print them
    y_offset += 4
    for key in settings.SETTINGS:
        # setting variable holds min, max, etc. while key holds the name of the setting
        setting = settings.SETTINGS[key]

        engine.console.print(int(WIDTH / 4), y_offset,
                             f"{key} ({setting.min}-{setting.max}):",
                             fg=colors.LIGHT_GREEN)

        engine.console.print(int(WIDTH * 3 / 4), y_offset,
                             f"{round(setting.val, 2)}",
                             fg=colors.LIGHT_GREEN, alignment=RIGHT)
        y_offset += 2


# TODO update with all your cool new shit!
def render_instructions(engine: Engine):
    # draw a frame at it, 5,5 by default
    y_offset = 5

    draw_center_frame(engine, y_offset, "Instructions")

    engine.console.print(6, y_offset + 2,
                         f"'C' makes a random corridor."
                         f"\n\nYou can change its length and blobulessness."
                         f"\n\n\n'F' fills in the caverns with walls."
                         f"\n\nYou can set the cavern radius."
                         f"\n\n\n'S' smooths out the walls."
                         f"\n\nHigh smoothness means more walls"
                         f"\n\n\n'R' resets the map."
                         f"\n\nYou can set how densely it will be filled"
                         f"\n\n\nLeft clicking on two tiles will make a corridor."
                         f"\n\n\nRight clicking on a tile will make a maze there."
                         f"\n\nThe maze's width and height can be modified in settings."
                         f"\n\n\nYou can also make an eg(g), wi(n)ding, or ca(v)ern map"
                         ,
                         fg=colors.LIGHT_GREEN, alignment=LEFT)


def render_bargains(engine: Engine, bargains: list[GodBargain]):

    # draw a frame at 5,5 by default
    y_offset = 5

    draw_center_frame(engine, y_offset, "Willst thou partake?")

    # print instrcutions
    engine.console.print(int(WIDTH / 2), y_offset + 2,
                         f"The gods genrously offer you the following bargains:",
                         fg=colors.ORANGE, alignment=CENTER)

    # increment offset b/c of instructions line, then loop through bargains
    y_offset += 4
    for i, bargain in enumerate(bargains):
        engine.console.print(7, y_offset,
                             f"{i + 1}) {bargain.description}",
                             fg=colors.LIGHT_GREEN)

        engine.console.print(int(WIDTH * 3 / 4), y_offset,
                             f"{bargain.cost}",
                             fg=colors.LIGHT_GREEN, alignment=RIGHT)
        y_offset += 2


def draw_center_frame(engine: Engine, y_offset: int, title: str):
    engine.console.draw_frame(y_offset, 5,
                              WIDTH - 10, HEIGHT - (2 * y_offset),
                              title, clear=True,
                              fg=colors.WHITE, bg=colors.BLACK
                              )


def render_main_menu(engine: Engine):
    engine.console.print(
        engine.console.width // 2,
        engine.console.height // 2 - 4,
        "Faith in the Crystal",
        fg=colors.CRYSTAL,
        alignment=CENTER,
    )

    menu_width = 24
    for i, text in enumerate(
            ["[M]ap Maker", "[P]lay the \"Game\""]
    ):
        engine.console.print(
            engine.console.width // 2,
            engine.console.height // 2 - 2 + i,
            text.ljust(menu_width),
            fg=colors.WHITE,
            bg=colors.BLACK,
            alignment=CENTER,
            bg_blend=BKGND_ALPHA(64),
        )


def render_loading_screen(engine: Engine):
    engine.console.clear()
    engine.console.print(
        engine.console.width // 2,
        engine.console.height // 2 - 4,
        "Loading level, please wait",
        fg=colors.CRYSTAL,
        alignment=CENTER,
    )
    engine.context.present(engine.console)


def render_bottom_bar_player(engine: Engine):
    # print the bottom line instuctions
    engine.console.print(int(WIDTH / 4), HEIGHT + 1,
                         f"Nu: {engine.player.nu}",
                         fg=colors.ORANGE,
                         alignment=CENTER)

    if engine.log.messages:
        engine.console.print(int(WIDTH * 3 / 4), HEIGHT + 1,
                             engine.log.messages[-1].full_text,
                             fg=colors.CRYSTAL,
                             alignment=CENTER
                             )


# using a mutable default argument should populate after running once and keep it, so it won't run again
def render_game_over(engine: Engine, show_once=[]):
    if show_once:
        return

    y_offset = 5

    engine.console.clear()
    draw_center_frame(engine, y_offset, "Thou hast perished most " + random.choice(["sadly", "foolishly", "amusingly"]))

    menu_width = 24
    for i, text in enumerate(
            ["[M]ain Menu", "[Q]uit"]
    ):
        engine.console.print(
            engine.console.width // 2,
            engine.console.height // 2 - 2 + i,
            text.ljust(menu_width),
            fg=colors.WHITE,
            bg=colors.BLACK,
            alignment=CENTER,
            bg_blend=BKGND_ALPHA(64),
        )

    engine.context.present(engine.console)

    show_once.append(True)


# using a mutable default argument should populate after running once and keep it, so it won't run again
def render_win_screen(engine: Engine, show_once=[]):
    if show_once:
        return

    y_offset = 5
    engine.console.clear()
    draw_center_frame(engine, y_offset, "~~~~~~~~~~~~~~~~~~~~~~~")

    for i, text in enumerate(
            ["At last", "thou hast", "thy victory"]
    ):
        engine.console.print(
            engine.console.width // 2,
            engine.console.height // 2 - 2 + i,
            text,
            fg=colors.GOLD,
            bg=colors.BLACK,
            alignment=CENTER,
            bg_blend=BKGND_ALPHA(64),
        )

        engine.context.present(engine.console)
        time.sleep(1)

    show_once.append(True)
