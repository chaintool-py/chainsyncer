# standard imports
import logging
import uuid

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

    def __init__(self, chain_spec, object_id):
        super(MemBackend, self).__init__(object_id)
        self.chain_spec = chain_spec
        self.db_session = None
        self.block_height_offset = 0
        self.block_height_cursor = 0
        self.tx_height_offset = 0
        self.tx_height_cursor = 0
        self.block_height_target = None
        self.flags = 0
        self.flags_start = 0
        self.flags_target = 0
        self.filter_names = []


    @staticmethod
    def custom(chain_spec, target_block, block_offset=0, tx_offset=0, flags=0, flags_count=0, *args, **kwargs):
        object_id = kwargs.get('object_id', str(uuid.uuid4()))
        backend = MemBackend(chain_spec, object_id)
        backend.block_height_offset = block_offset
        backend.block_height_cursor = block_offset
        backend.tx_height_offset = tx_offset
        backend.tx_height_cursor = tx_offset
        backend.block_height_target = target_block
        backend.flags = flags
        backend.flags_count = flags_count
        backend.flags_start = flags
        flags_target = (2 ** flags_count) - 1
        backend.flags_target = flags_target
        return backend


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


    def start(self):
        """Get the initial syncer state

        :rtype: tuple
        :returns: block height / tx index tuple, and filter flags value
        """
        return ((self.block_height_offset, self.tx_height_offset), self.flags_start)


    def target(self):
        """Returns the syncer target.

        :rtype: tuple
        :returns: block height / tx index tuple
        """
        return (self.block_height_target, self.flags_target)


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
