# standard imports
import uuid
import logging

# third-party imports
import websockets

logg = logging.getLogger()


class Syncer:

    def __init__(self, backend):
        super(HeadSyncer, self).__init__(backend)


class MinedSyncer(Syncer):

    def __init__(self, backend):
        super(HeadSyncer, self).__init__(backend)



class HeadSyncer(MinedSyncer):

    def __init__(self, backend):
        super(HeadSyncer, self).__init__(backend)


    def get(self, getter):
        (block_number, tx_number) = self.backend
        block_hash = []
        try:
            uu = uuid.uuid4()
            req = {
                    'jsonrpc': '2.0',
                    'method': 'eth_getBlock',
                    'id': str(uu),
                    'param': [block_number],
            logg.debug(req)
        except Exception as e:
            logg.error(e)

        return block_hash

