from typing import Optional, Union

import actions
import architect
import colors

import entity_maker
import render_functions
import settings
import tcod.console
import tcod.event
import numpy as np
import os
from operator import attrgetter

import tile_types
from test_functions import make_egg_map, make_cavern_map, make_winding_map
from god_bargains import see_through_walls, one_eyed, see_stairs, teleportitis, leave_walls, claustrophobia
from engine import Engine
from main import WIDTH, HEIGHT, MAP_Y_OFFSET

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

# This is the code to make a Conway's Life pattern https://conwaylife.com/wiki/
"""
LIFE_ARRAYS = np.load('resources/life/nparrays.npz', allow_pickle=True)['arr_0']

index = random.randrange(0, len(LIFE_ARRAYS))
pattern = LIFE_ARRAYS[index]
pattern_width, pattern_height = pattern.shape
self.engine.game_map.tiles[10:10+pattern_width, 10:10+pattern_height][pattern] = tile_types.acid

architect.game_of_life_cycle(self.engine.game_map, tile_types.acid, tile_types.floor)
"""

# ActionOrHandler return structure lifted from http://rogueliketutorials.com/tutorials/tcod/v2/
ActionOrHandler = Union[actions.Action, "BaseEventHandler"]


class BaseEventHandler(tcod.event.EventDispatch[None]):
    # Main handler, has a log and engine (for console/context)
    def __init__(self, eng: Engine):
        self.engine = eng

    # dispatch the event and perform any actions that are returned, then return the active handler
    def handle_events(self, event: tcod.event.Event) -> "BaseEventHandler":
        action_or_state = self.dispatch(event)

        # if an event handler is returned by event dispatch, set that as the handler
        if isinstance(action_or_state, BaseEventHandler):
            return action_or_state

        # if an action is returned by dispatch, perform then return self as the active handler
        if isinstance(action_or_state, actions.Action):
            self.engine.log.add_message(action_or_state.message)
            action_or_state.perform(self.engine.game_map)

        # if no return type is found (unprogrammed event), return self as active handler
        return self

    def on_render(self) -> None:
        raise NotImplementedError()

    def ev_quit(self, event: tcod.event.Quit):
        raise SystemExit()


class MainMenuHandler(BaseEventHandler):

    #  handlers' on_render will call appropriate functions from render_functions
    def on_render(self) -> None:
        self.engine.console.clear()
        render_functions.render_main_menu(self.engine)

    def ev_keydown(self, event: tcod.event.KeyDown) -> Optional[ActionOrHandler]:
        if event.sym in (tcod.event.K_q, tcod.event.K_ESCAPE):
            raise SystemExit

        # the m key makes a new map and allows the player to modify
        elif event.sym == tcod.event.K_m:
            self.engine.console = tcod.Console(self.engine.game_map.width, self.engine.game_map.height + MAP_Y_OFFSET,
                                               order='F')
            self.engine.game_map.reveal_tiles()

            return MapBuildingHandler(self.engine)

        # the p key puts the player in a game map
        elif event.sym == tcod.event.K_p:
            render_functions.render_loading_screen(self.engine)
            self.engine.make_new_game_map()
            return PlayerMoverHandler(self.engine)

        return self


class MapBuildingHandler(BaseEventHandler):
    def __init__(self, eng: Engine):
        super().__init__(eng)
        self.x1, self.y1, self.x2, self.y2 = None, None, None, None

    def on_render(self):
        self.engine.console.clear()
        render_functions.render_main_screen_map(self.engine)
        render_functions.render_entities_map(self.engine)
        render_functions.render_ui_map_builder(self.engine)
        if self.x2:
            render_functions.render_selected_tiles(self.engine, self.x1, self.y1, self.x2, self.y2)

    def ev_keydown(self, event: tcod.event.KeyDown) -> Optional[ActionOrHandler]:
        key = event.sym

        if (tcod.event.KMOD_LCTRL | tcod.event.KMOD_RCTRL) and key == tcod.event.K_s and self.x2:
            num = str(len(os.listdir('resources/features')))
            np.save(f"resources/features/{num}", self.engine.console.tiles_rgb[self.x1:self.x2+1, self.y1:self.y2+1])
            return self

        if key == tcod.event.K_ESCAPE:
            raise SystemExit()

        elif key == tcod.event.K_o:
            self.engine.console = tcod.console.Console(WIDTH, HEIGHT + MAP_Y_OFFSET, order='F')
            return SettingsHandler(self.engine)

        elif key == tcod.event.K_i:
            self.engine.console = tcod.console.Console(WIDTH, HEIGHT + MAP_Y_OFFSET, order='F')
            return MapInstructionsHandler(self.engine)

        elif key == tcod.event.K_p:
            if not (self.engine.player.x and self.engine.player.y):
                self.engine.place_player()

            self.engine.console = tcod.console.Console(WIDTH, HEIGHT + MAP_Y_OFFSET, order='F')
            self.engine.log.add_message("Welcome to the Crystal Caves", colors.CRYSTAL)
            return PlayerMoverHandler(self.engine)

        elif key == tcod.event.K_g:
            make_egg_map(self.engine.game_map)
            self.engine.log.add_message('Made egg map')

        elif key == tcod.event.K_v:
            make_cavern_map(self.engine.game_map, 0.5, 5, 7)
            self.engine.log.add_message('Made cavern map')

        elif key == tcod.event.K_n:
            make_winding_map(self.engine.game_map)
            self.engine.log.add_message('Made winding map')

        elif key == tcod.event.K_TAB:
            architect.connect_adjacent_segments(self.engine.game_map)

        elif key == tcod.event.K_j:
            architect.fast_corr(self.engine.game_map, 20)

        # checks if the key pressed matches a command's hotkey, and performs it if so
        for act in actions.ACTIONS.values():
            if key == act.hotkey:
                return act

    def ev_mousebuttondown(self, event: tcod.event.MouseButtonDown) -> Optional[ActionOrHandler]:
        mb = event.button

        # x, y are the locations of the click.
        x, y = event.tile

        # if not in the game map, return the handler
        if not self.engine.game_map.in_bounds(x, y):
            return self

        # on left click build a corridor
        if mb == tcod.event.BUTTON_LEFT:
            mod = tcod.event.Modifier(192)
            if mod & tcod.event.Modifier.SHIFT:
                self.engine.entities.append(entity_maker.Monster(self.engine, x, y))
                return self

            # if the length is two, it is the end point. add x, y to args and make the corridor
            if len(actions.ACTIONS["corr_between"].args) == 2:
                actions.ACTIONS["corr_between"].add_args(x, y)

                return actions.ACTIONS["corr_between"]

            # otherwise it is the start point.  reset the args list to x, y
            else:
                actions.ACTIONS["corr_between"].args = (x, y)
                return self

        # TODO will only work if top left is selected before bottom right
        # on right click select corners of a grid for saving.
        elif mb == tcod.event.BUTTON_RIGHT:
            if tcod.event.KMOD_LCTRL:
                self.engine.player.x, self.engine.player.y = x, y
                return self

            if not self.x1:
                self.x1, self.y1 = x, y
            elif not self.x2:
                self.x2, self.y2 = x, y
            else:
                self.x1, self.y1, self.x2, self.y2 = x, y, None, None

        elif mb == tcod.event.BUTTON_MIDDLE:
            w, h = settings.SETTINGS["Maze (W)idth"].val, settings.SETTINGS["Maze (H)eight"].val
            if self.engine.game_map.in_bounds(x + w, y + h):
                self.engine.game_map.tiles[x: x + w, y:y + h] = architect.make_maze(w, h, x, y).tiles


class SettingsHandler(BaseEventHandler):

    # will return a new event handler if we leave settings screen, else self
    def handle_events(self, event: tcod.event.Event) -> "BaseEventHandler":
        action_or_state = self.dispatch(event)
        if isinstance(action_or_state, BaseEventHandler):
            return action_or_state
        return self

    def on_render(self):
        render_functions.render_settings(self.engine)

    def ev_keydown(self, event: tcod.event.KeyDown) -> "BaseEventHandler":
        key = event.sym

        # check settings against hotkeys
        for setting in settings.SETTINGS.values():

            if key == setting.hotkey:
                # increment the matching setting, passing negative parameter as TRUE if a shift key is held
                setting.increment(negative=event.mod & (tcod.event.KMOD_LSHIFT | tcod.event.KMOD_RSHIFT))

        # make the parent handler again on escape key
        # the escape key returns to the parent handler
        if event.sym == tcod.event.K_ESCAPE:
            self.engine.console = tcod.Console(self.engine.game_map.width,
                                               self.engine.game_map.height + MAP_Y_OFFSET,
                                               order='F')
            return MapBuildingHandler(self.engine)
        else:
            return self


class MapInstructionsHandler(BaseEventHandler):

    def handle_events(self, event: tcod.event.Event) -> "BaseEventHandler":
        action_or_state = self.dispatch(event)
        if isinstance(action_or_state, BaseEventHandler):
            return action_or_state
        return self

    def on_render(self):
        render_functions.render_map_instructions(self.engine)

    def ev_keydown(self, event: tcod.event.KeyDown) -> "BaseEventHandler":
        # the escape key returns to the parent handler
        if event.sym == tcod.event.K_ESCAPE:
            self.engine.console = tcod.Console(self.engine.game_map.width, self.engine.game_map.height + MAP_Y_OFFSET,
                                               order='F')
            return MapBuildingHandler(self.engine)
        else:
            return self


class GodBargainHandler(BaseEventHandler):

    def __init__(self, eng: Engine):
        super().__init__(eng)
        self.bargains = [see_through_walls, one_eyed, see_stairs, teleportitis, leave_walls, claustrophobia]

    def handle_events(self, event: tcod.event.Event) -> "BaseEventHandler":

        action_or_state = self.dispatch(event)
        if isinstance(action_or_state, BaseEventHandler):
            return action_or_state
        return self

    def on_render(self):
        self.engine.console.clear()

        render_functions.render_bargains(self.engine, self.bargains)

    def ev_keydown(self, event: tcod.event.KeyDown) -> "BaseEventHandler":
        key = event.sym

        # if a number key is pressed, add the appropriate flag and change player's nu
        if key in NUMBER_KEYS:
            if NUMBER_KEYS[key] < len(self.bargains):
                bargain = self.bargains[NUMBER_KEYS[key]]
                self.engine.player.nu -= bargain.cost

                self.engine.player.flags[bargain.flag] = None if not bargain.val else bargain.val
                if bargain.func:
                    bargain.func(self.engine)

                return PlayerMoverHandler(self.engine)

        elif key == tcod.event.K_ESCAPE:
            return PlayerMoverHandler(self.engine)

        return self


class PlayerMoverHandler(BaseEventHandler):
    def ev_keydown(self, event: tcod.event.KeyDown) -> "BaseEventHandler":
        key = event.sym

        if key in MOVE_KEYS:
            dx, dy = MOVE_KEYS[key]

            self.engine.move_entity(self.engine.player.x + dx, self.engine.player.y + dy, self.engine.player)
            self.engine.end_player_turn()
            if self.engine.player_dead():
                return GameOverEventHandler(self.engine)
            return tick(self)

        elif key == tcod.event.K_SPACE:
            if self.engine.game_map.tiles[self.engine.player.x, self.engine.player.y] == tile_types.down_stairs:
                if self.engine.depth == 3:
                    return WinHandler(self.engine)

                render_functions.render_loading_screen(self.engine)
                self.engine.depth += 1
                self.engine.make_new_game_map()

        elif key == tcod.event.K_RETURN:
            return GodBargainHandler(self.engine)

        elif key == tcod.event.K_m:
            self.engine.console = tcod.Console(self.engine.game_map.width, self.engine.game_map.height + MAP_Y_OFFSET,
                                               order='F')
            self.engine.log.add_message("Press 'P' to return to play")
            return MapBuildingHandler(self.engine)

        elif key == tcod.event.K_s:
            self.engine.game_map.reveal_tiles()
        elif key == tcod.event.K_h:
            self.engine.game_map.hide_tiles()

        elif key == tcod.event.K_ESCAPE:
            raise SystemExit()

        elif key == tcod.event.K_SLASH and (event.mod & (tcod.event.KMOD_LSHIFT | tcod.event.KMOD_RSHIFT)):
            return GameInstructionsHandler(self.engine)

        return self

    def on_render(self):
        self.engine.console.clear()

        self.engine.update_fov()
        render_functions.render_main_screen_player(self.engine)
        render_functions.render_bottom_bar_player(self.engine)


class GameInstructionsHandler(BaseEventHandler):
    def handle_events(self, event: tcod.event.Event) -> "BaseEventHandler":
        action_or_state = self.dispatch(event)
        if isinstance(action_or_state, BaseEventHandler):
            return action_or_state
        return self

    def on_render(self):
        render_functions.render_game_instructions(self.engine)

    def ev_keydown(self, event: tcod.event.KeyDown) -> "BaseEventHandler":
        return PlayerMoverHandler(self.engine)


class GameOverEventHandler(BaseEventHandler):
    def on_render(self):
        render_functions.render_game_over(self.engine)

    def ev_keydown(self, event: tcod.event.KeyDown) -> "BaseEventHandler":
        key = event.sym

        if key in [tcod.event.K_q, tcod.event.K_ESCAPE]:
            raise SystemExit()
        elif key == tcod.event.K_m:
            return MainMenuHandler(self.engine)


class WinHandler(BaseEventHandler):
    def on_render(self):
        render_functions.render_win_screen(self.engine)

    def ev_keydown(self, event: tcod.event.KeyDown):
        key = event.sym

        if key in [tcod.event.K_q, tcod.event.K_ESCAPE]:
            raise SystemExit()


def tick(handler: BaseEventHandler):
    actors = handler.engine.entities_of_type(entity_maker.Actor)
    min_actor = min(actors, key=attrgetter('energy'))
    min_actor_energy = min_actor.energy
    for actor in actors:
        actor.energy = max(0, actor.energy - min_actor_energy)
    return PlayerMoverHandler(handler.engine) if handler.engine.player.energy == 0 else monster_turn(handler, min_actor)


def monster_turn(handler: BaseEventHandler, monster: entity_maker.Monster):
    monster.take_turn()
    return tick(handler)
