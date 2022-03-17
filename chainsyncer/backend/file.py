# standard imports
import os
import uuid
import shutil
import logging

# local imports
from .base import Backend

logg = logging.getLogger().getChild(__name__)

BACKEND_BASE_DIR = '/var/lib'


def chain_dir_for(chain_spec, base_dir=BACKEND_BASE_DIR):
    """Retrieve file backend directory for the given chain spec.

    :param chain_spec: Chain spec context of backend
    :type chain_spec: chainlib.chain.ChainSpec
    :param base_dir: Base directory to use for generation. Default is value of BACKEND_BASE_DIR
    :type base_dir: str 
    :rtype: str
    :returns: Absolute path of chain backend directory
    """
    base_data_dir = os.path.join(base_dir, 'chainsyncer')
    return os.path.join(base_data_dir, str(chain_spec).replace(':', '/'))


def data_dir_for(chain_spec, object_id, base_dir=BACKEND_BASE_DIR):
    """Retrieve file backend directory for the given syncer.

    :param chain_spec: Chain spec context of backend
    :type chain_spec: chainlib.chain.ChainSpec
    :param object_id: Syncer id
    :type object_id: str
    :param base_dir: Base directory to use for generation. Default is value of BACKEND_BASE_DIR
    :type base_dir: str 
    :rtype: str
    :returns: Absolute path of chain backend directory
    """
    chain_dir = chain_dir_for(chain_spec, base_dir=base_dir)
    return os.path.join(chain_dir, object_id)


class FileBackend(Backend):
    """Filesystem backend implementation for syncer state.

    FileBackend uses reverse order of filter flags.

    :param chain_spec: Chain spec for the chain that syncer is running for.
    :type chain_spec: cic_registry.chain.ChainSpec
    :param object_id: Unique id for the syncer session.
    :type object_id: str
    :param base_dir: Base directory to use for generation. Default is value of BACKEND_BASE_DIR
    :type base_dir: str 
    """
    __warned = False

    def __init__(self, chain_spec, object_id, base_dir=BACKEND_BASE_DIR):
        if not FileBackend.__warned:
            logg.warning('file backend for chainsyncer is experimental and not yet guaranteed to handle interrupted filter execution.')
            FileBackend.__warned = True
        super(FileBackend, self).__init__(object_id, flags_reversed=True)
        self.object_data_dir = data_dir_for(chain_spec, object_id, base_dir=base_dir)

        self.object_id = object_id
        self.db_object = None
        self.db_object_filter = None
        self.chain_spec = chain_spec

        self.filter = b'\x00'
        self.filter_names = []

        if self.object_id != None:
            self.connect()
            self.disconnect()


    @staticmethod
    def create_object(chain_spec, object_id=None, base_dir=BACKEND_BASE_DIR):
        """Creates a new syncer session at the given backend destination.

        :param chain_spec: Chain spec for the chain that syncer is running for.
        :type chain_spec: cic_registry.chain.ChainSpec
        :param object_id: Unique id for the syncer session.
        :type object_id: str
        :param base_dir: Base directory to use for generation. Default is value of BACKEND_BASE_DIR
        :type base_dir: str 
        """
        if object_id == None:
            object_id = str(uuid.uuid4())

        object_data_dir = data_dir_for(chain_spec, object_id, base_dir=base_dir)

        if os.path.isdir(object_data_dir):
            raise FileExistsError(object_data_dir)

        os.makedirs(object_data_dir)

        object_id_path = os.path.join(object_data_dir, 'object_id')
        f = open(object_id_path, 'wb')
        f.write(object_id.encode('utf-8'))
        f.close()

        init_value = 0
        b = init_value.to_bytes(16, byteorder='big')
        offset_path = os.path.join(object_data_dir, 'offset')
        f = open(offset_path, 'wb')
        f.write(b)
        f.close()

        target_path = os.path.join(object_data_dir, 'target')
        f = open(target_path, 'wb')
        f.write(b'\x00' * 16)
        f.close()

        cursor_path = os.path.join(object_data_dir, 'cursor')
        f = open(cursor_path, 'wb')
        f.write(b'\x00' * 16)
        f.close()

        cursor_path = os.path.join(object_data_dir, 'filter')
        f = open(cursor_path, 'wb')
        f.write(b'\x00' * 9)
        f.close()

        filter_name_path = os.path.join(object_data_dir, 'filter_name')
        f = open(filter_name_path, 'wb')
        f.write(b'')
        f.close()

        return object_id


    def load(self):
        """Loads the state of the syncer at the given location of the instance.

        :raises FileNotFoundError: Invalid data directory
        :raises IsADirectoryError: Invalid data directory
        """
        offset_path = os.path.join(self.object_data_dir, 'offset')
        f = open(offset_path, 'rb')
        b = f.read(16)
        f.close()
        self.block_height_offset = int.from_bytes(b[:8], byteorder='big')
        self.tx_index_offset = int.from_bytes(b[8:], byteorder='big')

        target_path = os.path.join(self.object_data_dir, 'target')
        f = open(target_path, 'rb')
        b = f.read(16)
        f.close()
        self.block_height_target = int.from_bytes(b[:8], byteorder='big')
        self.tx_index_target = int.from_bytes(b[8:], byteorder='big')

        cursor_path = os.path.join(self.object_data_dir, 'cursor')
        f = open(cursor_path, 'rb')
        b = f.read(16)
        f.close()
        self.block_height_cursor = int.from_bytes(b[:8], byteorder='big')
        self.tx_index_cursor = int.from_bytes(b[8:], byteorder='big')

        filter_path = os.path.join(self.object_data_dir, 'filter')
        f = open(filter_path, 'rb')
        b = f.read(8)
        self.filter_count = int.from_bytes(b, byteorder='big')
        filter_count_bytes = int((self.filter_count - 1) / 8 + 1)
        if filter_count_bytes > 0:
            self.filter = f.read(filter_count_bytes)
        f.close()

        filter_name_path = filter_path + '_name'
        f = open(filter_name_path, 'r')
        while True:
            s = f.readline().rstrip()
            if len(s) == 0:
                break
            self.filter_names.append(s)
        f.close()


    def connect(self):
        """Proxy for chainsyncer.backend.file.FileBackend.load that performs a basic sanity check for instance's backend location.

        :raises ValueError: Sanity check failed
        """
        object_path = os.path.join(self.object_data_dir, 'object_id') 
        f = open(object_path, 'r')
        object_id = f.read()
        f.close()
        if object_id != self.object_id:
            raise ValueError('data corruption in store for id {}'.format(object_id))

        self.load()


    def disconnect(self):
        """FileBackend applies no actual connection, so this is noop
        """
        pass

    
    def purge(self):
        """Remove syncer state from backend.
        """
        shutil.rmtree(self.object_data_dir)


    def get(self):
        """Get the current state of the syncer cursor.

        :rtype: tuple
        :returns: Block height / tx index tuple, and filter flags value
        """
        logg.debug('filter {}'.format(self.filter.hex()))
        return ((self.block_height_cursor, self.tx_index_cursor), self.get_flags())


    def get_flags(self):
        """Get canonical representation format of flags.

        :rtype: int
        :returns: Filter flag bitfield value
        """
        return int.from_bytes(self.filter, 'little')


    def set(self, block_height, tx_index):
        """Update the state of the syncer cursor.

        :param block_height: New block height
        :type block_height: int
        :param tx_height: New transaction height in block
        :type tx_height: int
        :returns: Block height / tx index tuple, and filter flags value
        :rtype: tuple
        """
        self.__set(block_height, tx_index, 'cursor')

#        cursor_path = os.path.join(self.object_data_dir, 'filter')
#        f = open(cursor_path, 'r+b')
#        f.seek(8)
#        l = len(self.filter)
#        c = 0
#        while c < l:
#            c += f.write(self.filter[c:])
#        f.close()

        return ((self.block_height_cursor, self.tx_index_cursor), self.get_flags())


    def __set(self, block_height, tx_index, category):
        cursor_path = os.path.join(self.object_data_dir, category)

        block_height_bytes = block_height.to_bytes(8, byteorder='big')
        tx_index_bytes = tx_index.to_bytes(8, byteorder='big')

        f = open(cursor_path, 'wb')
        b = f.write(block_height_bytes)
        b = f.write(tx_index_bytes)
        f.close()

        setattr(self, 'block_height_' + category, block_height)
        setattr(self, 'tx_index_' + category, tx_index)


    @staticmethod
    def initial(chain_spec, target_block_height, start_block_height=0, base_dir=BACKEND_BASE_DIR):
        """Creates a new syncer session and commit its initial state to backend.

        :param chain_spec: Chain spec of chain that syncer is running for.
        :type chain_spec: cic_registry.chain.ChainSpec
        :param target_block_height: Target block height
        :type target_block_height: int
        :param start_block_height: Start block height
        :type start_block_height: int
        :param base_dir: Base directory to use for generation. Default is value of BACKEND_BASE_DIR
        :type base_dir: str 
        :raises ValueError: Invalid start/target specification
        :returns: New syncer object 
        :rtype: cic_eth.db.models.BlockchainSync
        """
        if start_block_height >= target_block_height:
            raise ValueError('start block height must be lower than target block height')
       
        uu = FileBackend.create_object(chain_spec, base_dir=base_dir)

        o = FileBackend(chain_spec, uu, base_dir=base_dir)
        o.__set(target_block_height, 0, 'target')
        o.__set(start_block_height, 0, 'offset')
        o.__set(start_block_height, 0, 'cursor')

        return o


    @staticmethod
    def live(chain_spec, block_height, base_dir=BACKEND_BASE_DIR):
        """Creates a new open-ended syncer session starting at the given block height.

        :param chain: Chain spec of chain that syncer is running for.
        :type chain: cic_registry.chain.ChainSpec
        :param block_height: Start block height
        :type block_height: int
        :param base_dir: Base directory to use for generation. Default is value of BACKEND_BASE_DIR
        :type base_dir: str 
        :returns: "Live" syncer object
        :rtype: cic_eth.db.models.BlockchainSync
        """
        uu = FileBackend.create_object(chain_spec, base_dir=base_dir)
        o = FileBackend(chain_spec, uu, base_dir=base_dir)
        o.__set(block_height, 0, 'offset')
        o.__set(block_height, 0, 'cursor')

        return o


    def target(self):
        """Get the target state (upper bound of sync) of the syncer cursor.

        :returns: Block height and filter flags value
        :rtype: tuple
        """

        return (self.block_height_target, 0,)


    def start(self):
        """Get the initial state of the syncer cursor.

        :returns: Block height / tx index tuple, and filter flags value
        :rtype: tuple
        """
        return ((self.block_height_offset, self.tx_index_offset), 0,)


    @staticmethod
    def __sorted_entries(chain_spec, base_dir=BACKEND_BASE_DIR):
        chain_dir = chain_dir_for(chain_spec, base_dir=base_dir)

        entries = {}

        for v in os.listdir(chain_dir):
            d = os.path.realpath(os.path.join(chain_dir, v))
            f = open(os.path.join(d, 'object_id'))
            object_id = f.read()
            f.close()

            logg.debug('found syncer entry {} in {}'.format(object_id, d))

            o = FileBackend(chain_spec, object_id, base_dir=base_dir)

            entries[o.block_height_offset] = o

        sorted_entries = []
        for k in sorted(entries):
            sorted_entries.append(entries[k])

        return sorted_entries


    @staticmethod
    def resume(chain_spec, block_height, base_dir=BACKEND_BASE_DIR):
        """Retrieves and returns all previously unfinished syncer sessions.

        If a previous open-ended syncer is found, a new syncer will be generated to sync from where that syncer left off until the block_height given as argument.

        :param chain_spec: Chain spec of chain that syncer is running for
        :type chain_spec: cic_registry.chain.ChainSpec
        :param block_height: Target block height for previous live syncer
        :type block_height: int
        :param base_dir: Base directory to use for generation. Default is value of BACKEND_BASE_DIR
        :type base_dir: str 
        :raises FileNotFoundError: Invalid backend location
        :returns: Syncer objects of unfinished syncs
        :rtype: list of cic_eth.db.models.BlockchainSync
        """
        try:
            return FileBackend.__sorted_entries(chain_spec, base_dir=base_dir)
        except FileNotFoundError:
            return []


    @staticmethod
    def first(chain_spec, base_dir=BACKEND_BASE_DIR):
        """Returns the model object of the most recent syncer in backend.

        :param chain_spec: Chain spec of chain that syncer is running for.
        :type chain_spec: cic_registry.chain.ChainSpec
        :param base_dir: Base directory to use for generation. Default is value of BACKEND_BASE_DIR
        :type base_dir: str 
        :returns: Last syncer object 
        :rtype: cic_eth.db.models.BlockchainSync
        """
        entries = []
        try:
            entries = FileBackend.__sorted_entries(chain_spec, base_dir=base_dir)
        except FileNotFoundError:
            return entries
        return entries[len(entries)-1]


    # n is zero-index of bit field
    def begin_filter(self, n, base_dir=BACKEND_BASE_DIR):
        pass


    # n is zero-index of bit field
    def complete_filter(self, n, base_dir=BACKEND_BASE_DIR):
        """Sets the filter at the given index as completed.

        :param n: Filter index, starting at zero
        :type n: int
        :raises IndexError: Index is outside filter count range
        """
        if self.filter_count <= n:
            raise IndexError('index {} out of ranger for filter size {}'.format(n, self.filter_count))

        byte_pos = int(n / 8)
        bit_pos = n % 8

        byts = bytearray(self.filter)
        b = (0x80 >> bit_pos)
        b |= self.filter[byte_pos]
        logg.debug('bbb {}'.format(type(b)))
        byts[byte_pos] = b #b.to_bytes(1, byteorder='big')
        self.filter = byts
        
        filter_path = os.path.join(self.object_data_dir, 'filter')
        f = open(filter_path, 'r+b')
        f.seek(8 + byte_pos)
        f.write(self.filter)
        f.close()


    def register_filter(self, name):
        """Add filter to backend.

        Overwrites record on disk if manual changed members in struct

        :param name: Name of filter
        :type name: str
        """
        filter_path = os.path.join(self.object_data_dir, 'filter')
        if (self.filter_count + 1) % 8 == 0:
            self.filter += b'\x00'
            f = open(filter_path, 'a+b')
            f.write(b'\x00')
            f.close()
      
        filter_name_path = filter_path + '_name'
        f = open(filter_name_path, 'a')
        f.write(name + '\n')
        f.close()

        self.filter_count += 1
        f = open(filter_path, 'r+b')
        b = self.filter_count.to_bytes(8, byteorder='big')
        f.write(b)
        f.close()


    def reset_filter(self):
        """Reset all filter states.
        """
        self.filter = b'\x00' * len(self.filter)
        cursor_path = os.path.join(self.object_data_dir, 'filter')
        f = open(cursor_path, 'r+b')
        f.seek(8)
        l = len(self.filter)
        c = 0
        while c < l:
            c += f.write(self.filter[c:])
        f.close()
