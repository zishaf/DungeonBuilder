import architect
from dungeon_features import Floor
from settings import SETTINGS
from tcod import event

class Action():
    def __init__(self, hotkey, message, func, *settings):
        self.hotkey = hotkey
        self.message = message
        self.func = func
        self.args = settings

    def perform(self, map: Floor):
        params = (map,)
        for arg in self.args:
            params += (arg.val,)
        self.func(*params)

ACTIONS = {
    "Smooth":   Action(event.K_s,"Smoothed walls", architect.smooth_it_out,
                       SETTINGS["(S)moothness"]),
    "Fill":     Action(event.K_f, "Filled caverns", architect.fill_caverns,
                       SETTINGS["(F)ill Radius"]),
    "Reset":    Action(event.K_r, "Reset map",      architect.reset_map,
                       SETTINGS["(D)enseness"]),
    "Corridor": Action(event.K_c, "Made corridor",  architect.random_corridor,
                       SETTINGS["Corridor (L)ength"], SETTINGS["(B)lobulousness"])
    #TODO Add mazes, egg maps
}