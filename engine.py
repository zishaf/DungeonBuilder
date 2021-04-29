import architect
import tcod
from message_log import MessageLog
from settings import SETTINGS

#TODO add player, nu, and flickering halls

MAP_Y_OFFEST = 3
MAP_X_OFFSET = 0

class Engine:

    def __init__(self, context, console: tcod.console.Console):
        #make a new game map and default event handler
        self.log = MessageLog()
        self.console = console
        self.context = context
        self.game_map = architect.Floor(console.width - MAP_X_OFFSET, console.height - MAP_Y_OFFEST)