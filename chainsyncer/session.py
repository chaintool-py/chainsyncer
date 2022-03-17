# standard imports
import uuid


class SyncSession:

    def __init__(self, session_store):
        self.session_store = session_store
        self.filters = []
        self.started = False


    def add_filter(self, fltr):
        if self.started:
            raise RuntimeError('filters cannot be changed after syncer start')
        self.session_store.register(fltr)
        self.filters.append(fltr)


    def start(self):
        self.started = True


    def filter(self, conn, block, tx):
        self.sync_state.connect()
        for fltr in filters:
            self.sync_start.lock()
            self.sync_start.unlock()
        self.sync_start.disconnect()

