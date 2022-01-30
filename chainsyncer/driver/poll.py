# standard imports
import logging
import time

# local imports
from .base import Syncer
from chainsyncer.error import (
        SyncDone,
        NoBlockForYou,
        )

logg = logging.getLogger(__name__)


NS_DIV = 1000000000

class BlockPollSyncer(Syncer):
    """Syncer driver implementation of chainsyncer.driver.base.Syncer that retrieves new blocks through polling.
    """

    name = 'blockpoll'


    def __init__(self, backend, chain_interface, pre_callback=None, block_callback=None, post_callback=None, idle_callback=None):
        super(BlockPollSyncer, self).__init__(backend, chain_interface, pre_callback=pre_callback, block_callback=block_callback, post_callback=post_callback)
        self.idle_callback = idle_callback
        self.last_start = 0
        self.clock_id = time.CLOCK_MONOTONIC_RAW


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


    def loop(self, interval, conn):
        """Indefinite loop polling the given RPC connection for new blocks in the given interval.

        :param interval: Seconds to wait for next poll after processing of previous poll has been completed.
        :type interval: int
        :param conn: RPC connection
        :type conn: chainlib.connection.RPCConnection
        :rtype: tuple
        :returns: See chainsyncer.backend.base.Backend.get
        """
        (pair, fltr) = self.backend.get()
        start_tx = pair[1]


        while self.running and Syncer.running_global:
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
