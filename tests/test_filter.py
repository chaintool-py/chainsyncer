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
        )
from chainsyncer.unittest import (
        MockFilter,
        MockConn,
        MockTx,
        MockBlock,
        )

logging.basicConfig(level=logging.DEBUG)
logg = logging.getLogger()


class TestFilter(unittest.TestCase):

    def setUp(self):
        self.path = tempfile.mkdtemp()
        self.store = SyncFsStore(self.path)
        self.session = SyncSession(self.store)
        self.conn = MockConn()


    def tearDown(self):
        shutil.rmtree(self.path)


    def test_filter_basic(self):
        fltr_one = MockFilter('foo')
        self.store.register(fltr_one)
        fltr_two = MockFilter('bar')
        self.store.register(fltr_two)

        self.session.start()

        tx_hash = os.urandom(32).hex()
        tx = MockTx(42, tx_hash)
        block = MockBlock(13, [tx_hash])
        self.session.filter(self.conn, block, tx)
        
        self.assertEqual(len(fltr_one.contents), 1)
        self.assertEqual(len(fltr_two.contents), 1)
        


    def test_filter_interrupt(self):
        fltr_one = MockFilter('foo', brk=True)
        self.store.register(fltr_one)
        fltr_two = MockFilter('bar')
        self.store.register(fltr_two)

        self.session.start()

        tx_hash = os.urandom(32).hex()
        tx = MockTx(42, tx_hash)
        block = MockBlock(13, [tx_hash])
        self.session.filter(self.conn, block, tx)
        
        self.assertEqual(len(fltr_one.contents), 1)
        self.assertEqual(len(fltr_two.contents), 0)


if __name__ == '__main__':
    unittest.main()

