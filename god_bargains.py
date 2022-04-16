from engine import Engine


class GodBargain:
    def __init__(self, description: str, cost: int, flag: str, func=None):
        self.description, self.cost, self.flag, self.func = description, cost, flag, func


see_through_walls = GodBargain("The power to see through walls~~~", 100, 'see_through_walls')
one_eyed = GodBargain("Lose an eye .(", -100, 'one_eyed')
see_stairs = GodBargain("Sense the exit", 100, 'see_stairs', Engine.reveal_stairs)
teleportitis = GodBargain("Randomly teleport", -50, 'teleportitis')
leave_walls = GodBargain("Walls form behind you", -200, 'leave_walls')
