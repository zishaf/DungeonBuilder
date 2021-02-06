import tcod
from dungeon_features import PyramidMaze
from event_handler import EventHandler

#copy-pasted bitwise magic, lets me resize the window
FLAGS = tcod.context.SDL_WINDOW_RESIZABLE | tcod.context.SDL_WINDOW_MAXIMIZED
WIDTH, HEIGHT = 80, 55

def main() -> None:

    tileset = tcod.tileset.load_tilesheet("Anno_16x16.png", 16, 16, tcod.tileset.CHARMAP_CP437)
    console = tcod.Console(WIDTH, HEIGHT, order="F")
    event_handler = EventHandler(console)

    #some tiles weren't loading from test tilesets, this fixes it but possibly fucks up default ibm codes
    for i in range(256):
        tileset.remap(i,i%16,int(i/16))

    maze_width, maze_height = 23, 20
    event_handler.game_map.tiles[0:maze_width,0:maze_height] = PyramidMaze(maze_width, maze_height).tiles

    with tcod.context.new(
            width=WIDTH,
            height=HEIGHT,
            tileset=tileset,
            title="Cellular Automata",
            vsync=True,
            sdl_window_flags=FLAGS
    ) as context:

        #TODO make a good main loop (implement some delay to allow rendering? doesn't update when a key is held down with a big map)
        while True:
            console.clear()
            event_handler.updateConsole()
            context.present(console)

            for event in tcod.event.wait():
                context.convert_event(event)
                event_handler.dispatch(event)

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