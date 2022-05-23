import event_handler
import tcod
import os
from engine import Engine

# copy-pasted bitwise magic, lets me resize the window
FLAGS = tcod.context.SDL_WINDOW_RESIZABLE | tcod.context.SDL_WINDOW_MAXIMIZED

# TODO There's an error when one of these two/2 returns an odd value, needs a rework
WIDTH, HEIGHT, MAP_Y_OFFSET = 68, 52, 3


def main() -> None:
    if not os.path.exists('./resources'):
        # Create resources directory if there isn't one
        os.makedirs('./resources')
        os.makedirs('./resources/features')

    tileset = tcod.tileset.load_tilesheet("Anno_16x16.png", 16, 16, tcod.tileset.CHARMAP_CP437)
    console = tcod.Console(WIDTH, HEIGHT+MAP_Y_OFFSET, order="F")

    # some tiles weren't loading from test tilesheets, this fixes it but possibly fucks up default ibm codes
    for i in range(256):
        tileset.remap(i, i % 16, int(i / 16))

    with tcod.context.new(
            width=WIDTH,
            height=HEIGHT,
            tileset=tileset,
            title="Cellular Automata",
            vsync=True,
            sdl_window_flags=FLAGS
    ) as context:

        engine = Engine(context, console)
        handler = event_handler.MainMenuHandler(engine)

        # TODO make a good main loop (implement some delay system for rendering?)
        while True:

            for event in tcod.event.wait():
                context.convert_event(event)
                if isinstance(handler, event_handler.BaseEventHandler):
                    handler.on_render()
                    context.present(handler.engine.console)
                handler = handler.handle_events(event)



if __name__ == "__main__":
    main()


"""
TEST CODE TO VIEW NEW TILESETS

testCon = tcod.Console(16, 16, order="F")

with tcod.context.new(
        width=16,
        height=16,
        tileset=tileset,
        title="Cellular Automata",
        vsync=True,
        sdl_window_flags=FLAGS
) as context:
    while True:
        testCon.clear()
        for i in range(256):
            testCon.tiles_rgb[i%16, int(i/16)] = (i, (255, 255, 255), (0, 0, 0))
        context.present(testCon)

    for event in tcod.event.wait():
        context.convert_event(event)
        event_handler.dispatch(event)
"""
