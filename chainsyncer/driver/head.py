# standard imports
import logging

# local imports
from chainsyncer.error import NoBlockForYou
from .poll import BlockPollSyncer

logg = logging.getLogger(__name__)

class HeadSyncer(BlockPollSyncer):

    name = 'head'

    def process(self, conn, block):
        (pair, fltr) = self.backend.get()
        logg.debug('process block {} (backend {}:{})'.format(block, pair, fltr))
        i = pair[1] # set tx index from previous
        tx = None
        while True:
            try:
                tx = block.tx(i)
            except AttributeError:
                o = tx(block.txs[i])
                r = conn.do(o)
                tx = self.interface.tx_from_src(Tx.src_normalize(r), block=block)
            #except IndexError as e:
            #    logg.debug('index error syncer tx get {}'.format(e))
            #    break

            # TODO: Move specifics to eth subpackage, receipts are not a global concept
            rcpt = conn.do(self.chain_interface.tx_receipt(tx.hash))
            if rcpt != None:
                tx.apply_receipt(self.chain_interface.src_normalize(rcpt))

            self.process_single(conn, block, tx)
            self.backend.reset_filter()
                        
            i += 1
        

    def get(self, conn):
        (height, flags) = self.backend.get()
        block_number = height[0]
        block_hash = []
        o = self.chain_interface.block_by_number(block_number)
        r = conn.do(o)
        if r == None:
            raise NoBlockForYou()
        b = self.chain_interface.block_from_src(r)
        b.txs = b.txs[height[1]:]

        return b
