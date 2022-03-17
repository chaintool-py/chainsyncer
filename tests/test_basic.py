# standard imports
import unittest
import hashlib
import tempfile
import shutil
import logging

# external imports
from shep.state import State

# local imports
from chainsyncer.session import SyncSession
from chainsyncer.state import SyncState
from chainsyncer.store.fs import SyncFsStore

logging.basicConfig(level=logging.DEBUG)
logg = logging.getLogger()

class MockStore(State):

    def __init__(self, bits=0):
        super(MockStore, self).__init__(bits, check_alias=False) 


class MockFilter:

    def __init__(self, name, brk=False, z=None):
        self.name = name
        if z == None:
            h = hashlib.sha256()
            h.update(self.name.encode('utf-8'))
            z = h.digest()
        self.z = z
        self.brk = brk


    def sum(self):
        return self.z


    def common_name(self):
        return self.name 


    def filter(self, conn, block, tx):
        return self.brk


class TestSync(unittest.TestCase):

    def setUp(self):
        self.path = tempfile.mkdtemp()
        self.store = SyncFsStore(self.path)


    def tearDown(self):
        shutil.rmtree(self.path)


    def test_basic(self):
        store = MockStore(6)
        state = SyncState(store)
        session = SyncSession(state)


    def test_sum(self):
        store = MockStore(4)
        state = SyncState(store)

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
        state = SyncState(store)
        session = SyncSession(state)
        session.start()
       

    def test_state_dynamic(self):
        store = MockStore()
        state = SyncState(store)

        b = b'\x0d' * 32
        fltr = MockFilter(name='foo', z=b)
        state.register(fltr)


if __name__ == '__main__':
    unittest.main()
