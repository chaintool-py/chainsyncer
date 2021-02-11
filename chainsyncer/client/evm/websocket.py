# standard imports
import logging
import uuid
import json

# third-party imports
import websocket
from hexathon import add_0x

# local imports
from .response import EVMResponse
from chainsyncer.error import RequestError
from chainsyncer.client.evm.response import EVMBlock

logg = logging.getLogger()


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


    def block_by_integer(self, n):
        req_id = str(uuid.uuid4())
        nhx = '0x' + n.to_bytes(8, 'big').hex()
        req = {
                'jsonrpc': '2.0',
                'method': 'eth_getBlockByNumber',
                'id': str(req_id),
                'params': [nhx, False],
                }
        self.conn.send(json.dumps(req))
        r = self.conn.recv()
        res = EVMResponse('get_block', json.loads(r))
        err = res.get_error()
        if err != None:
            raise RequestError(err)

        j = res.get_result()
        if j == None:
            return None
        o = json.loads(j)
        return EVMBlock(o['hash'], o)


    def block_by_hash(self, hx_in):
        req_id = str(uuid.uuid4())
        hx = add_0x(hx_in)
        req ={
                'jsonrpc': '2.0',
                'method': 'eth_getBlockByHash',
                'id': str(req_id),
                'params': [hx, False],
                }
        self.conn.send(json.dumps(req))
        r = self.conn.recv()
        res = EVMResponse('get_block', json.loads(r))
        err = res.get_error()
        if err != None:
            raise RequestError(err)

        j = res.get_result()
        if j == None:
            return None
        o = json.loads(j)
        return EVMBlock(o['hash'], o)
