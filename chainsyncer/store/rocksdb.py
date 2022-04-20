# standard imports
import uuid
import os
import logging

# external imports
from shep.store.rocksdb import RocksDbStoreFactory

# local imports 
from chainsyncer.store import (
        SyncItem,
        SyncStore,
        )

logg = logging.getLogger(__name__)


class RocksDbStoreAdder:

    def __init__(self, factory, prefix):
        self.factory = factory
        self.prefix = prefix


    def add(self, k):
        path = os.path.join(self.prefix, k)
        return self.factory.add(path)


    def ls(self):
        return self.factory.ls()


class SyncRocksDbStore(SyncStore):

    def __init__(self, base_path, session_id=None, state_event_callback=None, filter_state_event_callback=None):
        super(SyncRocksDbStore, self).__init__(base_path, session_id=session_id)

        self.factory = RocksDbStoreFactory(self.session_path, binary=True)
        prefix_factory = RocksDbStoreAdder(self.factory, 'sync')
        self.setup_sync_state(prefix_factory, state_event_callback)

        prefix_factory = RocksDbStoreAdder(self.factory, 'filter')
        self.setup_filter_state(prefix_factory, filter_state_event_callback)

        self.session_id = os.path.basename(self.session_path)
        logg.info('session id {} resolved {} path {}'.format(session_id, self.session_id, self.session_path))

        self.target_db = RocksDbStoreAdder(self.factory, '.stat').add('target')


    def get_target(self):
        self.target_db.get('target')


    def set_target(self, v):
        self.target_db.put('target')


    def disconnect(self):
        super(SyncRocksDbStore, self).disconnect()
        self.factory.close()