from typing import Optional, Union

import actions
import architect
import render_functions
import settings
import tcod.console
import tcod.event
import tile
import time
import entity_maker
import numpy as np
from test_functions import make_egg_map, random_floor, make_cavern_map, make_winding_map
from god_bargains import see_through_walls, one_eyed, see_stairs
from engine import Engine

from tile import filled

MAP_Y_OFFEST = 3
MAP_X_OFFSET = 0

MOVE_KEYS = {
    # arrow keys
    tcod.event.K_UP: (0, -1),
    tcod.event.K_DOWN: (0, 1),
    tcod.event.K_LEFT: (-1, 0),
    tcod.event.K_RIGHT: (1, 0),
    # numpad keys
    tcod.event.K_KP_2: (0, 1),
    tcod.event.K_KP_4: (-1, 0),
    tcod.event.K_KP_6: (1, 0),
    tcod.event.K_KP_8: (0, -1),
}

NUMBER_KEYS = {
    tcod.event.K_1: 0,
    tcod.event.K_2: 1,
    tcod.event.K_3: 2,
    tcod.event.K_4: 3,
    tcod.event.K_5: 4,
    tcod.event.K_6: 5,

}

WAIT_KEYS = {
    tcod.event.K_PERIOD,
    tcod.event.K_KP_5,
    tcod.event.K_CLEAR,
}

#ActionOrHandler return structure lifted from http://rogueliketutorials.com/tutorials/tcod/v2/
ActionOrHandler = Union[actions.Action, "BaseEventHandler"]
class BaseEventHandler(tcod.event.EventDispatch[None]):
    #Main handler, has a log and engine (for console/context)
    def __init__(self, engine: Engine):
        self.engine = engine

    # dispatch the event and perform any actions that are returned, then return the active handler
    def handle_events(self, event: tcod.event.Event) -> "BaseEventHandler":
        action_or_state = self.dispatch(event)

        # if an event handler is returned by event dispatch, set that as the handler
        if isinstance(action_or_state, BaseEventHandler):
            return action_or_state

        # if an action is returned by dispatch, perform then return self as the active handler
        if isinstance(action_or_state, actions.Action):
            action_or_state.perform(self.engine.game_map)
            self.engine.log.add_message(action_or_state.message)

        # if no return type is found (unprogrammed event), return self as active handler
        return self

    def on_render(self) -> None:
        raise NotImplementedError()

    def ev_quit(self, event: tcod.event.Quit):
        raise SystemExit()

class MainMenuHandler(BaseEventHandler):

    def on_render(self) -> None:
        render_functions.render_main_menu(self.engine)

    def ev_keydown(self, event: tcod.event.KeyDown) -> Optional[ActionOrHandler]:
        if event.sym in (tcod.event.K_q, tcod.event.K_ESCAPE):
            raise SystemExit
        elif event.sym == tcod.event.K_m:
            self.engine.game_map.reveal_tiles()
            maze_x, maze_y, maze_width, maze_height = 1, 1, self.engine.game_map.width-2, self.engine.game_map.height-2
            maze = architect.BraidMaze(maze_width, maze_height)
            self.engine.game_map.tiles[maze_x:maze_x+maze_width, maze_y:maze_y+maze_height] = maze.tiles
            return MapBuildingHandler(self.engine)

        elif event.sym == tcod.event.K_p:
            maze = architect.make_new_maze_floor(self.engine.game_map)
            self.engine.player.x = maze.ent_x + maze.x
            self.engine.player.y = maze.ent_y + maze.y

            if(self.engine.player.flags["see_stairs"]):
                self.engine.game_map.explored[maze.ext_x + maze.x, maze.ext_y + maze.y] = True

            return PlayerMoverHandler(self.engine)

        return self

class MapBuildingHandler(BaseEventHandler):

    #event handlers' on_render will call appropriate functions from render_functions
    def on_render(self):
        self.engine.console.clear()
        render_functions.render_main_screen_map(self.engine)
        render_functions.render_ui_map_builder(self.engine)

    def ev_keydown(self, event: tcod.event.KeyDown) -> Optional[ActionOrHandler]:
        key = event.sym

        if key == tcod.event.K_ESCAPE:
            raise SystemExit()

        #if the key matches a different handler type, return that handler with self as its parent
        elif key == tcod.event.K_o:
            return SettingsHandler(parent=self)

        elif key == tcod.event.K_i:
            return InstructionsHandler(parent=self)

        elif key == tcod.event.K_SPACE:
            make_egg_map(self.engine.game_map, self.engine, self)

        elif key == tcod.event.K_RETURN:
            make_cavern_map(self.engine.game_map, 0.5, 5, 7, self.engine, self)

        elif key == tcod.event.K_k:
            make_winding_map(self.engine.game_map, self.engine, self)

        elif key == tcod.event.K_TAB:
            architect.connect_adjacent_segments(self.engine.game_map)

        elif key == tcod.event.K_h:
            architect.make_max_maze(self.engine.game_map)

        elif key == tcod.event.K_p:
            return GodBargainHandler(parent=self)

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

        #on right switch to player control mode and place player
        elif mb == tcod.event.BUTTON_RIGHT:
            self.engine.player.x, self.engine.player.y = (x, y)
            self.engine.game_map.hide_tiles()
            return PlayerMoverHandler(self.engine)

        elif mb == tcod.event.BUTTON_MIDDLE:
            tic = time.perf_counter()

            filled_tiles, boundaries = architect.flood_fill_floor(self.engine.game_map, x, y)
            for x, y in filled_tiles:
                self.engine.game_map.tiles[x, y] = tile.filled

            toc = time.perf_counter()

            print(f"Filled in {toc - tic:0.4f} seconds")

class SettingsHandler(BaseEventHandler):

    def __init__(self, parent: BaseEventHandler):
        self.parent = parent
        self.engine = parent.engine

    #will return a new event handler if we leave settings screen, else self
    def handle_events(self, event: tcod.event.Event) -> "BaseEventHandler":
        action_or_state = self.dispatch(event)
        if isinstance(action_or_state, BaseEventHandler):
            return action_or_state
        return self

    def on_render(self):
        self.parent.on_render()

        render_functions.render_settings(self.engine)

    def ev_keydown(self, event: tcod.event.KeyDown) -> "BaseEventHandler":
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

class InstructionsHandler(BaseEventHandler):

    def __init__(self, parent: BaseEventHandler):
        self.parent = parent
        self.engine = parent.engine

    def handle_events(self, event: tcod.event.Event) -> "BaseEventHandler":
        action_or_state = self.dispatch(event)
        if isinstance(action_or_state, BaseEventHandler):
            return action_or_state
        return self

    def on_render(self):
        self.parent.on_render()

        render_functions.render_instructions(self.engine)

    def ev_keydown(self, event: tcod.event.KeyDown) -> "BaseEventHandler":
        #the escape key returns to the parent handler
        return self.parent if event.sym == tcod.event.K_ESCAPE else self


class GodBargainHandler(BaseEventHandler):
    def __init__(self, engine: Engine):
        self.engine = engine
        self.bargains = [see_through_walls, one_eyed, see_stairs]

    def handle_events(self, event: tcod.event.Event) -> "BaseEventHandler":
        action_or_state = self.dispatch(event)
        if isinstance(action_or_state, BaseEventHandler):
            return action_or_state
        return self

    def on_render(self):
        self.engine.console.clear()

        render_functions.render_main_screen_player(self.engine)
        render_functions.render_entities(self.engine)

        render_functions.render_bargains(self.engine, self.bargains)

    def ev_keydown(self, event: tcod.event.KeyDown) -> "BaseEventHandler":
        key = event.sym
        # the escape key returns to the parent handler

        if key in NUMBER_KEYS:
            if NUMBER_KEYS[key] < len(self.bargains):
                self.bargains[NUMBER_KEYS[key]].func(self.engine)
                return PlayerMoverHandler(self.engine)
        elif key == tcod.event.K_ESCAPE:
            return PlayerMoverHandler(self.engine)
        return self


class PlayerMoverHandler(BaseEventHandler):

    def ev_keydown(self, event: tcod.event.KeyDown) -> "BaseEventHandler":
        key = event.sym

        if key in MOVE_KEYS:
            dx, dy = MOVE_KEYS[key]

            if event.mod & (tcod.event.KMOD_LSHIFT | tcod.event.KMOD_RSHIFT):
                while self.engine.player.move(self.engine.player.x+dx, self.engine.player.y+dy):
                    self.on_render()
                    self.engine.context.present(self.engine.console)
                    time.sleep(.1)
            self.engine.player.move(self.engine.player.x+dx, self.engine.player.y+dy)

        elif key == tcod.event.K_SPACE:
            if self.engine.game_map.tiles[self.engine.player.x, self.engine.player.y] == tile.maze_ext:
                self.engine.game_map.entities = [self.engine.player]
                maze = architect.make_new_maze_floor(self.engine.game_map)
                self.engine.player.x = maze.ent_x + maze.x
                self.engine.player.y = maze.ent_y + maze.y
                if (self.engine.player.flags["see_stairs"]):
                    self.engine.game_map.explored[maze.ext_x + maze.x, maze.ext_y + maze.y] = True

        elif key == tcod.event.K_RETURN:
            return GodBargainHandler(self.engine)

        elif key == tcod.event.K_s:
            self.engine.game_map.reveal_tiles()
        elif key == tcod.event.K_h:
            self.engine.game_map.hide_tiles()
        elif key == tcod.event.K_ESCAPE:
            raise SystemExit()

        return self

    def on_render(self):
        self.engine.console.clear()

        self.engine.update_fov()
        render_functions.render_main_screen_player(self.engine)
        render_functions.render_entities(self.engine)
        render_functions.render_nu(self.engine)

    def ev_mousebuttondown(self, event: tcod.event.MouseButtonDown) -> Optional[ActionOrHandler]:
        mb = event.button
        player = self.engine.player

        #x, y are the locations of the click.
        x, y = event.tile

        #if not in the game map, return the handler
        if not self.engine.game_map.in_bounds(x, y):
            return self

        #left click to autorun
        if mb == tcod.event.BUTTON_LEFT:
            path = player.auto_run(x, y)
            if path:
                for tile in path:
                    player.move(*tile)
                    self.on_render()
                    self.engine.context.present(self.engine.console)
                    time.sleep(.05)

        #on right place player
        elif mb == tcod.event.BUTTON_RIGHT:
            self.engine.game_map.entities[0].x, self.engine.game_map.entities[0].y = x, y
