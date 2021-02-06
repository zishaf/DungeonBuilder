import architect
import tcod.console
import tcod.event
from dungeon_features import Floor
from message_log import MessageLog


#TODO reimagine this lamentable SETTINGS ACTIONS situation
class Setting():
    def __init__(self, name: str, hotkey, min, max, val, inc):
        self.name = name
        self.hotkey = hotkey
        self.min = min
        self.max = max
        self.value = val
        self.inc = inc

    def setValue(self, inc):
        self.value += inc
        if self.value < self.min: self.value = self.min
        if self.value > self.max: self.value = self.max

#TODO curious about how to pass on a different function and args to action with *, ** operators
class Action():
    def __init__(self, name: str, hotkey, desc):
        self.name = name
        self.hotkey = hotkey
        self.desc = desc

    def perform(self, function, *args):
        func(*args)

"""
The Settings:
Blobulousness - how strictly/narrowly corridors tunnel. at 0, a corridor will only tunnel to a space with 3 adjacent walls
Denseness - the percent of squares that will be walls when a new map is made
Smoothness - "smoothing" the map changes each tile based on the cells in a 3x3 around it.  smoothness determines how many
cells in that 3x3 must be walls to make the center square a wall
Cavern radius - how many blank (floor) tiles must surround a tile to make it fill with wall on fill_caverns 
"""
SETTINGS = {
    1: Setting("(B)lobulousness", tcod.event.K_b, 0, 3, 0, 1),
    2: Setting("(D)enseness", tcod.event.K_d, 0.0, 1.0, 0.5, 0.05),
    3: Setting("(S)moothness", tcod.event.K_s, 0, 9, 5, 1),
    4: Setting("Corridor (l)ength", tcod.event.K_l, 1, 70, 15, 1),
    5: Setting("Ca(v)ern radius", tcod.event.K_v, 0, 10, 2, 1)
}

ACTIONS = {
    1: Action("Smooth it out", tcod.event.K_SPACE, "Space"),
    2: Action("Fill empty caverns", tcod.event.K_f, "F key"),
    3: Action("New map (uses denseness)", tcod.event.K_RETURN, "Enter"),
    4: Action("Make a random corridor", tcod.event.K_c, "C key")
}

class EventHandler(tcod.event.EventDispatch[None]):

    def __init__(self, console: tcod.console.Console):
        self.message_log = MessageLog()
        self.game_map = Floor(console.width - 15, console.height - 12)
        self.click_loaded = False
        self.console = console

        #tester for flood fill
        self.filled = list()

    def ev_quit(self, event: tcod.event.Quit):
        raise SystemExit()

    def ev_keydown(self, event: tcod.event.KeyDown):
        key = event.sym
        msg: str = None

        #decrement settings when shift is held
        incMult = -1 if event.mod & (tcod.event.KMOD_LSHIFT | tcod.event.KMOD_RSHIFT) else 1

        #check the action hotkeys
        if key == tcod.event.K_ESCAPE:
            raise SystemExit()
        elif key == tcod.event.K_SPACE:
            architect.smooth_it_out(self.game_map, SETTINGS[3].value)
            msg = f"Smoothed at {SETTINGS[3].value}"
        elif key == tcod.event.K_RETURN:
            architect.reset_map(self.game_map, SETTINGS[2].value)
            msg = "Reset with wall% at " + "{:.2f}".format(SETTINGS[2].value)
        elif key == tcod.event.K_c:
            if architect.random_corridor(self.game_map, SETTINGS[4].value, SETTINGS[1].value):
                msg = f"Made a corridor of length {SETTINGS[4].value} and {SETTINGS[1].value} blobby."
            else:
                msg = "No possible corridor of that length and blobby!"
        elif key == tcod.event.K_f:
            architect.fill_caverns(self.game_map, radius=SETTINGS[5].value)
            msg = f"Filled caverns at {SETTINGS[5].value}"

        #check if its a setting hotkey and modify value if so
        for setting in SETTINGS.values():
            if key == setting.hotkey:
                setting.setValue(setting.inc * incMult)

        #update message log
        if msg is not None:
            self.message_log.add_message(msg, fg = (125,125,125))

        #reset display to remove old filled corridors
        self.filled = []

    def ev_mousebuttondown(self, event: tcod.event.MouseButtonDown):
        #either store the mouse coordinates, or draw a new corridor with stored and new coords
        mb = event.button
        x2, y2 = event.tile
        if x2 >= self.game_map.width or y2 >= self.game_map.height:
            return

        if mb is tcod.event.BUTTON_LEFT:
            if self.click_loaded is True:
                architect.corridor_between(self.game_map, self.x1, self.y1, x2, y2)
                self.click_loaded = False
                self.message_log.add_message(f"Made a corridor from ({self.x1},{self.y1}) to ({x2},{y2})", fg = (125,125,125))
                self.filled = []
            else:
                self.x1, self.y1 = x2, y2
                self.click_loaded = True

        if mb is tcod.event.BUTTON_RIGHT:
            self.filled.append(architect.flood_fill(self.game_map,x2, y2))

    def updateConsole(self):
        #render map
        self.game_map.render(self.console)

        #render log
        self.console.print(self.game_map.width + 1, 0, "History", fg =(102, 102, 153))
        self.message_log.render(self.console, self.game_map.width + 1, 2, width=self.console.width-(self.game_map.width+1), height=self.game_map.height - 2)

        #render instructions with helper functions
        self.render_settings()
        self.render_actions()

        for fill in self.filled:
            for x, y in fill:
                self.console.tiles_rgb[x, y] = (ord("!"), (255, 153, 153),(0,0,0))

    def render_settings(self):
        y_offset = self.game_map.height
        self.console.print(0, y_offset    , f"Use hotkeys to increment options", fg=(0, 204, 153))
        self.console.print(0, y_offset + 1, f"Hold shift to decrement options" , fg=(0, 204, 153))
        y_offset += 2

        for setting in SETTINGS.values():
            self.console.print(0, y_offset, f"{setting.name}: {round(setting.value, 2)} ({setting.min}-{setting.max})",
                               fg=(0, 102, 204))
            y_offset += 2

    def render_actions(self):
        y_offset = self.game_map.height
        for action in ACTIONS.values():
            self.console.print(int(self.console.width / 2), y_offset, f"{action.desc}: {action.name}", fg=(0, 204, 153))
            y_offset += 2

        self.console.print(int(self.console.width / 2), y_offset, f"Click two tiles to build corridor",
                           fg=(0, 204, 153))