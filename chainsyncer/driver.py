# standard imports
import uuid
import logging
import time

logg = logging.getLogger()


def noop_progress(s):
    logg.debug(s)


class Syncer:

    running_global = True
    yield_delay=0.005

    def __init__(self, backend, progress_callback=noop_progress):
        self.cursor = None
        self.running = True
        self.backend = backend
        self.filter = []
        self.progress_callback = progress_callback


    def chain(self):
        """Returns the string representation of the chain spec for the chain the syncer is running on.

        :returns: Chain spec string
        :rtype: str
        """
        return self.bc_cache.chain()


    def add_filter(self, f):
        self.filter.append(f)


class MinedSyncer(Syncer):

    def __init__(self, backend, progress_callback):
        super(MinedSyncer, self).__init__(backend, progress_callback)


    def loop(self, interval, getter):
        while self.running and Syncer.running_global:
            while True:
                block_hash = self.get(getter)
                if block_hash == None:
                    break
                self.process(getter, block_hash)
                time.sleep(self.yield_delay)
            time.sleep(interval)


class HeadSyncer(MinedSyncer):

    def __init__(self, backend, progress_callback):
        super(HeadSyncer, self).__init__(backend, progress_callback)


    def process(self, getter, block):
        logg.debug('process {}'.format(block))
        i = 0
        tx = None
        while True:
            try:
                #self.filter[0].handle(getter, block, None)
                tx = block.tx(i)
                self.progress_callback('processing {}'.format(tx))
                self.backend.set(block.number, i)
                for f in self.filter:
                    f.handle(getter, block, tx)
                    self.progress_callback('applied filter {} on {}'.format(f.name(), tx))
            except IndexError as e:
                self.backend.set(block.number + 1, 0)
                break
            i += 1
        

    def get(self, getter):
        (block_number, tx_number) = self.backend.get()
        block_hash = []
        uu = uuid.uuid4()
        res = getter.get(block_number)
        logg.debug('get {}'.format(res))

        return res
