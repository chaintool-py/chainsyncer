# standard imports
import unittest
import logging

# external imports
from chainlib.chain import ChainSpec
from chainlib.eth.unittest.ethtester import EthTesterCase
from chainlib.eth.nonce import RPCNonceOracle
from chainlib.eth.gas import (
        RPCGasOracle,
        Gas,
        )
from chainlib.eth.unittest.base import TestRPCConnection

# local imports
from chainsyncer.backend.memory import MemBackend
from chainsyncer.driver.threadrange import (
        sync_split,
        ThreadPoolRangeHistorySyncer,
        )
from chainsyncer.unittest.base import MockConn
from chainsyncer.unittest.db import ChainSyncerDb

# testutil imports
from tests.chainsyncer_base import (
        EthChainInterface,
        )

logging.basicConfig(level=logging.DEBUG)
logg = logging.getLogger()


class SyncerCounter:

    def __init__(self):
        self.hits = []


    def filter(self, conn, block, tx, db_session=None):
        logg.debug('fltr {} {}'.format(block, tx))
        self.hits.append((block, tx))
       

class TestBaseEth(EthTesterCase):

    interface = EthChainInterface()

    def setUp(self):
        super(TestBaseEth, self).setUp()
        self.db = ChainSyncerDb()
        self.session = self.db.bind_session()

    def tearDown(self):
        self.session.commit()
        self.db.release_session(self.session)
        #os.unlink(self.db_path)


class TestThreadRange(TestBaseEth):

    interface = EthChainInterface()

    def test_range_split_even(self):
        ranges = sync_split(5, 20, 3)
        self.assertEqual(len(ranges), 3)
        self.assertEqual(ranges[0], (5, 9))
        self.assertEqual(ranges[1], (10, 14))
        self.assertEqual(ranges[2], (15, 19))


    def test_range_split_underflow(self):
        ranges = sync_split(5, 8, 4)
        self.assertEqual(len(ranges), 3)
        self.assertEqual(ranges[0], (5, 5))
        self.assertEqual(ranges[1], (6, 6))
        self.assertEqual(ranges[2], (7, 7))


    def test_range_syncer_hello(self):
        #chain_spec = ChainSpec('evm', 'bloxberg', 8996, 'foo')
        chain_spec = ChainSpec('evm', 'foochain', 42)
        backend = MemBackend.custom(chain_spec, 20, 5, 3, 5, 10)
        #syncer = ThreadPoolRangeHistorySyncer(MockConn, 3, backend, self.interface)
        syncer = ThreadPoolRangeHistorySyncer(3, backend, self.interface)
        syncer.loop(0.1, None)


    def test_range_syncer_content(self):
        nonce_oracle = RPCNonceOracle(self.accounts[0], self.rpc)
        gas_oracle = RPCGasOracle(self.rpc)

        self.backend.mine_blocks(10)

        c = Gas(signer=self.signer, nonce_oracle=nonce_oracle, gas_oracle=gas_oracle, chain_spec=self.chain_spec)
        (tx_hash, o) = c.create(self.accounts[0], self.accounts[1], 1024) 
        r = self.rpc.do(o)

        self.backend.mine_blocks(3)

        c = Gas(signer=self.signer, nonce_oracle=nonce_oracle, gas_oracle=gas_oracle, chain_spec=self.chain_spec)
        (tx_hash, o) = c.create(self.accounts[0], self.accounts[1], 2048) 
        r = self.rpc.do(o)

        self.backend.mine_blocks(10)

        backend = MemBackend.custom(self.chain_spec, 20, 5, 3, 5, 10)
        syncer = ThreadPoolRangeHistorySyncer(3, backend, self.interface)
        fltr = SyncerCounter()
        syncer.add_filter(fltr)
        syncer.loop(0.1, None)


if __name__ == '__main__':
    unittest.main()
