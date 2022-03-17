# standard imports
import logging
import time

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

    def __init__(self, conn, store, pre_callback=None, post_callback=None, block_callback=None, idle_callback=None):
        self.store = store
        self.running = True
        self.pre_callback = pre_callback
        self.post_callback = post_callback
        self.block_callback = block_callback
        self.idle_callback = idle_callback
        self.last_start = 0
        self.clock_id = time.CLOCK_MONOTONIC_RAW
        self.session = SyncSession(self.store)


    def __sig_terminate(self, sig, frame):
        logg.warning('got signal {}'.format(sig))
        self.terminate()


    def terminate(self):
        """Set syncer to terminate as soon as possible.
        """
        logg.info('termination requested!')
        SyncDriver.running_global = False
        self.running = False


    def run(self):
        while self.running_global:
            item = self.store.next_item()
            logg.debug('item {}'.format(item))
            if item == None:
                self.running = False
                self.running_global = False
                break
            self.loop(item)


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


    def loop(self, item):
        while self.running and SyncDriver.running_global:
            self.last_start = time.clock_gettime_ns(self.clock_id)
            if self.pre_callback != None:
                self.pre_callback()
            while True and self.running:
                if start_tx > 0:
                    start_tx -= 1
                    continue
                try:
                    block = self.get(conn)
                except SyncDone as e:
                    logg.info('all blocks sumitted for processing: {}'.format(e))
                    return self.backend.get()
                except NoBlockForYou as e:
                    break
                if self.block_callback != None:
                    self.block_callback(block, None)

                last_block = block
                try:
                    self.process(conn, block)
                except IndexError:
                    self.backend.set(block.number + 1, 0)
                start_tx = 0
                time.sleep(self.yield_delay)
            if self.post_callback != None:
                self.post_callback()

            self.idle(interval)

    def process_single(self, conn, block, tx):
        self.session.filter(conn, block, tx)


    def process(self, conn, block):
        raise NotImplementedError()


    def get(self, conn):
        raise NotImplementedError()
