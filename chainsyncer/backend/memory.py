# standard imports
import logging

# local imports
from .base import Backend

logg = logging.getLogger(__name__)


class MemBackend(Backend):
    """Disposable syncer backend. Keeps syncer state in memory.

    Filter bitfield is interpreted right to left.

    :param chain_spec: Chain spec context of syncer
    :type chain_spec: chainlib.chain.ChainSpec
    :param object_id: Unique id for the syncer session.
    :type object_id: str
    :param target_block: Block height to terminate sync at
    :type target_block: int
    """

    def __init__(self, chain_spec, object_id, target_block=None, block_height=0, tx_height=0, flags=0):
        super(MemBackend, self).__init__(object_id)
        self.chain_spec = chain_spec
        self.block_height_offset = block_height
        self.block_height_cursor = block_height
        self.tx_height_offset = tx_height
        self.tx_height_cursor = tx_height
        self.block_height_target = target_block
        self.db_session = None
        self.flags = flags
        self.filter_names = []


    def connect(self):
        """NOOP as memory backend implements no connection.
        """
        pass


    def disconnect(self):
        """NOOP as memory backend implements no connection.
        """
        pass


    def set(self, block_height, tx_height):
        """Set the syncer state.

        :param block_height: New block height
        :type block_height: int
        :param tx_height: New transaction height in block
        :type tx_height: int
        """
        logg.debug('memory backend received {} {}'.format(block_height, tx_height))
        self.block_height_cursor = block_height
        self.tx_height_cursor = tx_height


    def get(self):
        """Get the current syncer state

        :rtype: tuple
        :returns: block height / tx index tuple, and filter flags value
        """
        return ((self.block_height_cursor, self.tx_height_cursor), self.flags)


    def target(self):
        """Returns the syncer target.

        :rtype: tuple
        :returns: block height / tx index tuple
        """
        return (self.block_height_target, self.flags)


    def register_filter(self, name):
        """Adds a filter identifier to the syncer.

        :param name: Filter name
        :type name: str
        """
        self.filter_names.append(name)
        self.filter_count += 1


    def begin_filter(self, n):
        """Set filter at index as completed for the current block / tx state.

        :param n: Filter index
        :type n: int
        """
        v = 1 << n
        self.flags |= v
        logg.debug('set filter {} {}'.format(self.filter_names[n], v))


    def complete_filter(self, n):
        pass


    def reset_filter(self):
        """Set all filters to unprocessed for the current block / tx state.
        """
        logg.debug('reset filters')
        self.flags = 0

    
    def __str__(self):
        return "syncer membackend {} chain {} cursor {}".format(self.object_id, self.chain(), self.get())
