from cic_syncer.client import translate

translations = {
        'block_number': 'hex_to_int',
        }


class EVMResponse:

    def __init__(self, item, response_object):
        self.response_object = response_object
        self.item = item
        self.fn = getattr(translate, translations[self.item])


    def get_error(self):
        return self.response_object.get('error')


    def get_result(self):
        return self.fn(self.response_object.get('result'))
