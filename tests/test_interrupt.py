# standard imports
import logging
import unittest
import os

# external imports
from chainlib.chain import ChainSpec
from hexathon import add_0x

# local imports
from chainsyncer.backend.memory import MemBackend
from chainsyncer.driver import HeadSyncer
from chainsyncer.error import NoBlockForYou

# test imports
from tests.base import TestBase

logging.basicConfig(level=logging.DEBUG)
logg = logging.getLogger()


class TestSyncer(HeadSyncer):


    def __init__(self, backend, tx_counts=[]):
        self.tx_counts = tx_counts
        super(TestSyncer, self).__init__(backend)


    def get(self, conn):
        if self.backend.block_height == self.backend.target_block:
            raise NoBlockForYou()
        if self.backend.block_height > len(self.tx_counts):
            return []

        block_txs = []
        for i in range(self.tx_counts[self.backend.block_height]):
            block_txs.append(add_0x(os.urandom(32).hex()))
      
        return block_txs


    def process(self, conn, block):
        i = 0
        for tx in block:
            self.process_single(conn, block, tx, self.backend.block_height, i)
            i += 1



class NaughtyCountExceptionFilter:

    def __init__(self, name, croak_on):
        self.c = 0
        self.croak = croak_on
        self.name = name


    def filter(self, conn, block, tx, db_session=None):
        self.c += 1
        if self.c == self.croak:
            raise RuntimeError('foo')


    def __str__(self):
        return '{} {}'.format(self.__class__.__name__, self.name)


class CountFilter:

    def __init__(self, name):
        self.c = 0
        self.name = name


    def filter(self, conn, block, tx, db_session=None):
        self.c += 1


    def __str__(self):
        return '{} {}'.format(self.__class__.__name__, self.name)


class TestInterrupt(unittest.TestCase):

    def setUp(self):
        self.chain_spec = ChainSpec('foo', 'bar', 42, 'baz')
        self.backend = MemBackend(self.chain_spec, None, target_block=2)
        self.syncer = TestSyncer(self.backend, [4, 2, 3])

    def test_filter_interrupt(self):
       
        fltrs = [
            CountFilter('foo'),
            CountFilter('bar'),
            NaughtyCountExceptionFilter('xyzzy', 2),
            CountFilter('baz'),
                ]

        for fltr in fltrs:
            self.syncer.add_filter(fltr)

        self.syncer.loop(0.1, None)

if __name__ == '__main__':
    unittest.main()
