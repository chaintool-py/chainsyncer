# standard imports
import unittest
import tempfile
import shutil
import logging
import stat
import os

# local imports
from chainsyncer.store.fs import SyncFsStore
from chainsyncer.session import SyncSession
from chainsyncer.error import (
        LockError,
        FilterDone,
        IncompleteFilterError,
        SyncDone,
        )
from chainsyncer.unittest import (
        MockBlockGenerator,
        MockFilter,
        MockConn,
        MockTx,
        MockBlock,
        MockDriver,
        MockFilterError,
        state_event_handler,
        filter_state_event_handler,
        )
from chainsyncer.driver import SyncDriver

logging.basicConfig(level=logging.STATETRACE)
logg = logging.getLogger()


class TestFilter(unittest.TestCase):

    def setUp(self):
        self.path = tempfile.mkdtemp()
        self.store = SyncFsStore(self.path, state_event_callback=state_event_handler, filter_state_event_callback=filter_state_event_handler)
        self.conn = MockConn()


#    def tearDown(self):
#        shutil.rmtree(self.path)


    def test_filter_basic(self):
        session = SyncSession(self.store)
        session.start(target=1)
        fltr_one = MockFilter('foo')
        self.store.register(fltr_one)

        tx_hash = os.urandom(32).hex()
        tx = MockTx(42, tx_hash)
        block = MockBlock(0, [tx_hash])
        session.filter(self.conn, block, tx)
 
        tx_hash = os.urandom(32).hex()
        tx = MockTx(42, tx_hash)
        block = MockBlock(1, [tx_hash])
        session.filter(self.conn, block, tx)
        self.assertEqual(len(fltr_one.contents), 2)


    def test_driver(self):
        drv = MockDriver(self.store, target=1)
        generator = MockBlockGenerator()
        generator.generate([1, 2], driver=drv)

        fltr_one = MockFilter('foo')
        self.store.register(fltr_one)
        with self.assertRaises(SyncDone):
            drv.run(self.conn)

        self.assertEqual(len(fltr_one.contents), 3)


    def test_driver_interrupt_noresume(self):
        drv = MockDriver(self.store, target=1)
        generator = MockBlockGenerator()
        generator.generate([1], driver=drv)

        fltr_one = MockFilter('foo')
        self.store.register(fltr_one)
        fltr_two = MockFilter('bar', brk_hard=1)
        self.store.register(fltr_two)

        with self.assertRaises(MockFilterError):
            drv.run(self.conn)

        self.assertEqual(len(fltr_one.contents), 1)
        self.assertEqual(len(fltr_two.contents), 0)

        store = SyncFsStore(self.path, state_event_callback=state_event_handler, filter_state_event_callback=filter_state_event_handler)
        
        fltr_one = MockFilter('foo') #, brk_hard=1)
        store.register(fltr_one)
        fltr_two = MockFilter('bar')
        store.register(fltr_two)

        with self.assertRaises(LockError):
            drv = MockDriver(store, target=1)

        self.assertEqual(len(fltr_one.contents), 0)
        self.assertEqual(len(fltr_two.contents), 0)


    def test_driver_interrupt_filter(self):
        drv = MockDriver(self.store, target=1)
        generator = MockBlockGenerator()
        generator.generate([1, 1], driver=drv)

        fltr_one = MockFilter('foo')
        self.store.register(fltr_one)
        fltr_two = MockFilter('bar', brk=1)
        self.store.register(fltr_two)
        fltr_three = MockFilter('baz')
        self.store.register(fltr_three)

        store = SyncFsStore(self.path, state_event_callback=state_event_handler, filter_state_event_callback=filter_state_event_handler)

        with self.assertRaises(SyncDone):
            drv.run(self.conn)

        self.assertEqual(len(fltr_one.contents), 2)
        self.assertEqual(len(fltr_two.contents), 2)
        self.assertEqual(len(fltr_three.contents), 1)


    def test_driver_interrupt_sync(self):
        drv = MockDriver(self.store, interrupt_block=1, target=2)
        generator = MockBlockGenerator()
        generator.generate([3, 1, 2], driver=drv)

        fltr_one = MockFilter('foo')
        self.store.register(fltr_one)

        drv.run(self.conn, interval=0.1)

        self.assertEqual(len(fltr_one.contents), 3)

        store = SyncFsStore(self.path, state_event_callback=state_event_handler, filter_state_event_callback=filter_state_event_handler)
        store.register(fltr_one)
        drv = MockDriver(store)
        generator.apply(drv, offset=1)

        with self.assertRaises(SyncDone) as e:
            drv.run(self.conn, interval=0.1)
            self.assertEqual(e, 2)

        self.assertEqual(len(fltr_one.contents), 6)


if __name__ == '__main__':
    unittest.main()
