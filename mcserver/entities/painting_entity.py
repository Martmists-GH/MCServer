import numpy as np

from mcserver.entities.entity_base import Entity


class PaintingEntity(Entity):
    def __init__(self):
        super().__init__()
        self.motive = 0
        self.direction = 0

    def calculate_position(self):
        if self.motive <= 6:
            width = height = 1
        elif self.motive <= 11:
            width = 2
            height = 1
        elif self.motive <= 13:
            width = 1
            height = 2
        elif self.motive <= 19:
            width = height = 2
        elif self.motive == 20:
            width = 4
            height = 2
        elif self.motive <= 23:
            width = height = 4
        else:
            width = 4
            height = 3

        self.position = np.array([max(0, width // 2 - 1), height // 2])
