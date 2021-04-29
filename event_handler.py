from typing import Optional, Union

import actions
import settings
import tcod.console
import tcod.event
from engine import Engine
from message_log import MessageLog
from settings import SETTINGS

MAP_Y_OFFEST = 3
MAP_X_OFFSET = 0

ActionOrHandler = Union[actions.Action, "EventHandler"]

class EventHandler(tcod.event.EventDispatch[None]):

    #the main event handler will hold the message log
    def __init__(self, engine: Engine):
        self.log = MessageLog()
        self.engine = engine

    def ev_quit(self, event: tcod.event.Quit):
        raise SystemExit()

    def handle_events(self, event: tcod.event.Event) -> "EventHandler":
        action_or_state = self.dispatch(event)
        if isinstance(action_or_state, EventHandler):
            return action_or_state
        if isinstance(action_or_state, actions.Action):
            action_or_state.perform(self.engine.game_map)
            self.log.add_message(action_or_state.message)
        return self

    def on_render(self):
        self.engine.console.clear()
        self.engine.game_map.render(self.engine.console)

        self.engine.console.print(int(self.engine.game_map.width / 4), self.engine.game_map.height + 1,
                           "Press 'I' for instructions and 'O' for settings.",
                           fg=(200, 146, 119),
                           alignment=tcod.CENTER)

        if self.log.messages:
            self.engine.console.print(int(self.engine.game_map.width * 3 / 4), self.engine.game_map.height + 1,
                               self.log.messages[-1].full_text,
                               fg=(255, 207, 102),
                               alignment=tcod.CENTER
                               )

    def ev_keydown(self, event: tcod.event.KeyDown) -> Optional[ActionOrHandler]:
        key = event.sym

        if key == tcod.event.K_ESCAPE:
            raise SystemExit()

        elif key == tcod.event.K_o:
            return SettingsHandler(parent=self)

        elif key == tcod.event.K_i:
            return InstructionsHandler(parent=self)

        #checks if the key pressed matches a command's hotkey, and performs it if so
        for act in actions.ACTIONS.values():
            if key == act.hotkey:
                return act

    def ev_mousebuttondown(self, event: tcod.event.MouseButtonDown):
        """#either store the mouse coordinates, or draw a new corridor with stored and new coords
        mb = event.button
        x2, y2 = event.tile
        if x2 >= self.game_map.width or y2 >= self.game_map.height:
            return

        if mb is tcod.event.BUTTON_LEFT:
            if self.click_loaded:
                architect.corridor_between(self.game_map, self.x1, self.y1, x2, y2)
                self.click_loaded = False
                self.message_log.add_message(f"Made a corridor from ({self.x1},{self.y1}) to ({x2},{y2})", fg = (125,125,125))
                self.filled = []
            else:
                self.x1, self.y1 = x2, y2
                self.click_loaded = True

        if mb is tcod.event.BUTTON_RIGHT:
            self.filled.append(architect.flood_fill(self.game_map,x2, y2))
        """

class SettingsHandler(EventHandler):

    def __init__(self, parent: EventHandler):
        self.parent = parent
        self.engine = parent.engine
        self.log = parent.log

    def handle_events(self, event: tcod.event.Event) -> "EventHandler":
        action_or_state = self.dispatch(event)
        if isinstance(action_or_state, EventHandler):
            return action_or_state
        return self

    #TODO make it prettier (code and display)!
    def on_render(self):
        #render the map
        super().on_render()

        #draw a frame at it, 5,5 by default
        y_offset = 5
        self.engine.console.draw_frame(y_offset, 5,
                                       self.engine.game_map.width - 10, self.engine.game_map.height - (2*y_offset),
                                       "Settings", clear=True,
                                       fg=(255,255,255), bg=(0,0,0)
                                       )

        #print instrcutions
        self.engine.console.print(int(self.engine.game_map.width / 2), y_offset + 2,
                           f"Use hotkeys to increment options, hold shift to decrement",
                           fg=(0, 204, 153), alignment=tcod.constants.CENTER)

        #increment offset b/c of instructions line, then loop through settings and print them
        y_offset += 4
        for setting in SETTINGS:
            name = setting
            setting = SETTINGS[setting]
            self.engine.console.print(int(self.engine.game_map.width / 2), y_offset,
                               f"{name}: {round(setting.val, 2)} ({setting.min}-{setting.max})",
                               fg=(0, 102, 204), alignment=tcod.constants.CENTER)
            y_offset += 2

    def ev_keydown(self, event: tcod.event.KeyDown) -> "EventHandler":
        key = event.sym

        #if shift is held, we decrement the setting instead
        incMult = -1 if event.mod & (tcod.event.KMOD_LSHIFT | tcod.event.KMOD_RSHIFT) else 1

        #check settings against hotkeys
        for setting in settings.SETTINGS.values():

            if key == setting.hotkey:
                #increment the matching setting
                setting.set_value(setting.inc * incMult)

        #make the parent handler again on escape
        if key == tcod.event.K_ESCAPE:
            return self.parent

        return self



class InstructionsHandler(EventHandler):

    def __init__(self, parent: EventHandler):
        self.parent = parent
        self.engine = parent.engine
        self.log = parent.log

    def handle_events(self, event: tcod.event.Event) -> "EventHandler":
        action_or_state = self.dispatch(event)
        if isinstance(action_or_state, EventHandler):
            return action_or_state
        return self

    def on_render(self):
        super().on_render()

        # draw a frame at it, 5,5 by default
        y_offset = 5
        self.engine.console.draw_frame(y_offset, 5,
                                       self.engine.game_map.width - 10, self.engine.game_map.height - (2 * y_offset),
                                       "Instructions", clear=True,
                                       fg=(255, 255, 255), bg=(0, 0, 0)
                                       )
        self.engine.console.print(int(self.engine.game_map.width / 2), y_offset + 2,
                                  f"(C) to corridor, (F) to fill caverns, (S) to smooth it out, and (R) to reset map",
                                  fg=(0, 204, 153), alignment=tcod.constants.CENTER)

    def ev_keydown(self, event: tcod.event.KeyDown) -> "EventHandler":
        return self.parent