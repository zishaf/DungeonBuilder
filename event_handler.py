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

    def ev_mousebuttondown(self, event: tcod.event.MouseButtonDown) -> Optional[ActionOrHandler]:
        mb = event.button

        #x, y are the locations of the click.
        x, y = event.tile

        #if not in the game map, return the handler
        if not self.engine.game_map.in_bounds(x, y):
            return self

        #on left click build a corridor
        if mb == tcod.event.BUTTON_LEFT:

            #if the length is two, it is the end point. add x, y to args and make the corridor
            if len(actions.ACTIONS["corr_between"].args) == 2:
                actions.ACTIONS["corr_between"].add_args(x, y)

                return actions.ACTIONS["corr_between"]

            #otherwise it is the start point.  reset the args list to x, y
            else:
                actions.ACTIONS["corr_between"].args = (x, y)
                return self

        #on right click make a maze
        elif mb == tcod.event.BUTTON_RIGHT:

            #if there are already coords associated with maze, remove them
            if len(actions.ACTIONS["maze"].args) > 2:
                actions.ACTIONS["maze"].remove_args(2)

            #add the event coords and make the maze
            actions.ACTIONS["maze"].add_args(x, y)
            return actions.ACTIONS["maze"]


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
        #the escape key returns to the parent handler
        return self.parent if event.sym == tcod.event.K_ESCAPE else self