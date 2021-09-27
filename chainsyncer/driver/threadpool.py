# standard imports
import logging
#import threading
import multiprocessing
import queue
import time

# external imports
from chainlib.error import RPCException

# local imports
from .history import HistorySyncer
from chainsyncer.error import SyncDone

logg = logging.getLogger(__name__)


def foobarcb(v):
    logg.debug('foooz {}'.format(v))


class ThreadPoolTask:

    process_func = None
    chain_interface = None

    def poolworker(self, block_number, conn):
#            conn = args[1].get()
            try:
                logg.debug('processing parent {} {}'.format(conn, block_number))
                #self.process_parent(self.conn, block_number)
                self.process_parent(conn, block_number)
            except IndexError:
                pass
            except RPCException as e:
                logg.error('RPC failure for block {}, resubmitting to queue: {}'.format(block, e))
                raise e
                #self.queue.put(block_number)
#            conn = self.conn_pool.put(conn)

    def process_parent(self, conn, block_number):
            logg.debug('getting block {}'.format(block_number))
            o = self.chain_interface.block_by_number(block_number)
            r = conn.do(o)
            block = self.chain_interface.block_from_src(r)
            logg.debug('got block typ {}'.format(type(block)))
            #super(ThreadedHistorySyncer, self).process(conn, block)
            self.process_func(conn, block)



class ThreadPoolHistorySyncer(HistorySyncer):

    def __init__(self, conn_factory, thread_limit, backend, chain_interface, pre_callback=None, block_callback=None, post_callback=None, conn_limit=0):
        super(ThreadPoolHistorySyncer, self).__init__(backend, chain_interface, pre_callback, block_callback, post_callback)
        self.workers = []
        self.thread_limit = thread_limit
        if conn_limit == 0:
            self.conn_limit = self.thread_limit
        #self.conn_pool = queue.Queue(conn_limit)
        #self.queue = queue.Queue(thread_limit)
        #self.quit_queue = queue.Queue(1)
        #self.conn_pool = multiprocessing.Queue(conn_limit)
        #self.queue = multiprocessing.Queue(thread_limit)
        #self.quit_queue = multiprocessing.Queue(1)
        #self.lock = threading.Lock()
        #self.lock = multiprocessing.Lock()
        ThreadPoolTask.process_func = super(ThreadPoolHistorySyncer, self).process
        ThreadPoolTask.chain_interface = chain_interface
        #for i in range(thread_limit):
            #w = threading.Thread(target=self.worker)
        #    w = multiprocessing.Process(target=self.worker)
        #    self.workers.append(w)

        #for i in range(conn_limit):
        #    self.conn_pool.put(conn_factory())
        self.conn_factory = conn_factory
        self.worker_pool = None


    def terminate(self):
        #self.quit_queue.put(())
        super(ThreadPoolHistorySyncer, self).terminate()


#    def worker(self):
#        while True:
#            block_number = None
#            try:
#                block_number = self.queue.get(timeout=0.01)
#            except queue.Empty:
#                if self.quit_queue.qsize() > 0:
#                    #logg.debug('{} received quit'.format(threading.current_thread().getName()))
#                    logg.debug('{} received quit'.format(multiprocessing.current_process().name))
#                    return
#                continue
#            conn = self.conn_pool.get()
#            try:
#                logg.debug('processing parent {} {}'.format(conn, block_number))
#                self.process_parent(conn, block_number)
#            except IndexError:
#                pass
#            except RPCException as e:
#                logg.error('RPC failure for block {}, resubmitting to queue: {}'.format(block, e))
#                self.queue.put(block_number)
#            conn = self.conn_pool.put(conn)
#


    def process_single(self, conn, block, tx):
        self.filter.apply(conn, block, tx)


    def process(self, conn, block):
        pass


    def get(self, conn):
        if not self.running:
            raise SyncDone()

        block_number = None
        tx_index = None
        flags = None
        ((block_number, tx_index), flags) = self.backend.get()
        #try:
            #logg.debug('putting {}'.format(block.number))
            #self.queue.put((conn, block_number,), timeout=0.1)
            #self.queue.put(block_number, timeout=0.1)
        #except queue.Full:
            #logg.debug('queue full, try again')
        #    return
        task = ThreadPoolTask()
        conn = self.conn_factory()
        self.worker_pool.apply_async(task.poolworker, (block_number, conn,), {}, foobarcb)

        target, flags = self.backend.target()
        next_block = block_number + 1
        if next_block > target:
            #self.quit_queue.put(())
            self.worker_pool.close()
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
        self.worker_pool = multiprocessing.Pool(self.thread_limit)
        #for w in self.workers:
        #    w.start()
        r = super(ThreadPoolHistorySyncer, self).loop(interval, conn)
        #for w in self.workers:
        #    w.join()
        #while True:
        #    try:
        #     self.quit_queue.get_nowait()
        #    except queue.Empty:
        #        break
        time.sleep(1)
        self.worker_pool.join()

        logg.info('workers done {}'.format(r))
