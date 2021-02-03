import uuid
import json

import websocket

from .response import EVMResponse
from cic_syncer.error import RequestError



class EVMWebsocketClient:

    def __init__(self, url):
        self.url = url
        self.conn = websocket.create_connection(url)


    def __del__(self):
        self.conn.close()


    def block_number(self):
        req_id = str(uuid.uuid4())
        req = {
                'jsonrpc': '2.0',
                'method': 'eth_blockNumber',
                'id': str(req_id),
                'params': [],
                }
        self.conn.send(json.dumps(req))
        r = self.conn.recv()
        res = EVMResponse('block_number', json.loads(r))
        err = res.get_error()
        if err != None:
            raise RequestError(err)

        return res.get_result()
