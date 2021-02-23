# standard imports
import uuid
import logging
import time
import signal

# external imports
from chainlib.eth.block import (
        block_by_number,
        Block,
        )
from chainlib.eth.tx import receipt

# local imports
from chainsyncer.filter import SyncFilter
from chainsyncer.error import (
        SyncDone,
        NoBlockForYou,
    )

logg = logging.getLogger(__name__)


def noop_callback(block_number, tx_index, s=None):
    logg.debug('noop callback ({},{}) {}'.format(block_number, tx_index, s))


class Syncer:

    running_global = True
    yield_delay=0.005
    signal_set = False

    def __init__(self, backend, loop_callback=noop_callback, progress_callback=noop_callback):
        self.cursor = None
        self.running = True
        self.backend = backend
        self.filter = SyncFilter(backend)
        self.progress_callback = progress_callback
        self.loop_callback = loop_callback
        if not Syncer.signal_set:
            signal.signal(signal.SIGINT, Syncer.__sig_terminate)
            signal.signal(signal.SIGTERM, Syncer.__sig_terminate)
            Syncer.signal_set = True


    @staticmethod
    def __sig_terminate(sig, frame):
        logg.warning('got signal {}'.format(sig))
        Syncer.terminate()


    @staticmethod
    def terminate():
        logg.info('termination requested!')
        Syncer.running_global = False


    def chain(self):
        """Returns the string representation of the chain spec for the chain the syncer is running on.

        :returns: Chain spec string
        :rtype: str
        """
        return self.bc_cache.chain()


    def add_filter(self, f):
        self.filter.add(f)
        self.backend.register_filter(str(f))


class BlockPollSyncer(Syncer):

    def __init__(self, backend, loop_callback=noop_callback, progress_callback=noop_callback):
        super(BlockPollSyncer, self).__init__(backend, loop_callback, progress_callback)


    def loop(self, interval, conn):
        (g, flags) = self.backend.get()
        last_tx = g[1]
        last_block = g[0]
        self.progress_callback(last_block, last_tx, 'loop started')
        while self.running and Syncer.running_global:
            if self.loop_callback != None:
                self.loop_callback(last_block, last_tx)
            while True and Syncer.running_global:
                try:
                    block = self.get(conn)
                except SyncDone as e:
                    logg.info('sync done: {}'.format(e))
                    return self.backend.get()
                except NoBlockForYou as e:
                    break
                last_block = block.number
                self.process(conn, block)
                start_tx = 0
                self.progress_callback(last_block, last_tx, 'processed block {}'.format(self.backend.get()))
                time.sleep(self.yield_delay)
            self.progress_callback(last_block + 1, last_tx, 'loop ended')
            time.sleep(interval)


class HeadSyncer(BlockPollSyncer):

    def process(self, conn, block):
        logg.debug('process block {}'.format(block))
        i = 0
        tx = None
        while True:
            try:
                tx = block.tx(i)
                rcpt = conn.do(receipt(tx.hash))
                tx.apply_receipt(rcpt)
                self.progress_callback(block.number, i, 'processing {}'.format(repr(tx)))
                self.backend.set(block.number, i)
                self.filter.apply(conn, block, tx)
            except IndexError as e:
                self.backend.set(block.number + 1, 0)
                break
            i += 1
        

    def get(self, conn):
        (height, flags) = self.backend.get()
        block_number = height[0]
        block_hash = []
        o = block_by_number(block_number)
        r = conn.do(o)
        if r == None:
            raise NoBlockForYou()
        b = Block(r)
        logg.debug('get {}'.format(b))

        return b


    def __str__(self):
        return '[headsyncer] {}'.format(str(self.backend))


class HistorySyncer(HeadSyncer):

    def __init__(self, backend, loop_callback=noop_callback, progress_callback=noop_callback):
        super(HeadSyncer, self).__init__(backend, loop_callback, progress_callback)
        self.block_target = None
        (block_number, flags) = self.backend.target()
        if block_number == None:
            raise AttributeError('backend has no future target. Use HeadSyner instead')
        self.block_target = block_number


    def get(self, conn):
        (height, flags) = self.backend.get()
        if self.block_target < height[0]:
            raise SyncDone(self.block_target)
        block_number = height[0]
        block_hash = []
        o = block_by_number(block_number)
        r = conn.do(o)
        if r == None:
            raise NoBlockForYou()
        b = Block(r)
        logg.debug('get {}'.format(b))

        return b


    def __str__(self):
        return '[historysyncer] {}'.format(str(self.backend))


