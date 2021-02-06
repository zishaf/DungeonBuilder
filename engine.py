#currently out of use

import event_handler
import tcod
from architect import Floor
from message_log import MessageLog


#TODO add player, nu, and flickering halls

class Engine:

    def __init__(self, console: tcod.console.Console):
        self.log = MessageLog()
        self.console = console
        self.gameMap = Floor(console.width-20, console.height)
        self.eventHandler = event_handler.EventHandler(self)
        
    def updateConsole(self):
        self.console.clear()
        for x in range(len(self.gameMap.floor)):
            for y in range(len(self.gameMap.floor[x])):

                tile: Tile = self.gameMap.floor[x, y]
                self.console.tiles_rgb[x, y] = tile.graphic

        #console.tiles_rgb[0:engine.gameMap.width, 0:engine.gameMap.height] = engine.gameMap.floor[]
        self.log.render(console=self.console, x = self.gameMap.width+1, y=11, width=19, height=self.gameMap.height-20)