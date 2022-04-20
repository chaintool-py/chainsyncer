# standard imports
import os
import stat
import unittest
import shutil
import tempfile
import logging

# local imports
from chainsyncer.session import SyncSession
from chainsyncer.error import (
        LockError,
        FilterDone,
        IncompleteFilterError,
        SyncDone,
        )
from chainsyncer.unittest import (
        MockFilter,
        MockItem,
        )

logg = logging.getLogger(__name__)


class TestStoreBase(unittest.TestCase):

    def setUp(self):
        self.path = tempfile.mkdtemp()
        self.store_factory = None


    @classmethod
    def link(cls, target):
        for v in [
                "default",
                "store_start",
                "store_resume",
                "sync_process_nofilter",
                "sync_process_onefilter",
                "sync_process_outoforder",
                "sync_process_interrupt",
                "sync_process_reset",
                "sync_process_done",
                "sync_head_future",
                "sync_history_interrupted",
                "sync_history_complete",
                ]:
            setattr(target, 'test_' + v, getattr(cls, 't_' + v))


    def tearDown(self):
        shutil.rmtree(self.path)


    def t_default(self):
        bogus_item = MockItem(0, 0, 0, 0)
        store = self.store_factory()
        
        fp = os.path.join(self.path, store.session_id)
        session_id = store.session_id
        st = os.stat(fp)
        self.assertTrue(stat.S_ISDIR(st.st_mode))
        self.assertTrue(store.is_default)
        
        fpd = os.path.join(self.path, 'default')
        st = os.stat(fpd)
        self.assertTrue(stat.S_ISDIR(st.st_mode))
        self.assertTrue(store.is_default)

        fpd = os.path.realpath(fpd)
        self.assertEqual(fpd, fp)

        store.stop(bogus_item)
        store = self.store_factory()
        fpr = os.path.join(self.path, session_id)
        self.assertEqual(fp, fpr)
        self.assertTrue(store.is_default)

        store.stop(bogus_item)
        store = self.store_factory('default')
        fpr = os.path.join(self.path, session_id)
        self.assertEqual(fp, fpr)
        self.assertTrue(store.is_default)

        store.stop(bogus_item)
        store = self.store_factory('foo')
        fpf = os.path.join(self.path, 'foo')
        st = os.stat(fpf)
        self.assertTrue(stat.S_ISDIR(st.st_mode))
        self.assertFalse(store.is_default)


    def t_store_start(self):
        bogus_item = MockItem(0, 0, 0, 0)
        store = self.store_factory()
        store.start(42)
        self.assertTrue(store.first)

        store.stop(bogus_item)
        store = self.store_factory()
        store.start()
        self.assertFalse(store.first)


    def t_store_resume(self):
        store = self.store_factory()
        store.start(13)
        self.assertTrue(store.first)
        # todo not done


    def t_sync_process_nofilter(self):
        store = self.store_factory()
        session = SyncSession(store)
        session.start()
        o = session.get(0)
        with self.assertRaises(FilterDone):
            o.advance()


    def t_sync_process_onefilter(self):
        store = self.store_factory()
        session = SyncSession(store)

        fltr_one = MockFilter('foo')
        store.register(fltr_one)

        session.start()
        o = session.get(0)
        o.advance()
        o.release()


    def t_sync_process_outoforder(self):
        store = self.store_factory()
        session = SyncSession(store)

        fltr_one = MockFilter('foo')
        store.register(fltr_one)
        fltr_two = MockFilter('two')
        store.register(fltr_two)

        session.start()
        o = session.get(0)
        o.advance()
        with self.assertRaises(LockError):
            o.advance()

        o.release()
        with self.assertRaises(LockError):
            o.release()

        o.advance()
        o.release()


    def t_sync_process_interrupt(self):
        store = self.store_factory()
        session = SyncSession(store)

        fltr_one = MockFilter('foo')
        store.register(fltr_one)
        fltr_two = MockFilter('bar')
        store.register(fltr_two)

        session.start()
        o = session.get(0)
        o.advance()
        o.release(interrupt=True)
        with self.assertRaises(FilterDone):
            o.advance()


    def t_sync_process_reset(self):
        store = self.store_factory()
        session = SyncSession(store)

        fltr_one = MockFilter('foo')
        store.register(fltr_one)
        fltr_two = MockFilter('bar')
        store.register(fltr_two)

        session.start()
        o = session.get(0)
        o.advance()
        with self.assertRaises(LockError):
            o.reset()
        o.release()
        with self.assertRaises(IncompleteFilterError):
            o.reset()

        o.advance()
        o.release()

        with self.assertRaises(FilterDone):
            o.advance()

        o.reset()

    
    def t_sync_process_done(self):
        store = self.store_factory()
        session = SyncSession(store)

        fltr_one = MockFilter('foo')
        store.register(fltr_one)

        session.start(target=0)
        o = session.get(0)
        o.advance()
        o.release()
        with self.assertRaises(FilterDone):
            o.advance()
        o.reset()
        with self.assertRaises(SyncDone):
            o.next(advance_block=True)


    def t_sync_head_future(self):
        store = self.store_factory('foo')
        session = SyncSession(store)

        session.start()
        o = session.get(0)
        o.next(advance_block=True)
        o.next(advance_block=True)
        session.stop(o)

        store = self.store_factory('foo')
        store.start()
        o = store.get(2)


    def t_sync_history_interrupted(self):
        bogus_item = MockItem(0, 0, 0, 0)
        store = self.store_factory('foo')
        session = SyncSession(store)

        session.start(target=13)
        o = session.get(0)
        o.next(advance_block=True)
        o.next(advance_block=True)
        session.stop(o)

        store.stop(bogus_item)
        store = self.store_factory('foo')
        store.start()
        o = store.get(0)
        self.assertEqual(o.cursor, 2)
        self.assertEqual(o.target, 13) 
        o.next(advance_block=True)
        o.next(advance_block=True)

        store.stop(bogus_item)
        store = self.store_factory('foo')
        store.start()
        self.assertEqual(o.cursor, 4)
        self.assertEqual(o.target, 13) 


    def t_sync_history_complete(self):
        store = self.store_factory('foo')
        session = SyncSession(store)

        session.start(target=3)
        o = session.get(0)
        o.next(advance_block=True)
        o.next(advance_block=True)
        o.next(advance_block=True)
        with self.assertRaises(SyncDone):
            o.next(advance_block=True)
