# standard imports
import logging

logg = logging.getLogger(__name__)


class Backend:
    """Base class for syncer state backend.

    :param flags_reversed: If set, filter flags are interpreted from left to right
    :type flags_reversed: bool
    """

    def __init__(self, object_id, flags_reversed=False):
        self.object_id = object_id
        self.filter_count = 0
        self.flags_reversed = flags_reversed

        self.block_height_offset = 0
        self.tx_index_offset = 0

        self.block_height_cursor = 0
        self.tx_index_cursor = 0

        self.block_height_target = 0
        self.tx_index_target = 0

    
    def check_filter(self, n, flags):
        """Check whether an individual filter flag is set.

        :param n: Bit index
        :type n: int
        :param flags: Bit field to check against
        :type flags: int
        :rtype: bool
        :returns: True if set
        """
        if self.flags_reversed:
            try:
                v = 1 << flags.bit_length() - 1
                return (v >> n) & flags > 0
            except ValueError:
                pass
            return False
        return flags & (1 << n) > 0



    def chain(self):
        """Returns chain spec for syncer.

        :returns: Chain spec
        :rtype chain_spec: cic_registry.chain.ChainSpec
        """
        return self.chain_spec


    def __str__(self):
        return "syncerbackend {} chain {} start {} target {}".format(self.object_id, self.chain(), self.start(), self.target())
