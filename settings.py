# in game settings with their default and increments
from tcod import event


class Setting:
    def __init__(self, hotkey, minimum, maximum, val, inc):
        self.hotkey = hotkey
        self.min = minimum
        self.max = maximum
        self.val = val
        self.inc = inc

    def increment(self, negative: bool):
        if negative:
            self.val = max(self.min, self.val-self.inc)
        else:
            self.val = min(self.max, self.val+self.inc)


SETTINGS = {
    "(B)lobulousness"  : Setting(event.K_b, 0, 3, 0, 1),
    "(D)enseness"      : Setting(event.K_d, 0.0, 1.0, 0.5, 0.05),
    "(S)moothness"     : Setting(event.K_s, 0, 10, 5, 1),
    "Corridor (L)ength": Setting(event.K_l, 1, 70, 15, 1),
    "(F)ill Radius"    : Setting(event.K_f, 0, 10, 2, 1),
    "Maze (W)idth"     : Setting(event.K_w, 5, 60, 20, 1),
    "Maze (H)eight"    : Setting(event.K_h, 5, 60, 20, 1),
}
