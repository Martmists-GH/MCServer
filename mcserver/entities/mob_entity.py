from mcserver.entities.entity_base import Entity


class MobEntity(Entity):
    def __init__(self):
        super().__init__()
        self.head_pitch = 0
        self.metadata = 0

    def pack_metadata(self, bt) -> bytes:
        raise NotImplementedError()
