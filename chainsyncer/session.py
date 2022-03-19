# standard imports
import uuid

# local imports
from chainsyncer.error import FilterDone


class SyncSession:

    def __init__(self, session_store):
        self.session_store = session_store
        self.started = self.session_store.started
        self.get = self.session_store.get
        self.next = self.session_store.next_item
        self.item = None
        self.filters = self.session_store.filters

    
    def start(self, offset=0, target=-1):
        self.session_store.start(offset=offset, target=target)
        self.item = self.session_store.next_item()
        return self.item


    def stop(self, item):
        self.session_store.stop(item)


    def filter(self, conn, block, tx):
        self.session_store.connect()
        for fltr in self.filters:
            self.item.advance()
            interrupt = fltr.filter(conn, block, tx)
            if not self.item.release(interrupt=interrupt):
                break
        self.item.reset()
        self.next()
        self.session_store.disconnect()
