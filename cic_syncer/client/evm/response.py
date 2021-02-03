import json

from cic_syncer.client import translate


translations = {
        'block_number': translate.hex_to_int,
        'get_block': json.dumps,
        }


class EVMResponse:

    def __init__(self, item, response_object):
        self.response_object = response_object
        self.item = item
        self.fn = translations[self.item]


    def get_error(self):
        return self.response_object.get('error')


    def get_result(self):
        return self.fn(self.response_object.get('result'))
