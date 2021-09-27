# standard imports
import copy
import logging
import multiprocessing

# local imports
from chainsyncer.driver.history import HistorySyncer
from .threadpool import ThreadPoolTask

#logg = logging.getLogger(__name__)
logg = logging.getLogger()


#def range_to_backends(chain_spec, block_offset, tx_offset, block_target, flags, flags_count, backend_class, backend_count):
def sync_split(block_offset, block_target, count):
    block_count = block_target - block_offset
    if block_count < count:
        logg.warning('block count is less than thread count, adjusting thread count to {}'.format(block_count))
        count = block_count
    blocks_per_thread = int(block_count / count)

    #backends = []
    #for i in range(backend_count):
    ranges = []
    for i in range(count):
        block_target = block_offset + blocks_per_thread
        #backend = backend_class.custom(chain_spec, block_target - 1, block_offset=block_offset, tx_offset=tx_offset, flags=flags, flags_count=flags_count)
        offset = block_offset
        target = block_target -1
        ranges.append((offset, target,))
        block_offset = block_target
#        tx_offset = 0
#        flags = 0

#    return backends
    return ranges


class ThreadPoolRangeTask:

    def __init__(self, backend, sync_range, conn_factory, chain_interface, syncer_factory=HistorySyncer):
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
        self.conn_factory = conn_factory


    def start_loop(self, interval):
        conn = self.conn_factory()
        return self.syncer.loop(interval, conn)


class ThreadPoolRangeHistorySyncer:

    def __init__(self, conn_factory, thread_count, backend, chain_interface, pre_callback=None, block_callback=None, post_callback=None, runlevel_callback=None):
        self.src_backend = backend
        self.thread_count = thread_count
        self.conn_factory = conn_factory
        self.single_sync_offset = 0
        self.runlevel_callback = None
        backend_start = backend.start()
        backend_target = backend.target()
        self.ranges = sync_split(backend_start[0][0], backend_target[0], thread_count)
        self.chain_interface = chain_interface


    def loop(self, interval, conn):
        self.worker_pool = multiprocessing.Pool(processes=self.thread_count)
        for sync_range in self.ranges:
            conn = self.conn_factory()
            task = ThreadPoolRangeTask(self.src_backend, sync_range, self.conn_factory, self.chain_interface)
            t = self.worker_pool.apply_async(task.start_loop, (0.1,))
            print(t.get())
        self.worker_pool.close()
        self.worker_pool.join()
