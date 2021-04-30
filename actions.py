import architect
import settings
from dungeon_features import Floor
from settings import SETTINGS
from tcod import event

class Action():
    def __init__(self, hotkey, message, func, *settings):
        self.hotkey = hotkey
        self.message = message
        self.func = func
        self.args = settings

    # TODO modify messages based on args, also mazes are adding messages even when they don't draw
    def perform(self, map: Floor):
        params = (map,)
        for arg in self.args:
            if isinstance(arg, settings.Setting):
                params += (arg.val,)
            if isinstance(arg, int):
                params += (arg, )
        self.func(*params)

    def add_args(self, *args):
        for arg in args:
            self.args += (arg,)

    def remove_args(self, n: int):
        #convert the tuple args to a list, remove the last n items of it, and convert it back to a tuple for
        lst = list(self.args)
        del lst[-n:] # <--- python is pretty cool
        self.args = tuple(lst)

ACTIONS = {
    "smooth":       Action(event.K_s,"Smoothed walls",  architect.smooth_it_out,
                           SETTINGS["(S)moothness"]),
    "fill":         Action(event.K_f, "Filled caverns", architect.fill_caverns,
                           SETTINGS["(F)ill Radius"]),
    "reset":        Action(event.K_r, "Reset map",      architect.reset_map,
                           SETTINGS["(D)enseness"]),
    "corridor":     Action(event.K_c, "Made corridor",  architect.random_corridor,
                           SETTINGS["Corridor (L)ength"], SETTINGS["(B)lobulousness"]),
    "corr_between": Action(event.BUTTON_LEFT, "Custom corridor", architect.corridor_between,
                            ),
    "maze":         Action(event.K_e,"Made a maze", architect.make_maze,
                           SETTINGS["Maze (W)idth"], SETTINGS["Maze (H)eight"])
    #TODO Add mazes, egg maps, flood fill
}