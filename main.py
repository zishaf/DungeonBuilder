import tcod
from dungeon_features import PyramidMaze, PerfectMaze
from event_handler import EventHandler

#copy-pasted bitwise magic, lets me resize the window
FLAGS = tcod.context.SDL_WINDOW_RESIZABLE | tcod.context.SDL_WINDOW_MAXIMIZED
WIDTH, HEIGHT = 100, 70

"""
TEST VARIABLES FOR MAZES
"""
maze_x, maze_y, maze_width, maze_height = 1, 1, 83, 56

def main() -> None:

    tileset = tcod.tileset.load_tilesheet("Anno_16x16.png", 16, 16, tcod.tileset.CHARMAP_CP437)
    console = tcod.Console(WIDTH, HEIGHT, order="F")

    #some tiles weren't loading from test tilesheets, this fixes it but possibly fucks up default ibm codes
    for i in range(256):
        tileset.remap(i,i%16,int(i/16))

    with tcod.context.new(
            width=WIDTH,
            height=HEIGHT,
            tileset=tileset,
            title="Cellular Automata",
            vsync=True,
            sdl_window_flags=FLAGS
    ) as context:

        event_handler = EventHandler(context, console)

        # load a maze on start for testing
        event_handler.game_map.tiles[maze_x:maze_x + maze_width, maze_y:maze_y + maze_height] = PerfectMaze(maze_width, maze_height).tiles

        event_handler.update_console()

        #TODO make a good main loop (implement some delay to allow rendering? doesn't update when a key is held down with a big map)
        while True:

            for event in tcod.event.wait():
                context.convert_event(event)
                event_handler.dispatch(event)
                event_handler.update_console()

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