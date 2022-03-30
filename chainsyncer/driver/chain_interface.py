# external imports
from chainlib.error import RPCException

# local imports
from chainsyncer.error import NoBlockForYou
from chainsyncer.driver import SyncDriver


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


    def process(self, conn, item, block):
        tx_src = None
        i = item.tx_cursor
        while True:
            # handle block objects regardless of whether the tx data is embedded or not
            try:
                tx = block.tx(i)
            except AttributeError:
                tx_hash = block.txs[i]
                o = self.chain_interface.tx_by_hash(tx_hash, block=block)
                r = conn.do(o)
                #tx = self.chain_interface.tx_from_src(tx_src, block=block)

            rcpt = conn.do(self.chain_interface.tx_receipt(tx.hash))
            if rcpt != None:
                tx.apply_receipt(self.chain_interface.src_normalize(rcpt))

            self.process_single(conn, block, tx)
                        
            i += 1
