# standard imports
import uuid
import logging
import time
import signal

# external imports
import sqlalchemy
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


def noop_callback(block, tx):
    logg.debug('noop callback ({},{})'.format(block, tx))


class Syncer:

    running_global = True
    yield_delay=0.005
    signal_set = False

    def __init__(self, backend, pre_callback=None, block_callback=None, post_callback=None):
        self.cursor = None
        self.running = True
        self.backend = backend
        self.filter = SyncFilter(backend)
        self.block_callback = block_callback
        self.pre_callback = pre_callback
        self.post_callback = post_callback
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


    def process_single(self, conn, block, tx, block_height, tx_index):
        self.backend.set(block_height, tx_index)
        self.filter.apply(conn, block, tx)


class BlockPollSyncer(Syncer):

    def __init__(self, backend, pre_callback=None, block_callback=None, post_callback=None):
        super(BlockPollSyncer, self).__init__(backend, pre_callback, block_callback, post_callback)


    def loop(self, interval, conn):
        #(g, flags) = self.backend.get()
        #last_tx = g[1]
        #last_block = g[0]
        #self.progress_callback(last_block, last_tx, 'loop started')
        while self.running and Syncer.running_global:
            if self.pre_callback != None:
                self.pre_callback()
            while True and Syncer.running_global:
                try:
                    block = self.get(conn)
                except SyncDone as e:
                    logg.info('sync done: {}'.format(e))
                    return self.backend.get()
                except NoBlockForYou as e:
                    break
# TODO: To properly handle this, ensure that previous request is rolled back
#                except sqlalchemy.exc.OperationalError as e:
#                    logg.error('database error: {}'.format(e))
#                    break

                if self.block_callback != None:
                    self.block_callback(block, None)

                last_block = block
                self.process(conn, block)
                start_tx = 0
                time.sleep(self.yield_delay)
            if self.post_callback != None:
                self.post_callback()
            time.sleep(interval)


class HeadSyncer(BlockPollSyncer):

    def process(self, conn, block):
        logg.debug('process block {}'.format(block))
        i = 0
        tx = None
        while True:
            try:
                tx = block.tx(i)
            except IndexError as e:
                logg.debug('index error syncer rcpt get {}'.format(e))
                self.backend.set(block.number + 1, 0)
                break

            rcpt = conn.do(receipt(tx.hash))
            tx.apply_receipt(rcpt)
    
            self.process_single(conn, block, tx, block.number, i)
                        
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

        return b


    def __str__(self):
        return '[headsyncer] {}'.format(str(self.backend))


class HistorySyncer(HeadSyncer):

    def __init__(self, backend, pre_callback=None, block_callback=None, post_callback=None):
        super(HeadSyncer, self).__init__(backend, pre_callback, block_callback, post_callback)
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

        return b


    def __str__(self):
        return '[historysyncer] {}'.format(str(self.backend))


