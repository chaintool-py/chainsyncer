# standard imports
import unittest
import logging

# external imports
from chainlib.chain import ChainSpec

# local imports
from chainsyncer.backend.memory import MemBackend
from chainsyncer.driver.threadrange import (
#        range_to_backends,
        sync_split,
        ThreadPoolRangeHistorySyncer,
        )
from chainsyncer.unittest.base import MockConn

# testutil imports
from tests.chainsyncer_base import TestBase

logging.basicConfig(level=logging.DEBUG)
logg = logging.getLogger()


class TestThreadRange(TestBase):


    def test_range_split_even(self):
        ranges = sync_split(5, 20, 3)
        self.assertEqual(len(ranges), 3)
        self.assertEqual(ranges[0], (5, 9))
        self.assertEqual(ranges[1], (10, 14))
        self.assertEqual(ranges[2], (15, 19))

#    def test_range_split_even(self):
#        chain_spec = ChainSpec('evm', 'bloxberg', 8996, 'foo')
#        backends = range_to_backends(chain_spec, 5, 3, 20, 5, 10, MemBackend, 3)
#        self.assertEqual(len(backends), 3)
#        self.assertEqual(((5, 3), 5), backends[0].start())
#        self.assertEqual((9, 1023), backends[0].target())
#        self.assertEqual(((10, 0), 0), backends[1].start())
#        self.assertEqual((14, 1023), backends[1].target())
#        self.assertEqual(((15, 0), 0), backends[2].start())
#        self.assertEqual((19, 1023), backends[2].target())
#
#
#    def test_range_split_underflow(self):
#        chain_spec = ChainSpec('evm', 'bloxberg', 8996, 'foo')
#        backends = range_to_backends(chain_spec, 5, 3, 7, 5, 10, MemBackend, 3)
#        self.assertEqual(len(backends), 2)
#        self.assertEqual(((5, 3), 5), backends[0].start())
#        self.assertEqual((5, 1023), backends[0].target())
#        self.assertEqual(((6, 0), 0), backends[1].start())
#        self.assertEqual((6, 1023), backends[1].target())


#    def test_range_syncer(self):
#        chain_spec = ChainSpec('evm', 'bloxberg', 8996, 'foo')
#        backends = range_to_backends(chain_spec, 5, 3, 20, 5, 10, MemBackend, 3)
#
#        syncer = ThreadPoolRangeHistorySyncer(MockConn, 3, backends, self.interface)
#        syncer.loop(1, None)
#
    def test_range_syncer(self):
        chain_spec = ChainSpec('evm', 'bloxberg', 8996, 'foo')
        backend = MemBackend.custom(chain_spec, 20, 5, 3, 5, 10)
        syncer = ThreadPoolRangeHistorySyncer(MockConn, 3, backend, self.interface)
        syncer.loop(0.1, None)


if __name__ == '__main__':
    unittest.main()
