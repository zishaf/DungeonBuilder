#in game settings with their default and increments
from tcod import event


class Setting():
    def __init__(self, hotkey, min, max, val, inc):
        self.hotkey = hotkey
        self.min = min
        self.max = max
        self.val = val
        self.inc = inc

    def increment(self, negative: bool):
        if negative:
            self.val = max(self.min, self.val-self.inc)
        else:
            self.val = min(self.max, self.val+self.inc)
"""
The Settings:
Blobulousness - how strictly/narrowly corridors tunnel. at 0, a corridor will only tunnel to a space with 3 adjacent walls
Denseness - the percent of squares that will be walls when a new map is made
Smoothness - "smoothing" the map changes each tile based on the cells in a 3x3 around it.  smoothness determines how many
cells in that 3x3 must be walls to make the center square a wall
Cavern radius - how many blank (floor) tiles must surround a tile to make it fill with wall on fill_caverns 
"""
SETTINGS = {
    "(B)lobulousness"  : Setting(event.K_b, 0, 3, 0, 1),
    "(D)enseness"      : Setting(event.K_d, 0.0, 1.0, 0.5, 0.05),
    "(S)moothness"     : Setting(event.K_s, 0, 9, 5, 1),
    "Corridor (L)ength": Setting(event.K_l, 1, 70, 15, 1),
    "(F)ill Radius"    : Setting(event.K_f, 0, 10, 2, 1)
}