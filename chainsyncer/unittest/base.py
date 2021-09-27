# standard imports
import os
import logging

# external imports
from hexathon import add_0x

# local imports
from chainsyncer.driver.history import HistorySyncer
from chainsyncer.error import NoBlockForYou

logg = logging.getLogger().getChild(__name__)


class MockConn:
    """Noop connection mocker.

    :param o: Object to execute rpc call for
    :type o: dict
    """
    def do(self, o):
        pass


class MockTx:
    """Minimal mocked tx object.

    :param index: Transaction index in block
    :type index: int
    :param tx_hash: Transaction hash
    :type tx_hash: str
    """
    def __init__(self, index, tx_hash):
        self.hash = tx_hash
        self.index = index


    def apply_receipt(self, rcpt):
        """Save receipt source in mock tx object.

        :param rcpt: Transaction receipt
        :type rcpt: dict
        """
        self.rcpt = rcpt


class MockBlock:

    def __init__(self, number, txs):
        """Minimal mocked block object.

        :param number: Block number
        :type number: int
        :param txs: Transaction list to include in block
        :type txs: list
        """
        self.number = number
        self.txs = txs


    def tx(self, i):
        """Get block transaction at given index.

        :param i: Transaction index
        :type i: int
        """
        return MockTx(i, self.txs[i])


class TestSyncer(HistorySyncer):
    """Unittest extension of history syncer driver.

    :param backend: Syncer backend
    :type backend: chainsyncer.backend.base.Backend implementation
    :param chain_interface: Chain interface
    :type chain_interface: chainlib.interface.ChainInterface implementation
    :param tx_counts: List of integer values defining how many mock transactions to generate per block. Mock blocks will be generated for each element in list.
    :type tx_counts: list
    """

    def __init__(self, backend, chain_interface, tx_counts=[]):
        self.tx_counts = tx_counts
        super(TestSyncer, self).__init__(backend, chain_interface)


    def get(self, conn):
        """Implements the block getter of chainsyncer.driver.base.Syncer.

        :param conn: RPC connection
        :type conn: chainlib.connection.RPCConnection
        :raises NoBlockForYou: End of mocked block array reached
        :rtype: chainsyncer.unittest.base.MockBlock
        :returns: Mock block.
        """
        (pair, fltr) = self.backend.get()
        (target_block, fltr) = self.backend.target()
        block_height = pair[0]

        if block_height == target_block:
            self.running = False
            raise NoBlockForYou()

        block_txs = []
        if block_height < len(self.tx_counts):
            for i in range(self.tx_counts[block_height]):
                block_txs.append(add_0x(os.urandom(32).hex()))
     
        return MockBlock(block_height, block_txs)
