import event_handler
import tcod
from engine import Engine

#imports for testing purposes
from test_functions import make_cavern_map
from architect import make_maze, floor_segments, max_histogram, find_rectangle, reset_map

#copy-pasted bitwise magic, lets me resize the window
FLAGS = tcod.context.SDL_WINDOW_RESIZABLE | tcod.context.SDL_WINDOW_MAXIMIZED
WIDTH, HEIGHT = 100, 70

def main() -> None:

    tileset = tcod.tileset.load_tilesheet("Anno_16x16.png", 16, 16, tcod.tileset.CHARMAP_CP437)
    console = tcod.Console(WIDTH, HEIGHT, order="F")

    #some tiles weren't loading from test tilesheets, this fixes it but possibly fucks up default ibm codes
    for i in range(256):
        tileset.remap(i, i%16, int(i/16))

    with tcod.context.new(
            width=WIDTH,
            height=HEIGHT,
            tileset=tileset,
            title="Cellular Automata",
            vsync=True,
            sdl_window_flags=FLAGS
    ) as context:

        engine = Engine(context, console)
        handler = event_handler.EventHandler(engine)

        #make_cavern_map(engine.game_map, 0.5, 5, 10, engine, handler)
        # load a maze on start for testing
        """
        maze_x, maze_y, maze_width, maze_height = 1, 1, engine.game_map.width-2, engine.game_map.height-2
        make_maze(engine.game_map, maze_width, maze_height, maze_x, maze_y)
        """

        handler.on_render()

        #TODO make a good main loop (implement some delay system for rendering?)
        while True:

            for event in tcod.event.wait():
                context.convert_event(event)
                handler = handler.handle_events(event)
                if isinstance(handler, event_handler.EventHandler):
                    handler.on_render()
                    context.present(console)

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