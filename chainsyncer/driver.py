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


def noop_callback(block_number, tx_index, s=None):
    logg.debug('({},{}) {}'.format(block_number, tx_index, s))


class Syncer:

    running_global = True
    yield_delay=0.005

    def __init__(self, backend, loop_callback=noop_callback, progress_callback=noop_callback):
        self.cursor = None
        self.running = True
        self.backend = backend
        self.filter = SyncFilter(backend)
        self.progress_callback = progress_callback
        self.loop_callback = loop_callback


    def chain(self):
        """Returns the string representation of the chain spec for the chain the syncer is running on.

        :returns: Chain spec string
        :rtype: str
        """
        return self.bc_cache.chain()


    def add_filter(self, f):
        self.filter.add(f)


class BlockPollSyncer(Syncer):

    def __init__(self, backend, loop_callback=noop_callback, progress_callback=noop_callback):
        super(BlockPollSyncer, self).__init__(backend, loop_callback, progress_callback)


    def loop(self, interval, conn):
        g = self.backend.get()
        last_tx = g[1]
        last_block = g[0]
        self.progress_callback(last_block, last_tx, 'loop started')
        while self.running and Syncer.running_global:
            if self.loop_callback != None:
                self.loop_callback(last_block, last_tx)
            while True:
                try:
                    block = self.get(conn)
                except Exception:
                    break
                last_block = block.number
                self.process(conn, block)
                start_tx = 0
                self.progress_callback(last_block, last_tx, 'processed block {}'.format(self.backend.get()))
                time.sleep(self.yield_delay)
            self.progress_callback(last_block + 1, last_tx, 'loop ended')
            time.sleep(interval)


class HeadSyncer(BlockPollSyncer):

    def __init__(self, backend, loop_callback=noop_callback, progress_callback=noop_callback):
        super(HeadSyncer, self).__init__(backend, loop_callback, progress_callback)


    def process(self, conn, block):
        logg.debug('process block {}'.format(block))
        i = 0
        tx = None
        while True:
            try:
                tx = block.tx(i)
                self.progress_callback(block.number, i, 'processing {}'.format(repr(tx)))
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
