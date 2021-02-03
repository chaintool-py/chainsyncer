# standard imports
import uuid
import logging
import time

logg = logging.getLogger()


class Syncer:

    running_global = True

    def __init__(self, backend):
        self.cursor = None
        self.running = True
        self.backend = backend
        self.filter = []


    def chain(self):
        """Returns the string representation of the chain spec for the chain the syncer is running on.

        :returns: Chain spec string
        :rtype: str
        """
        return self.bc_cache.chain()



class MinedSyncer(Syncer):

    def __init__(self, backend):
        super(MinedSyncer, self).__init__(backend)


    def loop(self, interval, getter):
        while self.running and Syncer.running_global:
            e = self.get(getter)
            time.sleep(interval)


class HeadSyncer(MinedSyncer):

    def __init__(self, backend):
        super(HeadSyncer, self).__init__(backend)


    def get(self, getter):
        (block_number, tx_number) = self.backend.get()
        block_hash = []
        uu = uuid.uuid4()
        res = getter.get_block_by_integer(block_number)
        logg.debug(res)

        return block_hash

