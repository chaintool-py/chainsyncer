# standard imports
import logging
import uuid
import os
import unittest
import shutil

# external imports
from chainlib.chain import ChainSpec

# local imports
from chainsyncer.backend_file import SyncerFileBackend

logging.basicConfig(level=logging.DEBUG)
logg = logging.getLogger().getChild(__name__)

script_dir = os.path.dirname(__file__)
tmp_test_dir = os.path.join(script_dir, 'testdata', 'tmp') 
chainsyncer_test_dir = os.path.join(tmp_test_dir, 'chainsyncer')
os.makedirs(tmp_test_dir, exist_ok=True)


class TestFile(unittest.TestCase):

    def setUp(self):
        self.chain_spec = ChainSpec('foo', 'bar', 42, 'baz')
        self.uu = SyncerFileBackend.create_object(self.chain_spec, None, base_dir=tmp_test_dir)
        logg.debug('made uu {} for {}'.format(self.uu, self.chain_spec))

        self.o = SyncerFileBackend(self.chain_spec, self.uu, base_dir=tmp_test_dir)


    def tearDown(self):
        self.o.purge()
        shutil.rmtree(chainsyncer_test_dir)


    @unittest.skip('foo')
    def test_set(self):
        self.o.set(42, 13)

        o = SyncerFileBackend(self.chain_spec, self.o.object_id, base_dir=tmp_test_dir)

        state = o.get()

        self.assertEqual(state[0], 42)
        self.assertEqual(state[1], 13)


    @unittest.skip('foo')
    def test_initial(self):
        local_uu = SyncerFileBackend.initial(self.chain_spec, 1337, start_block_height=666, base_dir=tmp_test_dir)

        o = SyncerFileBackend(self.chain_spec, local_uu, base_dir=tmp_test_dir)

        (pair, filter_stats) = o.target()
        self.assertEqual(pair[0], 1337)
        self.assertEqual(pair[1], 0)

        (pair, filter_stats) = o.start()
        self.assertEqual(pair[0], 666)
        self.assertEqual(pair[1], 0)


    @unittest.skip('foo')
    def test_resume(self):
        for i in range(1, 10):
            local_uu = SyncerFileBackend.initial(self.chain_spec, 666, start_block_height=i, base_dir=tmp_test_dir)

        entries = SyncerFileBackend.resume(self.chain_spec, base_dir=tmp_test_dir)

        self.assertEqual(len(entries), 10)

        last = -1
        for o in entries:
            self.assertLess(last, o.block_height_offset)
            last = o.block_height_offset


    @unittest.skip('foo')
    def test_first(self):
        for i in range(1, 10):
            local_uu = SyncerFileBackend.initial(self.chain_spec, 666, start_block_height=i, base_dir=tmp_test_dir)

        first_entry = SyncerFileBackend.first(self.chain_spec, base_dir=tmp_test_dir)

        self.assertEqual(first_entry.block_height_offset, 9)


    def test_filter(self):
    
        self.assertEqual(len(self.o.filter), 1)

        self.o.register_filter('foo')
        self.o.register_filter('bar')

        o = SyncerFileBackend(self.chain_spec, self.uu, base_dir=tmp_test_dir)

        self.assertEqual(o.filter_count, 2)
        self.assertEqual(o.filter_names, ['foo', 'bar'])
        self.assertEqual(len(o.filter), 1)
        
        self.o.complete_filter(1)
        self.assertEqual(self.o.filter, b'\x40')

        self.o.complete_filter(0)
        self.assertEqual(self.o.filter, b'\xc0')

        o = SyncerFileBackend(self.chain_spec, self.uu, base_dir=tmp_test_dir)
        self.assertEqual(o.filter, b'\xc0')


        with self.assertRaises(IndexError):
            self.o.complete_filter(2)

        self.o.register_filter('baz')
        self.o.complete_filter(2)


if __name__ == '__main__':
    unittest.main()
