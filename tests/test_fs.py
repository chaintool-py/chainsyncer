# standard imports
import unittest
import logging

# local imports
from chainsyncer.store.fs import SyncFsStore
from chainsyncer.unittest.store import TestStoreBase

logging.basicConfig(level=logging.DEBUG)
logg = logging.getLogger()


class StoreFactory:

    def __init__(self, path):
        self.path = path


    def create(self, session_id=None):
        return SyncFsStore(self.path, session_id=session_id)


class TestFs(TestStoreBase):

    def setUp(self):
        super(TestFs, self).setUp()
        self.store_factory = StoreFactory(self.path).create


if __name__ == '__main__':
    TestStoreBase.link(TestFs)
    unittest.main()
