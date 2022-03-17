# standard imports
import uuid


class SyncSession:

    def __init__(self, session_store, sync_state, session_id=None, is_default=False):
        self.session_store = session_store
        if session_id == None:
            session_id = str(uuid.uuid4())
            is_default = True
        self.session_id = session_id
        self.is_default = is_default
        self.sync_state = sync_state
        self.filters = []
        self.started = False


    def add_filter(self, fltr):
        if self.started:
            raise RuntimeError('filters cannot be changed after syncer start')
        self.sync_state.register(fltr)
        self.filters.append(fltr)


    def start(self):
        self.started = True


    def filter(self, conn, block, tx):
        self.sync_state.connect()
        for fltr in filters:
            self.sync_start.lock()
            self.sync_start.unlock()
        self.sync_start.disconnect()

