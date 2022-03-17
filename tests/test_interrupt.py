# standard imports
import logging
import unittest
import os
import tempfile

# external imports
from chainlib.chain import ChainSpec

# local imports
from chainsyncer.backend.memory import MemBackend
from chainsyncer.backend.sql import SQLBackend
from chainsyncer.backend.file import (
        FileBackend,
        data_dir_for,
    )
from chainsyncer.error import LockError

# test imports
from tests.chainsyncer_base import TestBase
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
        self.c += 1
        if self.c == self.croak:
            self.croak = -1
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



class TestInterrupt(TestBase):

    def setUp(self):
        super(TestInterrupt, self).setUp()
        
        self.backend = None
        self.conn = MockConn()
        self.vectors = [
                [4, 3, 2],
                [6, 4, 2],
                [6, 5, 2],
                [6, 4, 3],
                ]
        self.track_complete = True
        

    def assert_filter_interrupt(self, vector, chain_interface):
    
        logg.debug('running vector {} {}'.format(str(self.backend), vector))

        z = 0
        for v in vector:
            z += v

        syncer = TestSyncer(self.backend, chain_interface, vector)

        filters =  [
            CountFilter('foo'),
            CountFilter('bar'),
            NaughtyCountExceptionFilter('xyzzy', croak_on=3),
            CountFilter('baz'),
            ]

        for fltr in filters:
            syncer.add_filter(fltr)

        try:
            syncer.loop(0.1, self.conn)
        except RuntimeError:
            self.croaked = 2
            logg.info('caught croak')
            pass
        (pair, fltr) = self.backend.get()
        self.assertGreater(fltr, 0)

        try:
            syncer.loop(0.1, self.conn)
        except LockError:
            self.backend.complete_filter(2)
            syncer.loop(0.1, self.conn)

        for fltr in filters:
            logg.debug('{} {}'.format(str(fltr), fltr.c))
            self.assertEqual(fltr.c, z)


    def test_filter_interrupt_memory(self):
        self.track_complete = True
        for vector in self.vectors:
            self.backend = MemBackend.custom(self.chain_spec, target_block=len(vector))
            self.assert_filter_interrupt(vector, self.interface)

    #TODO: implement flag lock in file backend
    @unittest.expectedFailure
    def test_filter_interrupt_file(self):
        #for vector in self.vectors:
            vector = self.vectors.pop()
            d = tempfile.mkdtemp()
            #os.makedirs(data_dir_for(self.chain_spec, 'foo', d))
            self.backend = FileBackend.initial(self.chain_spec, len(vector), base_dir=d) #'foo', base_dir=d)
            self.assert_filter_interrupt(vector, self.interface)


    def test_filter_interrupt_sql(self):
        self.track_complete = True
        for vector in self.vectors:
            self.backend = SQLBackend.initial(self.chain_spec, len(vector))
            self.assert_filter_interrupt(vector, self.interface)


if __name__ == '__main__':
    unittest.main()
