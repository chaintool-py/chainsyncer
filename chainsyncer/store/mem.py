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
        super(SyncMemStore, self).__init__('/dev/null', session_id=session_id)

        self.session_id = os.path.basename(self.session_path)
        logg.info('session id {} resolved {} path {}'.format(session_id, self.session_id, self.session_path))

        factory = None
        self.setup_sync_state(factory, state_event_callback)

        factory = None
        self.setup_filter_state(factory, filter_state_event_callback)


    def set_target(self, v):
        self.target = int(v)


    def get_target(self):
        return self.target
