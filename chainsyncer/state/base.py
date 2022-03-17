# standard imports
import hashlib


class SyncState:

    def __init__(self, state_store):
        self.state_store = state_store
        self.digest = b'\x00' * 32
        self.summed = False
        self.__syncs = {}
        self.synced = False
        self.connected = False
        self.state_store.add('INTERRUPT')
        self.state_store.add('LOCK')


    def __verify_sum(self, v):
        if not isinstance(v, bytes) and not isinstance(v, bytearray):
            raise ValueError('argument must be instance of bytes')
        if len(v) != 32:
            raise ValueError('argument must be 32 bytes')


    def register(self, fltr):
        if self.summed:
            raise RuntimeError('filter already applied')
        z = fltr.sum()
        self.__verify_sum(z)
        self.digest += z
        s = fltr.common_name()
        self.state_store.add(s)


    def sum(self):
        h = hashlib.sha256()
        h.update(self.digest)
        self.digest = h.digest()
        self.summed = True
        return self.digest


    def connect(self):
        if not self.synced:
            for v in self.state_store.all():
                self.state_store.sync(v)
                self.__syncs[v] = True
            self.synced = True
        self.connected = True


    def disconnect(self):
        self.connected = False


    def lock(self):
        pass


    def unlock(self):
        pass
