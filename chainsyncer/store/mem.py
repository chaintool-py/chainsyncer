# standard imports
import logging
import os

# external imports
from shep import State

# local imports 
from chainsyncer.store import SyncStore

logg = logging.getLogger(__name__)


class SyncMemStore(SyncStore):

    def __init__(self, session_id=None, state_event_callback=None, filter_state_event_callback=None):
        super(SyncMemStore, self).__init__(None, session_id=session_id)

        factory = None
        self.setup_sync_state(factory, state_event_callback)

        factory = None
        self.setup_filter_state(factory, filter_state_event_callback)


    def set_target(self, v):
        self.target = int(v)


    def get_target(self):
        return self.target


    def stop(self, item):
        if item != None:
            super(SyncMemStore, self).stop(item)
        logg.info('I am an in-memory only state store. I am shutting down now, so all state will now be discarded.')


    def save_filter_list(self):
        pass


    def load_filter_list(self):
        return []
