# standard imports
import unittest
import tempfile
import shutil
import logging
import stat
import os

# local imports
from chainsyncer.store.fs import SyncFsStore
from chainsyncer.session import SyncSession
from chainsyncer.error import (
        LockError,
        FilterDone,
        IncompleteFilterError,
        SyncDone,
        )
from chainsyncer.unittest import (
        MockFilter,
        MockConn,
        MockTx,
        MockBlock,
        )
from chainsyncer.driver import SyncDriver

logging.basicConfig(level=logging.DEBUG)
logg = logging.getLogger()


class TestFilter(unittest.TestCase):

    def setUp(self):
        self.path = tempfile.mkdtemp()
        self.store = SyncFsStore(self.path)
        self.conn = MockConn()


    def tearDown(self):
        shutil.rmtree(self.path)


    def test_filter_basic(self):
        session = SyncSession(self.store)
        session.start(target=1)
        fltr_one = MockFilter('foo')
        session.register(fltr_one)

        tx_hash = os.urandom(32).hex()
        tx = MockTx(42, tx_hash)
        block = MockBlock(0, [tx_hash])
        session.filter(self.conn, block, tx)
 
        tx_hash = os.urandom(32).hex()
        tx = MockTx(42, tx_hash)
        block = MockBlock(1, [tx_hash])
        with self.assertRaises(SyncDone):
            session.filter(self.conn, block, tx)
        self.assertEqual(len(fltr_one.contents), 2)



    def test_driver(self):
        drv = SyncDriver(self.conn, self.store)
        drv.run()


if __name__ == '__main__':
    unittest.main()
