from __future__ import annotations

from engine import Engine
from tcod import CENTER, RIGHT, LEFT, BKGND_ALPHA
from typing import TYPE_CHECKING, List
import tile
import numpy as np
import settings
import colors
if TYPE_CHECKING:
    from god_bargains import GodBargain

def render_main_screen_player(engine: Engine):
    engine.console.tiles_rgb[0:engine.game_map.width, 0:engine.game_map.height] = np.select(
        condlist=[engine.game_map.visible, engine.game_map.explored],
        choicelist=[engine.game_map.tiles["light"], engine.game_map.tiles["dark"]],
        default=tile.SHROUD,
    )

def render_main_screen_map(engine: Engine):
    engine.console.tiles_rgb[0:engine.game_map.width, 0:engine.game_map.height] = engine.game_map.tiles["light"]

def render_ui_map_builder(engine: Engine):
    #print the bottom line instuctions
    engine.console.print(int(engine.game_map.width / 4), engine.game_map.height + 1,
                         "'I': instructions    'O': options",
                         fg=colors.ORANGE,
                         alignment=CENTER)

    #print the most recent action (if it exists)
    if engine.log.messages:
        engine.console.print(int(engine.game_map.width * 3 / 4), engine.game_map.height + 1,
                             engine.log.messages[-1].full_text,
                             fg=colors.LIGHT_GREEN,
                             alignment=CENTER
                             )

def render_entities(engine: Engine):
    for entity in engine.game_map.entities:
        if engine.game_map.explored[entity.x, entity.y]:
            engine.console.tiles_rgb[entity.x, entity.y] = entity.graphic

def render_settings(engine: Engine):

    # draw a frame at 5,5 by default
    y_offset = 5

    draw_center_frame(engine, y_offset, "Settings")

    # print instrcutions
    engine.console.print(int(engine.game_map.width / 2), y_offset + 2,
                         f"Use hotkeys to increment options, hold shift to decrement",
                         fg=(colors.ORANGE),alignment=CENTER)

    # increment offset b/c of instructions line, then loop through settings and print them
    y_offset += 4
    for key in settings.SETTINGS:
        #setting variable holds min, max, etc. while key holds the name of the setting
        setting = settings.SETTINGS[key]

        engine.console.print(int(engine.game_map.width/4), y_offset,
                             f"{key} ({setting.min}-{setting.max}):",
                             fg=colors.LIGHT_GREEN)

        engine.console.print(int(engine.game_map.width*3/4), y_offset,
                             f"{round(setting.val, 2)}",
                             fg=(colors.LIGHT_GREEN), alignment=RIGHT)
        y_offset += 2

def render_instructions(engine: Engine):
    # draw a frame at it, 5,5 by default
    y_offset = 5

    draw_center_frame(engine, y_offset, "Instructions")


    engine.console.print(6, y_offset + 2,
                              f"'C' makes a random corridor.  Its length and blobulousness can be modified in settings."
                              f"\n\nBlobulousness is how blobby a corridor is.  Higher values make more open corridors."
                              f"\n\n\n'F' fills in the caverns with walls.  The radius can be modified in settings."
                              f"\n\nThe cavern radius is how many squares of floor must exist between walls before filling."
                              f"\n\n\n'S' smooths out the walls.  Smoothness can be modified in settings."
                              f"\n\nSmoothness is the number of surrrounding walls required to make another wall."
                              f"\n\n\n'R' resets the map.  The density of walls on reset can be modified in settings."
                              f"\n\nDensity is the percent of tiles that will be created as walls on a reset."
                              f"\n\n\nLeft clicking on two tiles will make a corridor between those two tiles."
                              f"\n\n\nRight clicking on a tile will make a maze with the top left corner at that point."
                              f"\n\nThe maze's width and height can be modified in settings."
                              f"\n\n\nPress space to make a randomized 'egg map'",
                              fg=colors.LIGHT_GREEN, alignment=LEFT)

def render_bargains(engine: Engine, bargains: list[GodBargain] = []):

    # draw a frame at 5,5 by default
    y_offset = 5

    draw_center_frame(engine, y_offset, "Willst thou partake?")

    # print instrcutions
    engine.console.print(int(engine.game_map.width / 2), y_offset + 2,
                         f"The gods genrously offer you the following bargains:",
                         fg=(colors.ORANGE),alignment=CENTER)

    # increment offset b/c of instructions line, then loop through bargains
    y_offset += 4
    for i, bargain in enumerate(bargains):

        engine.console.print(7, y_offset,
                             f"{i+1}) {bargain.description}",
                             fg=colors.LIGHT_GREEN)

        engine.console.print(int(engine.game_map.width*3/4), y_offset,
                             f"{bargain.cost}",
                             fg=(colors.LIGHT_GREEN), alignment=RIGHT)
        y_offset += 2


def draw_center_frame(engine: Engine, y_offset: int, title: str):
    engine.console.draw_frame(y_offset, 5,
                              engine.game_map.width - 10, engine.game_map.height - (2 * y_offset),
                              title, clear=True,
                              fg=colors.WHITE, bg=colors.BLACK
                              )

def render_main_menu(engine: Engine):
    engine.console.print(
        engine.console.width // 2,
        engine.console.height // 2 - 4,
        "NuRogue",
        fg=colors.WHITE,
        alignment=CENTER,
    )
    engine.console.print(
        engine.console.width // 2,
        engine.console.height - 2,
        "By Zishaf",
        fg=colors.WHITE,
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

def render_nu(engine: Engine):
    #print the bottom line instuctions
    engine.console.print(int(engine.game_map.width / 2), engine.game_map.height + 1,
                         f"Nu: {engine.player.nu}",
                         fg=colors.ORANGE,
                         alignment=CENTER)
