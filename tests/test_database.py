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

        t = o.target()
        self.assertEqual(t, (1 << 9) - 1)

        for i in range(9):
            o.set(i)

        c = o.cursor()
        self.assertEqual(c, t)

        session.close()


    def test_backend_resume(self):
        s = SyncerBackend.live(self.chain_spec, 42)
        s.register_filter('foo')
        s.register_filter('bar')
        s.register_filter('baz')

        s.set(42, 13)

        s = SyncerBackend.first(self.chain_spec)
        logg.debug('start {}'.format(s))
        self.assertEqual(s.get(), ((42,13), 0))
        

if __name__ == '__main__':
    unittest.main()
