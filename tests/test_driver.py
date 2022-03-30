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
        MockChainInterfaceConn,
        MockTx,
        MockBlock,
        MockChainInterface,
        MockFilterError,
        )
from chainsyncer.driver.chain_interface import ChainInterfaceDriver

logging.basicConfig(level=logging.DEBUG)
logg = logging.getLogger()


class TestFilter(unittest.TestCase):

    def setUp(self):
        self.path = tempfile.mkdtemp()
        self.store = SyncFsStore(self.path)
        self.ifc = MockChainInterface()
        self.conn = MockChainInterfaceConn(self.ifc)


    def tearDown(self):
        shutil.rmtree(self.path)


    def test_driver(self):
        generator = MockBlockGenerator()
        generator.generate([1, 2], driver=self.conn)

        drv = ChainInterfaceDriver(self.store, self.ifc, target=1)

        fltr_one = MockFilter('foo')
        self.store.register(fltr_one)
        with self.assertRaises(SyncDone):
            drv.run(self.conn)

        self.assertEqual(len(fltr_one.contents), 3)


if __name__ == '__main__':
    unittest.main()
