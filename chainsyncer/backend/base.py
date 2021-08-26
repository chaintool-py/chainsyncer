# standard imports
import logging

logg = logging.getLogger().getChild(__name__)


class Backend:

    def __init__(self, flags_reversed=False):
        self.filter_count = 0
        self.flags_reversed = flags_reversed

        self.block_height_offset = 0
        self.tx_index_offset = 0

        self.block_height_cursor = 0
        self.tx_index_cursor = 0

        self.block_height_target = 0
        self.tx_index_target = 0

   
    
    def check_filter(self, n, flags):
        if self.flags_reversed:
            try:
                v = 1 << flags.bit_length() - 1
                return (v >> n) & flags > 0
            except ValueError:
                pass
            return False
        return flags & (1 << n) > 0



    def chain(self):
        """Returns chain spec for syncer

        :returns: Chain spec
        :rtype chain_spec: cic_registry.chain.ChainSpec
        """
        return self.chain_spec

    def __str__(self):
        return "syncerbackend chain {} start {} target {}".format(self.chain(), self.start(), self.target())
