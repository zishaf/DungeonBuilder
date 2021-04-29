from engine import Engine
from tcod import CENTER
from tcod import RIGHT
from tcod import LEFT
import settings
import colors

def render_main_screen(engine: Engine):

    #draw the game map
    engine.game_map.render(engine.console)

    #print the bottom line instuctions
    engine.console.print(int(engine.game_map.width / 4), engine.game_map.height + 1,
                         "Press 'I' for instructions and 'O' for settings.",
                         fg=colors.ORANGE,
                         alignment=CENTER)

    #print the most recent action (if it exists)
    if engine.log.messages:
        engine.console.print(int(engine.game_map.width * 3 / 4), engine.game_map.height + 1,
                             engine.log.messages[-1].full_text,
                             fg=colors.LIGHT_GREEN,
                             alignment=CENTER
                             )

def render_settings(engine: Engine):
    # TODO make it prettier (code and display)!

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

    engine.console.print(int(engine.game_map.width / 2), y_offset + 2,
                              f"(C) to corridor, (F) to fill caverns, (S) to smooth it out, and (R) to reset map",
                              fg=colors.LIGHT_GREEN, alignment=CENTER)

def draw_center_frame(engine: Engine, y_offset: int, title: str):
    engine.console.draw_frame(y_offset, 5,
                              engine.game_map.width - 10, engine.game_map.height - (2 * y_offset),
                              title, clear=True,
                              fg=colors.WHITE, bg=colors.BLACK
                              )