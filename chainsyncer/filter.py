# standard imports
import hashlib
import logging
import re
import os

logg = logging.getLogger(__name__)

re_processedname = r'^_?[A-Z,\.]*$'


class SyncFilter:

    def sum(self):
        s = self.common_name()
        h = hashlib.sha256()
        h.update(s.encode('utf-8'))
        return h.digest()
        

    def filter(self, conn, block, tx):
        raise NotImplementedError()


    def common_name(self):
        s = self.__module__ + '.' + self.__class__.__name__
        return s.replace('.', '_')


# TODO: properly clarify interface shared with syncfsstore, move to filter module?
class FilterState:

    def __init__(self, state_store, scan=None):
        self.state_store = state_store
        self.digest = b'\x00' * 32
        self.summed = False
        self.__syncs = {}
        self.synced = False
        self.connected = False
        self.state_store.add('DONE')
        self.state_store.add('LOCK')
        self.state_store.add('INTERRUPT')
        self.state_store.add('RESET')

        self.state = self.state_store.state
        self.elements = self.state_store.elements
        self.put = self.state_store.put
        self.mask = self.state_store.mask
        self.name = self.state_store.name
        self.set = self.state_store.set
        self.next = self.state_store.next
        self.move = self.state_store.move
        self.unset = self.state_store.unset
        self.peek = self.state_store.peek
        self.from_name = self.state_store.from_name
        self.list = self.state_store.list
        self.state_store.sync()
        self.all = self.state_store.all
        self.started = False

        self.scan = scan


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
        n = self.state_store.from_name(s)
        logg.debug('add filter {} {} {}'.format(s, n, self))


    def sum(self):
        h = hashlib.sha256()
        h.update(self.digest)
        self.digest = h.digest()
        self.summed = True
        return self.digest


    def connect(self):
        if not self.synced:
            for v in self.state_store.all():
                k = self.state_store.from_name(v)
                self.state_store.sync(k)
                self.__syncs[v] = True
            if self.scan != None:
                ks = self.scan()
                for v in ks: #os.listdir(self.scan_path):
                    k = None
                    try:
                        k = self.state_store.from_elements(v)
                        self.state_store.alias(v, k)
                    except ValueError:
                        k = self.state_store.from_name(v)
                    self.state_store.sync(k)
                    self.__syncs[v] = True
            self.synced = True
        self.connected = True


    def disconnect(self):
        self.connected = False


    def start(self, offset=0, target=-1):
        self.state_store.start(offset=offset, target=target)
        self.started = True


    def get(self, k):
        return None


    def next_item(self):
        return None


    def filters(self):
        return []
