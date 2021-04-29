from typing import Optional, Union

import actions
import render_functions
import settings
import tcod.console
import tcod.event
from engine import Engine

MAP_Y_OFFEST = 3
MAP_X_OFFSET = 0

ActionOrHandler = Union[actions.Action, "EventHandler"]

class EventHandler(tcod.event.EventDispatch[None]):

    #Main handler, has a log and engine (for console/context)
    def __init__(self, engine: Engine):
        self.engine = engine

    def ev_quit(self, event: tcod.event.Quit):
        raise SystemExit()

    #dispatch the event and perform any actions that are returned, then return the active handler
    def handle_events(self, event: tcod.event.Event) -> "EventHandler":
        action_or_state = self.dispatch(event)

        #if an event handler is returned by event dispatch, set that as the handler
        if isinstance(action_or_state, EventHandler):
            return action_or_state

        #if an action is returned by dispatch, perform then return self as the active handler
        if isinstance(action_or_state, actions.Action):
            action_or_state.perform(self.engine.game_map)
            self.engine.log.add_message(action_or_state.message)

        #if no return type is found (unprogrammed event), return self as active handler
        return self

    #event handlers' on_render will call appropriate functions from render_functions
    def on_render(self):
        self.engine.console.clear()

        render_functions.render_main_screen(self.engine)

    def ev_keydown(self, event: tcod.event.KeyDown) -> Optional[ActionOrHandler]:
        key = event.sym

        if key == tcod.event.K_ESCAPE:
            raise SystemExit()

        #if the key matches a different handler type, return that handler with self as its parent
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

    def handle_events(self, event: tcod.event.Event) -> "EventHandler":
        action_or_state = self.dispatch(event)
        if isinstance(action_or_state, EventHandler):
            return action_or_state
        return self

    def on_render(self):
        super().on_render()

        render_functions.render_settings(self.engine)

    def ev_keydown(self, event: tcod.event.KeyDown) -> "EventHandler":
        key = event.sym

        #check settings against hotkeys
        for setting in settings.SETTINGS.values():

            if key == setting.hotkey:
                #increment the matching setting, passing negative parameter as TRUE if a shift key is held
                setting.increment(negative=event.mod & (tcod.event.KMOD_LSHIFT | tcod.event.KMOD_RSHIFT))

        #make the parent handler again on escape key
        if key == tcod.event.K_ESCAPE:
            return self.parent

        return self

class InstructionsHandler(EventHandler):

    def __init__(self, parent: EventHandler):
        self.parent = parent
        self.engine = parent.engine

    def handle_events(self, event: tcod.event.Event) -> "EventHandler":
        action_or_state = self.dispatch(event)
        if isinstance(action_or_state, EventHandler):
            return action_or_state
        return self

    def on_render(self):
        super().on_render()

        render_functions.render_instructions(self.engine)

    def ev_keydown(self, event: tcod.event.KeyDown) -> "EventHandler":
        return self.parent