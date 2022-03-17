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
from chainsyncer.unittest import MockFilter

logging.basicConfig(level=logging.DEBUG)
logg = logging.getLogger()


class TestFs(unittest.TestCase):

    def setUp(self):
        self.path = tempfile.mkdtemp()


    def tearDown(self):
        shutil.rmtree(self.path)


    def test_default(self):
        store = SyncFsStore(self.path)
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

        store = SyncFsStore(self.path)
        fpr = os.path.join(self.path, session_id)
        self.assertEqual(fp, fpr)
        self.assertTrue(store.is_default)

        store = SyncFsStore(self.path, 'default')
        fpr = os.path.join(self.path, session_id)
        self.assertEqual(fp, fpr)
        self.assertTrue(store.is_default)

        store = SyncFsStore(self.path, 'foo')
        fpf = os.path.join(self.path, 'foo')
        st = os.stat(fpf)
        self.assertTrue(stat.S_ISDIR(st.st_mode))
        self.assertFalse(store.is_default)


    def test_store_start(self):
        store = SyncFsStore(self.path)
        store.start(42)
        self.assertTrue(store.first)

        store = SyncFsStore(self.path)
        store.start()
        self.assertFalse(store.first)


    def test_store_resume(self):
        store = SyncFsStore(self.path)
        store.start(13)
        self.assertTrue(store.first)
        # todo not done


    def test_sync_process_nofilter(self):
        store = SyncFsStore(self.path)
        session = SyncSession(store)
        session.start()
        o = session.get(0)
        with self.assertRaises(FilterDone):
            o.advance()


    def test_sync_process_onefilter(self):
        store = SyncFsStore(self.path)
        session = SyncSession(store)

        fltr_one = MockFilter('foo')
        session.register(fltr_one)

        session.start()
        o = session.get(0)
        o.advance()
        o.release()


    def test_sync_process_outoforder(self):
        store = SyncFsStore(self.path)
        session = SyncSession(store)

        fltr_one = MockFilter('foo')
        session.register(fltr_one)
        fltr_two = MockFilter('two')
        session.register(fltr_two)

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


    def test_sync_process_interrupt(self):
        store = SyncFsStore(self.path)
        session = SyncSession(store)

        fltr_one = MockFilter('foo')
        session.register(fltr_one)
        fltr_two = MockFilter('bar')
        session.register(fltr_two)

        session.start()
        o = session.get(0)
        o.advance()
        o.release(interrupt=True)
        with self.assertRaises(FilterDone):
            o.advance()


    def test_sync_process_reset(self):
        store = SyncFsStore(self.path)
        session = SyncSession(store)

        fltr_one = MockFilter('foo')
        session.register(fltr_one)
        fltr_two = MockFilter('bar')
        session.register(fltr_two)

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

    
    def test_sync_process_done(self):
        store = SyncFsStore(self.path)
        session = SyncSession(store)

        fltr_one = MockFilter('foo')
        session.register(fltr_one)

        session.start(target=0)
        o = session.get(0)
        o.advance()
        o.release()
        with self.assertRaises(FilterDone):
            o.advance()
        with self.assertRaises(SyncDone):
            o.reset()


if __name__ == '__main__':
    unittest.main()
