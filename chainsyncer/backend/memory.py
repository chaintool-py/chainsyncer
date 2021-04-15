# standard imports
import logging

logg = logging.getLogger().getChild(__name__)


class MemBackend:

    def __init__(self, chain_spec, object_id, target_block=None):
        self.object_id = object_id
        self.chain_spec = chain_spec
        self.block_height = 0
        self.tx_height = 0
        self.flags = 0
        self.target_block = target_block
        self.db_session = None
        self.filter_names = []
        self.filter_values = []


    def connect(self):
        pass


    def disconnect(self):
        pass


    def set(self, block_height, tx_height):
        logg.debug('stateless backend received {} {}'.format(block_height, tx_height))
        self.block_height = block_height
        self.tx_height = tx_height
        for i in range(len(self.filter_values)):
            self.filter_values[i] = False


    def get(self):
        return ((self.block_height, self.tx_height), self.flags)


    def target(self):
        return (self.target_block, self.flags)


    def register_filter(self, name):
        self.filter_names.append(name)
        self.filter_values.append(False)


    def complete_filter(self, n):
        self.filter_values[n-1] = True
        logg.debug('set filter {}'.format(self.filter_names[n-1]))


    def __str__(self):
        return "syncer membackend chain {} cursor".format(self.get())
        
