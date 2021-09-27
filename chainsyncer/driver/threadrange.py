# standard imports
import copy
import logging
import multiprocessing

# local imports
from chainsyncer.driver.history import HistorySyncer
from .threadpool import ThreadPoolTask

#logg = logging.getLogger(__name__)
logg = logging.getLogger()


def range_to_backends(chain_spec, block_offset, tx_offset, block_target, flags, flags_count, backend_class, backend_count):
    block_count = block_target - block_offset
    if block_count < backend_count:
        logg.warning('block count is less than thread count, adjusting thread count to {}'.format(block_count))
        backend_count = block_count
    blocks_per_thread = int(block_count / backend_count)

    backends = []
    for i in range(backend_count):
        block_target = block_offset + blocks_per_thread
        backend = backend_class.custom(chain_spec, block_target - 1, block_offset=block_offset, tx_offset=tx_offset, flags=flags, flags_count=flags_count)
        backends.append(backend)
        block_offset = block_target
        tx_offset = 0
        flags = 0

    return backends


class ThreadPoolRangeTask:
    
    loop_func = None

    def __init__(self, backend, conn):
        pass


    def foo(self, a, b):
        return self.loop_func()


class ThreadPoolRangeHistorySyncer(HistorySyncer):

    def __init__(self, conn_factory, thread_count, backends, chain_interface, loop_func=HistorySyncer.loop, pre_callback=None, block_callback=None, post_callback=None, runlevel_callback=None):
        if thread_count > len(backends):
            raise ValueError('thread count {} is greater than than backend count {}'.format(thread_count, len(backends)))
        self.backends = backends
        self.thread_count = thread_count
        self.conn_factory = conn_factory
        self.single_sync_offset = 0
        self.runlevel_callback = None

        ThreadPoolRangeTask.loop_func = loop_func


    def loop(self, interval, conn):
        super_loop = super(ThreadPoolRangeHistorySyncer, self).loop
        self.worker_pool = multiprocessing.Pool(processes=self.thread_count)
        for backend in self.backends:
            conn = self.conn_factory()
            task = ThreadPoolRangeTask(backend, conn)
            t = self.worker_pool.apply_async(task.foo, (backend, conn,))
            print(t.get())
        self.worker_pool.close()
        self.worker_pool.join()
