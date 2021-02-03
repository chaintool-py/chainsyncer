# standard imports
import uuid
import logging

# third-party imports
import websockets

logg = logging.getLogger()


class Syncer:

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
        super(HeadSyncer, self).__init__(backend)


    def loop(self, interval):
        while self.running and Syncer.running_global:
            getter = self.backend.connect()
            logg.debug('loop execute')
            e = self.get(getter)


class HeadSyncer(MinedSyncer):

    def __init__(self, backend):
        super(HeadSyncer, self).__init__(backend)


    def get(self, getter):
        (block_number, tx_number) = self.backend.get()
        block_hash = []
        try:
            uu = uuid.uuid4()
            req = {
                    'jsonrpc': '2.0',
                    'method': 'eth_getBlock',
                    'id': str(uu),
                    'param': [block_number],
                    }
            logg.debug(req)
        except Exception as e:
            logg.error(e)

        return block_hash

