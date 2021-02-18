# standard imports
import uuid
import logging
import time

# external imports
from chainlib.eth.block import (
        block_by_number,
        Block,
        )

# local imports
from chainsyncer.filter import SyncFilter

logg = logging.getLogger()


def noop_progress(s, block_number, tx_index):
    logg.debug('({},{}) {}'.format(block_number, tx_index, s))


class Syncer:

    running_global = True
    yield_delay=0.005

    def __init__(self, backend, progress_callback=noop_progress):
        self.cursor = None
        self.running = True
        self.backend = backend
        self.filter = SyncFilter(backend)
        self.progress_callback = progress_callback


    def chain(self):
        """Returns the string representation of the chain spec for the chain the syncer is running on.

        :returns: Chain spec string
        :rtype: str
        """
        return self.bc_cache.chain()


    def add_filter(self, f):
        self.filter.add(f)


class BlockSyncer(Syncer):

    def __init__(self, backend, progress_callback=noop_progress):
        super(BlockSyncer, self).__init__(backend, progress_callback)


    def loop(self, interval, conn):
        g = self.backend.get()
        last_tx = g[1]
        last_block = g[0]
        self.progress_callback('loop started', last_block, last_tx)
        while self.running and Syncer.running_global:
            while True:
                try:
                    block = self.get(conn)
                except Exception:
                    break
                last_block = block.number
                self.process(conn, block)
                start_tx = 0
                self.progress_callback('processed block {}'.format(self.backend.get()), last_block, last_tx)
                time.sleep(self.yield_delay)
            self.progress_callback('loop ended', last_block + 1, last_tx)
            time.sleep(interval)


class HeadSyncer(BlockSyncer):

    def __init__(self, backend, progress_callback=noop_progress):
        super(HeadSyncer, self).__init__(backend, progress_callback)


    def process(self, conn, block):
        logg.debug('process block {}'.format(block))
        i = 0
        tx = None
        while True:
            try:
                tx = block.tx(i)
                self.progress_callback('processing {}'.format(repr(tx)), block.number, i)
                self.backend.set(block.number, i)
                self.filter.apply(conn, block, tx)
            except IndexError as e:
                self.backend.set(block.number + 1, 0)
                break
            i += 1
        

    def get(self, conn):
        (block_number, tx_number) = self.backend.get()
        block_hash = []
        o = block_by_number(block_number)
        r = conn.do(o)
        b = Block(r)
        logg.debug('get {}'.format(b))

        return b
