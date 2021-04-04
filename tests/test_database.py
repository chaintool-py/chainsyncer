# standard imports
import unittest
import logging

# external imports
from chainlib.chain import ChainSpec

# local imports
from chainsyncer.db.models.base import SessionBase
from chainsyncer.db.models.filter import BlockchainSyncFilter
from chainsyncer.backend import SyncerBackend

# testutil imports
from tests.base import TestBase

logg = logging.getLogger()


class TestDatabase(TestBase):


    def test_backend_live(self):
        s = SyncerBackend.live(self.chain_spec, 42)
        self.assertEqual(s.object_id, 1)
        backend = SyncerBackend.first(self.chain_spec)
        #SyncerBackend(self.chain_spec, sync_id)
        self.assertEqual(backend.object_id, 1)

        bogus_chain_spec = ChainSpec('bogus', 'foo', 13, 'baz')
        sync_id = SyncerBackend.first(bogus_chain_spec)
        self.assertIsNone(sync_id)


    def test_backend_filter(self):
        s = SyncerBackend.live(self.chain_spec, 42)

        s.connect()
        filter_id = s.db_object_filter.id
        s.disconnect()

        session = SessionBase.create_session()
        o = session.query(BlockchainSyncFilter).get(filter_id)
        self.assertEqual(len(o.flags), 0)
        session.close()

        for i in range(9):
            s.register_filter(str(i))

        s.connect()
        filter_id = s.db_object_filter.id
        s.disconnect()

        session = SessionBase.create_session()
        o = session.query(BlockchainSyncFilter).get(filter_id)
        self.assertEqual(len(o.flags), 2)

        (t, c, d) = o.target()
        self.assertEqual(t, (1 << 9) - 1)

        for i in range(9):
            o.set(i)

        (f, c, d) = o.cursor()
        self.assertEqual(f, t)
        self.assertEqual(c, 9)
        self.assertEqual(d, o.digest)

        session.close()

    def test_backend_retrieve(self):
        s = SyncerBackend.live(self.chain_spec, 42)
        s.register_filter('foo')
        s.register_filter('bar')
        s.register_filter('baz')

        s.set(42, 13)

        s = SyncerBackend.first(self.chain_spec)
        self.assertEqual(s.get(), ((42,13), 0))


    def test_backend_initial(self):
        with self.assertRaises(ValueError):
            s = SyncerBackend.initial(self.chain_spec, 42, 42)
        
        with self.assertRaises(ValueError):
            s = SyncerBackend.initial(self.chain_spec, 42, 43)
        
        s = SyncerBackend.initial(self.chain_spec, 42, 13)

        s.set(43, 13)

        s = SyncerBackend.first(self.chain_spec)
        self.assertEqual(s.get(), ((43,13), 0))
        self.assertEqual(s.start(), ((13,0), 0))


    def test_backend_resume(self):
        s = SyncerBackend.resume(self.chain_spec, 666)
        self.assertEqual(len(s), 0)

        s = SyncerBackend.live(self.chain_spec, 42)
        original_id = s.object_id
        s = SyncerBackend.resume(self.chain_spec, 666)
        self.assertEqual(len(s), 1)
        resumed_id = s[0].object_id
        self.assertEqual(resumed_id, original_id + 1)
        self.assertEqual(s[0].get(), ((42, 0), 0))


    def test_backend_resume_when_completed(self):
        s = SyncerBackend.live(self.chain_spec, 42)

        s = SyncerBackend.resume(self.chain_spec, 666)
        s[0].set(666, 0)
    
        s = SyncerBackend.resume(self.chain_spec, 666)
        self.assertEqual(len(s), 0)
        
    
    def test_backend_resume_several(self):
        s = SyncerBackend.live(self.chain_spec, 42)
        s.set(43, 13)
        
        s = SyncerBackend.resume(self.chain_spec, 666)
        SyncerBackend.live(self.chain_spec, 666)
        s[0].set(123, 2)

        s = SyncerBackend.resume(self.chain_spec, 1024)
        SyncerBackend.live(self.chain_spec, 1024) 

        self.assertEqual(len(s), 2)
        self.assertEqual(s[0].target(), (666, 0))
        self.assertEqual(s[0].get(), ((123, 2), 0))
        self.assertEqual(s[1].target(), (1024, 0))
        self.assertEqual(s[1].get(), ((666, 0), 0))


    def test_backend_resume_filter(self):
        s = SyncerBackend.live(self.chain_spec, 42)
        s.register_filter('foo')
        s.register_filter('bar')
        s.register_filter('baz')

        s.set(43, 13)
        s.complete_filter(0)
        s.complete_filter(2)

        s = SyncerBackend.resume(self.chain_spec, 666)
        (pair, flags) = s[0].get()

        self.assertEqual(flags, 5)


if __name__ == '__main__':
    unittest.main()
