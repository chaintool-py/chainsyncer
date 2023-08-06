# standard imports
import logging

# external imports
from chainlib.error import RPCException

# local imports
from chainsyncer.error import NoBlockForYou
from chainsyncer.driver import SyncDriver

logg = logging.getLogger(__name__)


class ChainInterfaceDriver(SyncDriver):

    def __init__(self, store, chain_interface, offset=0, target=-1, pre_callback=None, post_callback=None, block_callback=None, idle_callback=None):
        super(ChainInterfaceDriver, self).__init__(store, offset=offset, target=target, pre_callback=pre_callback, post_callback=post_callback, block_callback=block_callback, idle_callback=idle_callback)
        self.chain_interface = chain_interface


    def get(self, conn, item):
        """Retrieve the block currently defined by the syncer cursor from the RPC provider.

        :param conn: RPC connection
        :type conn: chainlib.connectin.RPCConnection
        :raises NoBlockForYou: Block at the given height does not exist
        :rtype: chainlib.block.Block
        :returns: Block object
        """
        o = self.chain_interface.block_by_number(item.cursor)
        try:
            r = conn.do(o)
        except RPCException:
            r = None
        if r == None:
            raise NoBlockForYou()
        b = self.chain_interface.block_from_src(r)
        b.txs = b.txs[item.tx_cursor:]

        return b


    def merge_rcpts_single(self, conn, txs):
        i = 0
        c = len(txs)
        for j in range(c):
            hsh = txs[j].hash
            o = self.chain_interface.tx_receipt(hsh)
            r = conn.do(o)
            txs[j].apply_receipt(r)
            logg.debug('get receipt {}/{}: {}'.format(j+1, c, hsh))
            i += 1
        return i


    def merge_rcpts(self, conn, txs):
        if self.chain_interface.batch_limit == 1:
            return self.merge_rcpts_single(conn, txs)

        rcpts = []
        c = 0
        for tx in txs:
            rcpts.append(self.chain_interface.tx_receipt(tx.hash))
            c += 1
            if c == self.chain_interface.batch_limit:
                break

        rcpts_r = conn.do(rcpts)
        i = 0
        for j in range(len(rcpts)):
            rcpt = rcpts_r[j]
            if rcpt != None:
                txs[j].apply_receipt(self.chain_interface.src_normalize(rcpt))
            i += 1
        return i


    def process(self, conn, item, block):
        txs = []
        i = item.tx_cursor
        while True:
            # handle block objects regardless of whether the tx data is embedded or not
            try:
                tx = block.tx(i)
            except AttributeError:
                tx_hash = block.txs[i]
                o = self.chain_interface.tx_by_hash(tx_hash, block=block)
                r = conn.do(o)
            except IndexError:
                break
            txs.append(tx)
            i += 1
  
        j = len(txs)
        i = 0
        while i < j:
            i += self.merge_rcpts(conn, txs[i:])

        for tx in txs:
            self.process_single(conn, block, tx)
        raise IndexError()
