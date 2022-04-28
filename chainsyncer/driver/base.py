# standard imports
import logging
import time
import signal

# local imports
from chainsyncer.error import (
        SyncDone,
        NoBlockForYou,
        )
from chainsyncer.session import SyncSession


logg = logging.getLogger(__name__)

NS_DIV = 1000000000

class SyncDriver:

    running_global = True
    """If set to false syncer will terminate polling loop."""
    yield_delay=0.005
    """Delay between each processed block."""
    signal_request = [signal.SIGINT, signal.SIGTERM]
    """Signals to catch to request shutdown."""
    signal_set = False
    """Whether shutdown signal has been received."""
    name = 'base'
    """Syncer name, to be overriden for each extended implementation."""


    def __init__(self, store, offset=0, target=-1, pre_callback=None, post_callback=None, block_callback=None, idle_callback=None):
        self.store = store
        self.running = True
        self.pre_callback = pre_callback
        self.post_callback = post_callback
        self.block_callback = block_callback
        self.idle_callback = idle_callback
        self.last_start = 0
        self.clock_id = time.CLOCK_MONOTONIC_RAW
        self.store.connect()
        self.store.start(offset=offset, target=target)
        if not SyncDriver.signal_set:
            for sig in SyncDriver.signal_request:
                signal.signal(sig, self.__sig_terminate)
            SyncDriver.signal_set = True


    def __sig_terminate(self, sig, frame):
        logg.warning('got signal {}'.format(sig))
        self.terminate()


    def terminate(self):
        """Set syncer to terminate as soon as possible.
        """
        logg.info('termination requested!')
        SyncDriver.running_global = False
        self.running = False


    def run(self, conn, interval=1):
        while self.running_global:
            self.session = SyncSession(self.store)
            item = self.session.start()
            if item == None:
                self.running = False
                self.running_global = False
                break
            self.loop(conn, item, interval=interval)


    def idle(self, interval):
        interval *= NS_DIV
        idle_start = time.clock_gettime_ns(self.clock_id)
        delta = idle_start - self.last_start
        if delta > interval:
            interval /= NS_DIV
            time.sleep(interval)
            return

        if self.idle_callback != None:
            r = True
            while r:
                before = time.clock_gettime_ns(self.clock_id)
                r = self.idle_callback(interval)
                after = time.clock_gettime_ns(self.clock_id)
                delta = after - before
                if delta < 0:
                    return
                interval -= delta
                if interval < 0:
                    return

        interval /= NS_DIV
        time.sleep(interval)


    def loop(self, conn, item, interval=1):
        logg.debug('started loop')
        while self.running and SyncDriver.running_global:
            self.last_start = time.clock_gettime_ns(self.clock_id)

            if self.pre_callback != None:
                self.pre_callback()

            while True and self.running:
                try:
                    block = self.get(conn, item)
                except SyncDone as e:
                    logg.info('all blocks sumitted for processing: {}'.format(e))
                    return
                except NoBlockForYou as e:
                    break
                if self.block_callback != None:
                    self.block_callback(block, None)

                try:
                    self.process(conn, item, block)
                except IndexError:
                    item.next(advance_block=True)
                time.sleep(self.yield_delay)

                if self.store.target > -1 and block.number >= self.store.target:
                    self.running = False

            if self.post_callback != None:
                self.post_callback()
   

            self.idle(interval)


    def process_single(self, conn, block, tx):
        self.session.filter(conn, block, tx)


    def process(self, conn, item, block):
        raise NotImplementedError()


    def get(self, conn):
        raise NotImplementedError()

