# standard imports
import hashlib

class SyncState:

    def __init__(self, state_store):
        self.store = state_store
        self.digest = b'\x00' * 32
        self.summed = False
        self.synced = {}


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
        self.store.add('i_' + s)
        self.store.add('o_' + s)


    def sum(self):
        h = hashlib.sha256()
        h.update(self.digest)
        self.digest = h.digest()
        self.summed = True
        return self.digest


    def start(self):
        for v in self.store.all():
            self.store.sync(v)
            self.synced[v] = True
