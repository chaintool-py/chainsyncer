# standard imports
import uuid


class SyncSession:

    def __init__(self, state_store, session_id=None, is_default=False):
        if session_id == None:
            session_id = str(uuid.uuid4())
            is_default = True
        self.session_id = session_id
        self.is_default = is_default
        self.state_store = state_store
        self.filters = []


    def add_filter(self, fltr):
        self.state_store.register(fltr)
        self.filters.append(fltr)


    def start(self):
        self.state_store.start()
