# standard imporst
import unittest

# external imports
from shep import State

# local imports
from chainsyncer.state import SyncState
from chainsyncer.session import SyncSession


class MockStore(State):

    def __init__(self, bits):
        super(MockStore, self).__init__(bits, check_alias=False) 


class MockFilter:

    def __init__(self, z, name):
        self.z = z
        self.name = name


    def sum(self):
        return self.z


    def common_name(self):
        return self.name 


class TestSync(unittest.TestCase):

    def setUp(self):
        self.store = MockStore(6)
        self.state = SyncState(self.store)


    def test_basic(self):
        session = SyncSession(self.state)
        self.assertTrue(session.is_default)
        
        session = SyncSession(self.state, session_id='foo')
        self.assertFalse(session.is_default)


    def test_sum(self):
        b = b'\x2a' * 32
        fltr = MockFilter(b, name='foo')
        self.state.register(fltr)

        b = b'\x0d' * 31
        fltr = MockFilter(b, name='bar')
        with self.assertRaises(ValueError):
            self.state.register(fltr)

        b = b'\x0d' * 32
        fltr = MockFilter(b, name='bar')
        self.state.register(fltr)

        v = self.state.sum()
        self.assertEqual(v.hex(), 'a24abf9fec112b4e0210ae874b4a371f8657b1ee0d923ad6d974aef90bad8550')


    def test_session_start(self):
        session = SyncSession(self.state)
        session.start()
        

if __name__ == '__main__':
    unittest.main()
