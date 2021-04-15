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
        (pair, fltr) = self.backend.get()
        (target_block, fltr) = self.backend.target()
        block_height = pair[0]

        if block_height == target_block:
            self.running = False
            raise NoBlockForYou()
            return []

        block_txs = []
        if block_height < len(self.tx_counts):
            for i in range(self.tx_counts[block_height]):
                block_txs.append(add_0x(os.urandom(32).hex()))
     
        return MockBlock(block_height, block_txs)


    # TODO: implement mock conn instead, and use HeadSyncer.process
    def process(self, conn, block):
        i = 0
        for tx in block.txs:
            self.process_single(conn, block, block.tx(i))
            self.backend.reset_filter()
            i += 1
        self.backend.set(block.number + 1, 0)
