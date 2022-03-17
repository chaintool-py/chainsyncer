# standard imports
import unittest
import tempfile
import shutil
import logging
import stat
import os

# local imports
from chainsyncer.store.fs import SyncFsStore

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



if __name__ == '__main__':
    unittest.main()
