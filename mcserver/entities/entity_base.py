from uuid import uuid4

import numpy as np

from mcserver.messager import Messager
from rewrite.utils import get_free_id


class Entity:
    def __init__(self):
        self.ent_id: int = next(get_free_id())
        self.position = np.array([0, 100, 0])
        self.velocity = np.array([0, 0, 0])
        self.rotation = np.array([0, 0])
        self.on_ground = False
        self.health = 0
        self.max_health = 0
        self.type_ = 1
        self.data = 0
        self.uuid = uuid4()

    def moved(self, new_pos: np.ndarray, on_ground: bool):
        diff = (new_pos*32 - self.position*32)*128
        self.position = new_pos
        self.on_ground = on_ground
        Messager.send_entity_moved(self, diff, on_ground)
