# standard imports
import unittest
import logging

# external imports
from shep import State

# local imports
from chainsyncer.store.mem import SyncMemStore
from chainsyncer.unittest.store import TestStoreBase

logging.basicConfig(level=logging.DEBUG)
logg = logging.getLogger()


class StoreFactory:

    def create(self, session_id=None):
        return SyncMemStore(session_id=session_id)


class TestMem(TestStoreBase):

    def setUp(self):
        super(TestMem, self).setUp()
        self.store_factory = StoreFactory().create
        self.persist = False


if __name__ == '__main__':
    TestStoreBase.link(TestMem)
    # Remove tests that test persistence of state
    unittest.main()
