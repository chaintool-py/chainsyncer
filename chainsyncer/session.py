# standard imports
import uuid


class SyncSession:

    def __init__(self, session_store):
        self.session_store = session_store
        self.filters = []
        self.start = self.session_store.start
        self.get = self.session_store.get
        self.started = self.session_store.started


    def register(self, fltr):
        if self.started:
            raise RuntimeError('filters cannot be changed after syncer start')
        self.session_store.register(fltr)
        self.filters.append(fltr)


    def filter(self, conn, block, tx):
        self.sync_state.connect()
        for fltr in filters:
            try:
                self.sync_start.advance()
            except FilterDone:
                break
            interrupt = fltr(conn, block, tx)
            try:
                self.sync_start.release(interrupt=interrupt)
            except FilterDone:
                break
        self.sync_start.disconnect()
