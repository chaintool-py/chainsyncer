# standard imports
import logging

# external imports
from chainlib.eth.tx import (
        transaction,
        Tx,
        )
from chainlib.error import RPCException

# local imports
from chainsyncer.error import NoBlockForYou
from .poll import BlockPollSyncer

logg = logging.getLogger(__name__)

class HeadSyncer(BlockPollSyncer):
    """Extends the block poller, implementing an open-ended syncer.
    """

    name = 'head'

    def process(self, conn, block):
        """Process a single block using the given RPC connection.

        Processing means that all filters are executed on all transactions in the block.

        If the block object does not contain the transaction details, the details will be retrieved from the network (incurring the corresponding performance penalty).

        :param conn: RPC connection
        :type conn: chainlib.connection.RPCConnection
        :param block: Block object
        :type block: chainlib.block.Block
        """
        (pair, fltr) = self.backend.get()
        logg.debug('process block {} (backend {}:{})'.format(block, pair, fltr))
        i = pair[1] # set tx index from previous
        tx_src = None
        while True:
            # handle block objects regardless of whether the tx data is embedded or not
            try:
                tx = block.tx(i)
            except AttributeError:
                o = transaction(block.txs[i])
                r = conn.do(o)
                tx_src = Tx.src_normalize(r)
                tx = self.chain_interface.tx_from_src(tx_src, block=block)


            #except IndexError as e:
            #    logg.debug('index error syncer tx get {}'.format(e))
            #    break

            rcpt = conn.do(self.chain_interface.tx_receipt(tx.hash))
            if rcpt != None:
                tx.apply_receipt(self.chain_interface.src_normalize(rcpt))

            self.process_single(conn, block, tx)
            self.backend.reset_filter()
                        
            i += 1
        

    def get(self, conn):
        """Retrieve the block currently defined by the syncer cursor from the RPC provider.

        :param conn: RPC connection
        :type conn: chainlib.connectin.RPCConnection
        :raises NoBlockForYou: Block at the given height does not exist
        :rtype: chainlib.block.Block
        :returns: Block object
        """
        (height, flags) = self.backend.get()
        block_number = height[0]
        block_hash = []
        o = self.chain_interface.block_by_number(block_number)
        try:
            r = conn.do(o)
        except RPCException:
            r = None
        if r == None:
            raise NoBlockForYou()
        b = self.chain_interface.block_from_src(r)
        b.txs = b.txs[height[1]:]

        return b
