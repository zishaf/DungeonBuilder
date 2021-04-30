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

    # TODO modify messages based on args
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
                            )
    #TODO Add mazes, egg maps
}