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
        MockFilterError,
        state_event_handler,
        filter_state_event_handler,
        )


logging.basicConfig(level=logging.STATETRACE)
logg = logging.getLogger()



class TestFilter(unittest.TestCase):

    def setUp(self):
        self.path = tempfile.mkdtemp()
        self.store = SyncFsStore(self.path, state_event_callback=state_event_handler, filter_state_event_callback=filter_state_event_handler)
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


    def test_filter_resume_single_revert(self):
        fltr_one = MockFilter('foo', brk_hard=True)
        self.store.register(fltr_one)

        self.session.start()

        item = self.store.get('0')
        item.next()

        tx_hash = os.urandom(32).hex()
        tx = MockTx(42, tx_hash)
        block = MockBlock(13, [tx_hash])

        with self.assertRaises(MockFilterError):
            self.session.filter(self.conn, block, tx)
      
        # Unlock the state, reverting to previous filter
        store = SyncFsStore(self.path, state_event_callback=state_event_handler, filter_state_event_callback=filter_state_event_handler)
        self.conn = MockConn()
        fltr_one = MockFilter('foo')
        store.register(fltr_one)
        store.connect()
        store.start(ignore_lock=True)
        store.unlock_filter(revert=True)

        store = SyncFsStore(self.path, state_event_callback=state_event_handler, filter_state_event_callback=filter_state_event_handler)
        session = SyncSession(store)
        self.conn = MockConn()

        fltr_one = MockFilter('foo')
        store.register(fltr_one)

        session.start()

        session.filter(self.conn, block, tx)



    def test_filter_resume_single_continue(self):
        fltr_one = MockFilter('foo', brk_hard=True)
        self.store.register(fltr_one)

        self.session.start()

        item = self.store.get('0')
        item.next()

        tx_hash = os.urandom(32).hex()
        tx = MockTx(42, tx_hash)
        block = MockBlock(13, [tx_hash])

        with self.assertRaises(MockFilterError):
            self.session.filter(self.conn, block, tx)
      
        # Unlock the state, reverting to previous filter
        store = SyncFsStore(self.path, state_event_callback=state_event_handler, filter_state_event_callback=filter_state_event_handler)
        self.conn = MockConn()
        fltr_one = MockFilter('foo')
        store.register(fltr_one)
        store.connect()
        store.start(ignore_lock=True)
        store.unlock_filter(revert=False)

        store = SyncFsStore(self.path, state_event_callback=state_event_handler, filter_state_event_callback=filter_state_event_handler)
        session = SyncSession(store)
        self.conn = MockConn()

        fltr_one = MockFilter('foo')
        store.register(fltr_one)
        store.connect()

        session.start()

        session.filter(self.conn, block, tx)



    def test_filter_resume_multi_revert_last(self):
        fltr_one = MockFilter('foo')
        self.store.register(fltr_one)

        fltr_two = MockFilter('bar', brk_hard=True)
        self.store.register(fltr_two)

        self.session.start()

        item = self.store.get('0')
        item.next()

        tx_hash = os.urandom(32).hex()
        tx = MockTx(42, tx_hash)
        block = MockBlock(13, [tx_hash])

        with self.assertRaises(MockFilterError):
            self.session.filter(self.conn, block, tx)
      
        # Unlock the state, reverting to previous filter
        store = SyncFsStore(self.path, state_event_callback=state_event_handler, filter_state_event_callback=filter_state_event_handler)
        self.conn = MockConn()
        fltr_one = MockFilter('foo')
        store.register(fltr_one)
        fltr_bar = MockFilter('bar')
        store.register(fltr_bar)
        store.connect()
        store.start(ignore_lock=True)
        store.unlock_filter(revert=True)

        store = SyncFsStore(self.path, state_event_callback=state_event_handler, filter_state_event_callback=filter_state_event_handler)
        session = SyncSession(store)
        self.conn = MockConn()

        fltr_one = MockFilter('foo')
        store.register(fltr_one)
        fltr_two = MockFilter('bar')
        store.register(fltr_two)

        store.connect()

        session.start()

        session.filter(self.conn, block, tx)


    def test_filter_resume_multi_continue_last(self):
        fltr_one = MockFilter('foo')
        self.store.register(fltr_one)

        fltr_two = MockFilter('bar', brk_hard=True)
        self.store.register(fltr_two)

        self.session.start()

        item = self.store.get('0')
        item.next()

        tx_hash = os.urandom(32).hex()
        tx = MockTx(42, tx_hash)
        block = MockBlock(13, [tx_hash])

        with self.assertRaises(MockFilterError):
            self.session.filter(self.conn, block, tx)
      
        # Unlock the state, reverting to previous filter
        store = SyncFsStore(self.path, state_event_callback=state_event_handler, filter_state_event_callback=filter_state_event_handler)
        self.conn = MockConn()
        fltr_one = MockFilter('foo')
        store.register(fltr_one)
        fltr_bar = MockFilter('bar')
        store.register(fltr_bar)
        store.connect()
        store.start(ignore_lock=True)
        store.unlock_filter(revert=False)

        store = SyncFsStore(self.path, state_event_callback=state_event_handler, filter_state_event_callback=filter_state_event_handler)
        session = SyncSession(store)
        self.conn = MockConn()

        fltr_one = MockFilter('foo')
        store.register(fltr_one)
        fltr_two = MockFilter('bar')
        store.register(fltr_two)

        session.start()

        session.filter(self.conn, block, tx)


    def test_filter_resume_multi_revert_middle(self):
        fltr_one = MockFilter('foo')
        self.store.register(fltr_one)

        fltr_two = MockFilter('bar', brk_hard=True)
        self.store.register(fltr_two)

        fltr_three = MockFilter('baz')
        self.store.register(fltr_three)

        self.session.start()

        item = self.store.get('0')
        item.next()

        tx_hash = os.urandom(32).hex()
        tx = MockTx(42, tx_hash)
        block = MockBlock(13, [tx_hash])

        with self.assertRaises(MockFilterError):
            self.session.filter(self.conn, block, tx)
      
        # Unlock the state, reverting to previous filter
        store = SyncFsStore(self.path, state_event_callback=state_event_handler, filter_state_event_callback=filter_state_event_handler)
        self.conn = MockConn()
        fltr_one = MockFilter('foo')
        store.register(fltr_one)
        fltr_two = MockFilter('bar')
        store.register(fltr_two)
        fltr_three = MockFilter('baz')
        store.register(fltr_three)

        store.connect()
        store.start(ignore_lock=True)
        store.unlock_filter(revert=True)

        store = SyncFsStore(self.path, state_event_callback=state_event_handler, filter_state_event_callback=filter_state_event_handler)
        session = SyncSession(store)
        self.conn = MockConn()

        fltr_one = MockFilter('foo')
        store.register(fltr_one)
        fltr_two = MockFilter('bar')
        store.register(fltr_two)
        fltr_three = MockFilter('baz')
        store.register(fltr_three)

        store.connect()

        session.start()

        session.filter(self.conn, block, tx)


    def test_filter_resume_multi_continue_middle(self):
        fltr_one = MockFilter('foo')
        self.store.register(fltr_one)

        fltr_two = MockFilter('bar', brk_hard=True)
        self.store.register(fltr_two)

        fltr_three = MockFilter('baz')
        self.store.register(fltr_three)

        self.session.start()

        item = self.store.get('0')
        item.next()

        tx_hash = os.urandom(32).hex()
        tx = MockTx(42, tx_hash)
        block = MockBlock(13, [tx_hash])

        with self.assertRaises(MockFilterError):
            self.session.filter(self.conn, block, tx)
      
        # Unlock the state, reverting to previous filter
        store = SyncFsStore(self.path, state_event_callback=state_event_handler, filter_state_event_callback=filter_state_event_handler)
        self.conn = MockConn()
        fltr_one = MockFilter('foo')
        store.register(fltr_one)
        fltr_two = MockFilter('bar')
        store.register(fltr_two)
        fltr_three = MockFilter('baz')
        store.register(fltr_three)

        store.connect()
        store.start(ignore_lock=True)
        store.unlock_filter(revert=False)

        store = SyncFsStore(self.path, state_event_callback=state_event_handler, filter_state_event_callback=filter_state_event_handler)
        session = SyncSession(store)
        self.conn = MockConn()

        fltr_one = MockFilter('foo')
        store.register(fltr_one)
        fltr_two = MockFilter('bar')
        store.register(fltr_two)
        fltr_three = MockFilter('baz')
        store.register(fltr_three)

        session.start()

        session.filter(self.conn, block, tx)


if __name__ == '__main__':
    unittest.main()

