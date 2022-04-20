# standard imports
import unittest
import tempfile
import shutil
import logging
import stat
import os

# local imports
from chainsyncer.store.rocksdb import SyncRocksDbStore
from chainsyncer.session import SyncSession
from chainsyncer.error import (
        LockError,
        FilterDone,
        IncompleteFilterError,
        SyncDone,
        )
from chainsyncer.unittest import MockFilter

logging.basicConfig(level=logging.DEBUG)
logg = logging.getLogger()


class TestFs(unittest.TestCase):

    def setUp(self):
        self.path = tempfile.mkdtemp()


    def test_default(self):
        store = SyncRocksDbStore(self.path)
        store.start(42)
        self.assertTrue(store.first)


if __name__ == '__main__':
    unittest.main()
