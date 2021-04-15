# standard imports
import logging
import unittest
import os

# external imports
from chainlib.chain import ChainSpec

# local imports
from chainsyncer.backend.memory import MemBackend
from chainsyncer.backend.sql import SyncerBackend

# test imports
from tests.base import TestBase
from chainsyncer.unittest.base import (
        MockBlock,
        MockConn,
        TestSyncer,
        )

logging.basicConfig(level=logging.DEBUG)
logg = logging.getLogger()


class NaughtyCountExceptionFilter:

    def __init__(self, name, croak_on):
        self.c = 0
        self.croak = croak_on
        self.name = name


    def filter(self, conn, block, tx, db_session=None):
        if self.c == self.croak:
            self.croak = -1
            raise RuntimeError('foo')
        self.c += 1


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



class TestInterrupt(TestBase):

    def setUp(self):
        super(TestInterrupt, self).setUp()
        self.filters =  [
            CountFilter('foo'),
            CountFilter('bar'),
            NaughtyCountExceptionFilter('xyzzy', croak_on=3),
            CountFilter('baz'),
            ]
        self.backend = None
        self.conn = MockConn()
        

    def assert_filter_interrupt(self):
       
        syncer = TestSyncer(self.backend, [4, 3, 2])

        for fltr in self.filters:
            syncer.add_filter(fltr)

        try:
            syncer.loop(0.1, self.conn)
        except RuntimeError:
            logg.info('caught croak')
            pass
        (pair, fltr) = self.backend.get()
        self.assertGreater(fltr, 0)
        syncer.loop(0.1, self.conn)

        for fltr in self.filters:
            logg.debug('{} {}'.format(str(fltr), fltr.c))
            self.assertEqual(fltr.c, 9)


    def test_filter_interrupt_memory(self):
        self.backend = MemBackend(self.chain_spec, None, target_block=4)
        self.assert_filter_interrupt()


    def test_filter_interrupt_sql(self):
        self.backend = SyncerBackend.initial(self.chain_spec, 4)
        self.assert_filter_interrupt()


if __name__ == '__main__':
    unittest.main()
