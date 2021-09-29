# standard imports
import copy
import logging
import multiprocessing
import os

# external iports
from chainlib.eth.connection import RPCConnection
# local imports
from chainsyncer.driver.history import HistorySyncer
from chainsyncer.driver.base import Syncer
from .threadpool import ThreadPoolTask

logg = logging.getLogger(__name__)


def sync_split(block_offset, block_target, count):
    block_count = block_target - block_offset
    if block_count < count:
        logg.warning('block count is less than thread count, adjusting thread count to {}'.format(block_count))
        count = block_count
    blocks_per_thread = int(block_count / count)

    ranges = []
    for i in range(count):
        block_target = block_offset + blocks_per_thread
        offset = block_offset
        target = block_target -1
        ranges.append((offset, target,))
        block_offset = block_target
    return ranges


class ThreadPoolRangeTask:

    def __init__(self, backend, sync_range, chain_interface, syncer_factory=HistorySyncer, filters=[]):
        backend_start = backend.start()
        backend_target = backend.target()
        backend_class = backend.__class__
        tx_offset = 0
        flags = 0
        if sync_range[0] == backend_start[0][0]:
            tx_offset = backend_start[0][1]
            flags = backend_start[1]
        self.backend = backend_class.custom(backend.chain_spec, sync_range[1], block_offset=sync_range[0], tx_offset=tx_offset, flags=flags, flags_count=0)
        self.syncer = syncer_factory(self.backend, chain_interface)
        for fltr in filters:
            self.syncer.add_filter(fltr)

    def start_loop(self, interval):
        conn = RPCConnection.connect(self.backend.chain_spec)
        return self.syncer.loop(interval, conn)


class ThreadPoolRangeHistorySyncer:

    def __init__(self, thread_count, backend, chain_interface, pre_callback=None, block_callback=None, post_callback=None, runlevel_callback=None):
        self.src_backend = backend
        self.thread_count = thread_count
        self.single_sync_offset = 0
        self.runlevel_callback = None
        backend_start = backend.start()
        backend_target = backend.target()
        self.ranges = sync_split(backend_start[0][0], backend_target[0], thread_count)
        self.chain_interface = chain_interface
        self.filters = []


    def add_filter(self, f):
        self.filters.append(f)


    def loop(self, interval, conn):
        self.worker_pool = multiprocessing.Pool(processes=self.thread_count)

        for sync_range in self.ranges:
            task = ThreadPoolRangeTask(self.src_backend, sync_range, self.chain_interface, filters=self.filters)
            t = self.worker_pool.apply_async(task.start_loop, (0.1,))
            logg.debug('result of worker {}: {}'.format(t, t.get()))
        self.worker_pool.close()
        self.worker_pool.join()
