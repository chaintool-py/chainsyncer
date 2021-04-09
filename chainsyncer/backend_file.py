# standard imports
import os
import uuid
import shutil
import logging

logging.basicConfig(level=logging.DEBUG)
logg = logging.getLogger().getChild(__name__)


def data_dir_for(chain_spec, object_id, base_dir='/var/lib'):
    base_data_dir = os.path.join(base_dir, 'chainsyncer')
    chain_dir = str(chain_spec).replace(':', '/')
    return os.path.join(base_data_dir, chain_dir, object_id)


class SyncerFileBackend:

    def __init__(self, chain_spec, object_id=None, base_dir='/var/lib'):
        self.object_data_dir = data_dir_for(chain_spec, object_id, base_dir=base_dir)

        self.block_height_offset = 0
        self.tx_index_offset = 0

        self.block_height_cursor = 0
        self.tx_index_cursor = 0

        self.block_height_target = 0
        self.tx_index_target = 0

        self.object_id = object_id
        self.db_object = None
        self.db_object_filter = None
        self.chain_spec = chain_spec

        if self.object_id != None:
            self.connect()
            self.disconnect()


    @staticmethod
    def create_object(chain_spec, object_id=None, base_dir='/var/lib'):
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

        return object_id


    def load(self):
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


    def connect(self):
        object_path = os.path.join(self.object_data_dir, 'object_id') 
        f = open(object_path, 'r')
        object_id = f.read()
        f.close()
        if object_id != self.object_id:
            raise ValueError('data corruption in store for id {}'.format(object_id))

        self.load()


    def disconnect(self):
        pass

    
    def purge(self):
        shutil.rmtree(self.object_data_dir)


    def get(self):
        return (self.block_height_cursor, self.tx_index_cursor)



    def set(self, block_height, tx_index):
        return self.__set(block_height, tx_index, 'cursor')


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
    def initial(chain_spec, target_block_height, start_block_height=0, base_dir='/var/lib'):
        if start_block_height >= target_block_height:
            raise ValueError('start block height must be lower than target block height')
       
        uu = SyncerFileBackend.create_object(chain_spec, base_dir=base_dir)

        o = SyncerFileBackend(chain_spec, uu, base_dir=base_dir)
        o.__set(target_block_height, 0, 'target')
        o.__set(start_block_height, 0, 'offset')

        return uu


    def target(self):
        return ((self.block_height_target, self.tx_index_target), None,)


    def start(self):
        return ((self.block_height_offset, self.tx_index_offset), None,)
