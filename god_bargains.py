from engine import Engine


class GodBargain:
    def __init__(self, description: str, cost: int, flag: str, func=None, val=None):
        self.description, self.cost, self.flag, self.func, self.val = description, cost, flag, func, val


see_through_walls = GodBargain("X-ray vision", 100, 'see_through_walls')
one_eyed = GodBargain("Lose an eye .(", -100, 'one_eyed')
see_stairs = GodBargain("Sense the exit", 100, 'see_stairs', func=Engine.reveal_stairs)
teleportitis = GodBargain("Randomly teleport", -50, 'teleportitis', val=.01)
leave_walls = GodBargain("Walls form behind you", -200, 'leave_walls')
claustrophobia = GodBargain("You imagine walls around you", -100, 'claustrophobia', func=Engine.init_claustrophobia,
                            val=[0, []])
