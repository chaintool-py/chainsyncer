# standard imports
import uuid
import logging
import time

logg = logging.getLogger()


class Syncer:

    running_global = True

    def __init__(self, backend, handler):
        self.cursor = None
        self.running = True
        self.backend = backend
        self.filter = []
        self.handler = handler


    def chain(self):
        """Returns the string representation of the chain spec for the chain the syncer is running on.

        :returns: Chain spec string
        :rtype: str
        """
        return self.bc_cache.chain()



class MinedSyncer(Syncer):

    def __init__(self, backend, handler):
        super(MinedSyncer, self).__init__(backend, handler)


    def loop(self, interval, getter):
        while self.running and Syncer.running_global:
            block_hash = self.get(getter)
            if block_hash != None:
                self.process(getter, block_hash)
            time.sleep(interval)


class HeadSyncer(MinedSyncer):

    def __init__(self, backend, handler):
        super(HeadSyncer, self).__init__(backend, handler)


    def process(self, getter, block):
        logg.debug('process block {}'.format(block))
        block = getter.get_block_by_hash(block.hash)
        i = 0
        tx = None
        while True:
            try:
                self.filter[0].handle(getter, block, None)
                tx = block.tx(i)
                logg.debug('tx {}'.format(tx))
                self.backend.set(block.number(), i)
                for f in self.filter:
                    f(getter, block, tx)
            except IndexError as e:
                self.backend.set(block.number() + 1, 0)
                break
            i += 1
        

    def get(self, getter):
        (block_number, tx_number) = self.backend.get()
        block_hash = []
        uu = uuid.uuid4()
        res = getter.get_block_by_integer(block_number)
        logg.debug('get {}'.format(res))

        return res

