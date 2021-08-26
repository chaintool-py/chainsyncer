# standard imports
import logging
#import threading
import multiprocessing
import queue

# external imports
from chainlib.error import RPCException

# local imports
from .history import HistorySyncer
from chainsyncer.error import SyncDone

logg = logging.getLogger(__name__)



class ThreadedHistorySyncer(HistorySyncer):

    def __init__(self, conn_factory, thread_limit, backend, chain_interface, pre_callback=None, block_callback=None, post_callback=None, conn_limit=0):
        super(ThreadedHistorySyncer, self).__init__(backend, chain_interface, pre_callback, block_callback, post_callback)
        self.workers = []
        if conn_limit == 0:
            conn_limit = thread_limit
        #self.conn_pool = queue.Queue(conn_limit)
        #self.queue = queue.Queue(thread_limit)
        #self.quit_queue = queue.Queue(1)
        self.conn_pool = multiprocessing.Queue(conn_limit)
        self.queue = multiprocessing.Queue(thread_limit)
        self.quit_queue = multiprocessing.Queue(1)
        #self.lock = threading.Lock()
        self.lock = multiprocessing.Lock()
        for i in range(thread_limit):
            #w = threading.Thread(target=self.worker)
            w = multiprocessing.Process(target=self.worker)
            self.workers.append(w)

        for i in range(conn_limit):
            self.conn_pool.put(conn_factory())


    def terminate(self):
        self.quit_queue.put(())
        super(ThreadedHistorySyncer, self).terminate()


    def worker(self):
        while True:
            block_number = None
            try:
                block_number = self.queue.get(timeout=0.01)
            except queue.Empty:
                if self.quit_queue.qsize() > 0:
                    #logg.debug('{} received quit'.format(threading.current_thread().getName()))
                    logg.debug('{} received quit'.format(multiprocessing.current_process().name))
                    return
                continue
            conn = self.conn_pool.get()
            try:
                logg.debug('processing parent {} {}'.format(conn, block_number))
                self.process_parent(conn, block_number)
            except IndexError:
                pass
            except RPCException as e:
                logg.error('RPC failure for block {}, resubmitting to queue: {}'.format(block, e))
                self.queue.put(block_number)
            conn = self.conn_pool.put(conn)


    def process_parent(self, conn, block_number):
            logg.debug('getting block {}'.format(block_number))
            o = self.chain_interface.block_by_number(block_number)
            r = conn.do(o)
            block = self.chain_interface.block_from_src(r)
            logg.debug('got block typ {}'.format(type(block)))
            super(ThreadedHistorySyncer, self).process(conn, block)


    def process_single(self, conn, block, tx):
        self.filter.apply(conn, block, tx)


    def process(self, conn, block):
        pass


    #def process(self, conn, block):
    def get(self, conn):
        if not self.running:
            raise SyncDone()

        block_number = None
        tx_index = None
        flags = None
        ((block_number, tx_index), flags) = self.backend.get()
        try:
            #logg.debug('putting {}'.format(block.number))
            #self.queue.put((conn, block_number,), timeout=0.1)
            self.queue.put(block_number, timeout=0.1)
        except queue.Full:
            #logg.debug('queue full, try again')
            return
   
        target, flags = self.backend.target()
        next_block = block_number + 1
        if next_block > target:
            self.quit_queue.put(())
            raise SyncDone()
        self.backend.set(self.backend.block_height + 1, 0)


#    def get(self, conn):
#        try:
#            r = super(ThreadedHistorySyncer, self).get(conn)
#            return r
#        except SyncDone as e:
#            self.quit_queue.put(())
#            raise e


    def loop(self, interval, conn):
        for w in self.workers:
            w.start()
        r = super(ThreadedHistorySyncer, self).loop(interval, conn)
        for w in self.workers:
            w.join()
        while True:
            try:
                self.quit_queue.get_nowait()
            except queue.Empty:
                break

        logg.info('workers done {}'.format(r))
