# standard imports
import unittest
import tempfile
import shutil
import logging

# local imports
from chainsyncer.session import SyncSession
from chainsyncer.filter import FilterState
from chainsyncer.store.fs import SyncFsStore
from chainsyncer.unittest import (
        MockStore,
        MockFilter,
        )

logging.basicConfig(level=logging.DEBUG)
logg = logging.getLogger()


class TestSync(unittest.TestCase):

    def setUp(self):
        self.path = tempfile.mkdtemp()
        self.store = SyncFsStore(self.path)


    def tearDown(self):
        shutil.rmtree(self.path)


    def test_basic(self):
        store = MockStore(6)
        state = FilterState(store)
        session = SyncSession(state)


    def test_sum(self):
        store = MockStore(6)
        state = FilterState(store)

        b = b'\x2a' * 32
        fltr = MockFilter('foo', z=b)
        state.register(fltr)

        b = b'\x0d' * 31
        fltr = MockFilter('bar', z=b)
        with self.assertRaises(ValueError):
            state.register(fltr)

        b = b'\x0d' * 32
        fltr = MockFilter('bar', z=b)
        state.register(fltr)

        v = state.sum()
        self.assertEqual(v.hex(), 'a24abf9fec112b4e0210ae874b4a371f8657b1ee0d923ad6d974aef90bad8550')


    def test_session_start(self):
        store = MockStore(6)
        state = FilterState(store)
        session = SyncSession(state)
        session.start()
       

    def test_state_dynamic(self):
        store = MockStore()
        state = FilterState(store)

        b = b'\x0d' * 32
        fltr = MockFilter(name='foo', z=b)
        state.register(fltr)


if __name__ == '__main__':
    unittest.main()
