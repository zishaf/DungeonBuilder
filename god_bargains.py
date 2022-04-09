class GodBargain:
    def __init__(self, description: str, cost: int, flag: str):
        self.description, self.cost, self.flag = description, cost, flag


see_through_walls = GodBargain("The power to see through walls~~~", 100, 'see_through_walls')
one_eyed = GodBargain("Lose an eye .(", -100, '_one_eyed')
see_stairs = GodBargain("Sense the exit", 100, 'see_stairs')
teleportitis = GodBargain("Randomly teleport", -50, 'teleportitis')
leave_walls = GodBargain("Walls form behind you", -200, 'leave_walls')
