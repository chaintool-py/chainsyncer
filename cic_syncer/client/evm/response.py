import json

from cic_syncer.client import translate
from cic_syncer.client.block import Block
from cic_syncer.client.tx import Tx


translations = {
        'block_number': translate.hex_to_int,
        'get_block': json.dumps,
        'number': translate.hex_to_int,
        }


class EVMResponse:

    def __init__(self, item, response_object):
        self.response_object = response_object
        self.item = item
        self.fn = translations[self.item]


    def get_error(self):
        return self.response_object.get('error')


    def get_result(self):
        r = self.fn(self.response_object.get('result'))
        if r == 'null':
            return None
        return r


class EVMTx(Tx):

    def __init__(self, block, tx_number, obj):
        super(EVMTx, self).__init__(block, tx_number, obj)
    

class EVMBlock(Block):

    def tx(self, idx):
        o = self.obj['transactions'][idx]
        return Tx(self, idx, o)


    def number(self):
        return translate.hex_to_int(self.obj['number'])


    def __str__(self):
        return str('block {} {}'.format(self.number(), self.hash))
