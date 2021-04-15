# standard imports
import logging

# local imports
from .base import Backend

logg = logging.getLogger().getChild(__name__)


class MemBackend(Backend):

    def __init__(self, chain_spec, object_id, target_block=None):
        super(MemBackend, self).__init__()
        self.object_id = object_id
        self.chain_spec = chain_spec
        self.block_height = 0
        self.tx_height = 0
        self.flags = 0
        self.target_block = target_block
        self.db_session = None
        self.filter_names = []


    def connect(self):
        pass


    def disconnect(self):
        pass


    def set(self, block_height, tx_height):
        logg.debug('stateless backend received {} {}'.format(block_height, tx_height))
        self.block_height = block_height
        self.tx_height = tx_height


    def get(self):
        return ((self.block_height, self.tx_height), self.flags)


    def target(self):
        return (self.target_block, self.flags)


    def register_filter(self, name):
        self.filter_names.append(name)
        self.filter_count += 1


    def complete_filter(self, n):
        v = 1 << n
        self.flags |= v
        logg.debug('set filter {} {}'.format(self.filter_names[n], v))


    def reset_filter(self):
        logg.debug('reset filters')
        self.flags = 0

    
    def get_flags(self):
        return flags


    def __str__(self):
        return "syncer membackend chain {} cursor".format(self.get())
        
