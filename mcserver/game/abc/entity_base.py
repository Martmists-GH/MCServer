# Stdlib
from abc import ABC

# External Libraries
import numpy as np

# MCServer
from mcserver.utils.misc import get_free_id


class Spawnable(ABC):
    def __init__(self):
        self.id = next(get_free_id())
        self.position = np.array([0, 0, 0])
        self.dimension = 0


class Look:
    def __init__(self, xyz: list = (0, 0, 0), pitchyaw: list = (0, 0), relative=0):
        self.xyz = np.array([*xyz])  # Dumb var names will probably change dunno what else atm though
        self.pitchyaw = np.array([*pitchyaw])
        self.relative = relative


class EntityBase(Spawnable):
    def __init__(self):
        super().__init__()
        self.rotation = np.array([0, 0])
        self.look = Look()
        self.metadata = {}
        self.flags = 0

    def __repr__(self):
        return f"{self.__class__.__name__}(position={self.position}, rotation={self.rotation})"
