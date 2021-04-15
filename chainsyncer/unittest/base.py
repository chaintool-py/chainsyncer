# standard imports
import os
import logging

# external imports
from hexathon import add_0x

# local imports
from chainsyncer.driver import HistorySyncer
from chainsyncer.error import NoBlockForYou

logg = logging.getLogger().getChild(__name__)


class MockTx:

    def __init__(self, index, tx_hash):
        self.hash = tx_hash
        self.index = index


class MockBlock:

    def __init__(self, number, txs):
        self.number = number
        self.txs = txs


    def tx(self, i):
        return MockTx(i, self.txs[i])


class TestSyncer(HistorySyncer):


    def __init__(self, backend, tx_counts=[]):
        self.tx_counts = tx_counts
        super(TestSyncer, self).__init__(backend)


    def get(self, conn):
        if self.backend.block_height == self.backend.target_block:
            self.running = False
            raise NoBlockForYou()
            return []

        block_txs = []
        if self.backend.block_height < len(self.tx_counts):
            for i in range(self.tx_counts[self.backend.block_height]):
                block_txs.append(add_0x(os.urandom(32).hex()))
     
        logg.debug('get tx height {}'.format(self.backend.tx_height))
        
        return MockBlock(self.backend.block_height, block_txs)


    # TODO: implement mock conn instead, and use HeadSyncer.process
    def process(self, conn, block):
        i = 0
        for tx in block.txs:
            self.process_single(conn, block, block.tx(i))
            self.backend.reset_filter()
            i += 1
        self.backend.set(self.backend.block_height + 1, 0)
