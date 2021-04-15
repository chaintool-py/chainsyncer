# standard imports
import logging
import unittest
import os

# external imports
from chainlib.chain import ChainSpec
from hexathon import add_0x

# local imports
from chainsyncer.backend.memory import MemBackend

# test imports
from tests.base import TestBase
from chainsyncer.unittest.base import (
        MockBlock,
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

        try:
            self.syncer.loop(0.1, None)
        except RuntimeError:
            pass
        self.syncer.loop(0.1, None)

        for fltr in fltrs:
            logg.debug('{} {}'.format(str(fltr), fltr.c))
            self.assertEqual(fltr.c, 9)


if __name__ == '__main__':
    unittest.main()
