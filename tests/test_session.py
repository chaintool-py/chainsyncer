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
        MockDriver,
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
        self.store.register(fltr_one)

        tx_hash = os.urandom(32).hex()
        tx = MockTx(42, tx_hash)
        block = MockBlock(0, [tx_hash])
        session.filter(self.conn, block, tx)
 
        tx_hash = os.urandom(32).hex()
        tx = MockTx(42, tx_hash)
        block = MockBlock(1, [tx_hash])
        session.filter(self.conn, block, tx)
        self.assertEqual(len(fltr_one.contents), 2)


    def test_driver(self):
        drv = MockDriver(self.store, target=1)

        tx_hash = os.urandom(32).hex()
        tx = MockTx(0, tx_hash)
        block = MockBlock(0, [tx_hash])
        drv.add_block(block)

        tx_hash_one = os.urandom(32).hex()
        tx = MockTx(0, tx_hash_one)
        tx_hash_two = os.urandom(32).hex()
        tx = MockTx(1, tx_hash_two)
        block = MockBlock(1, [tx_hash_one, tx_hash_two])
        drv.add_block(block)

        fltr_one = MockFilter('foo')
        self.store.register(fltr_one)
        with self.assertRaises(SyncDone):
            drv.run(self.conn)

        self.assertEqual(len(fltr_one.contents), 3)


if __name__ == '__main__':
    unittest.main()
