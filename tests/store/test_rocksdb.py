# standard imports
import unittest
import logging

# local imports
from chainsyncer.store.rocksdb import SyncRocksDbStore
from chainsyncer.unittest.store import (
        TestStoreBase,
        filter_change_callback,
        state_change_callback,
        )

logging.basicConfig(level=logging.DEBUG)
logg = logging.getLogger()

class StoreFactory:

    def __init__(self, path):
        self.path = path


    def create(self, session_id=None):
        return SyncRocksDbStore(self.path, session_id=session_id, state_event_callback=state_change_callback, filter_state_event_callback=filter_change_callback)


class TestRocksDb(TestStoreBase):

    def setUp(self):
        super(TestRocksDb, self).setUp()
        self.store_factory = StoreFactory(self.path).create


if __name__ == '__main__':
    TestStoreBase.link(TestRocksDb)
    unittest.main()
