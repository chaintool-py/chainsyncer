# standard imports
import logging
import unittest
import tempfile
import os
#import pysqlite

# external imports
from chainlib.chain import ChainSpec
from chainlib.interface import ChainInterface
from chainlib.eth.tx import (
        receipt,
        Tx,
        )
from chainlib.eth.block import (
        block_by_number,
        Block,
        )
from potaahto.symbols import snake_and_camel

# local imports
from chainsyncer.db import dsn_from_config
from chainsyncer.db.models.base import SessionBase

# test imports
from chainsyncer.unittest.db import ChainSyncerDb

script_dir = os.path.realpath(os.path.dirname(__file__))

logging.basicConfig(level=logging.DEBUG)


class EthChainInterface(ChainInterface):
    
    def __init__(self):
        self._tx_receipt = receipt
        self._block_by_number = block_by_number
        self._block_from_src = Block.from_src
        self._tx_from_src = Tx.from_src
        self._src_normalize = snake_and_camel


class TestBase(unittest.TestCase):

    interface = EthChainInterface()

    def setUp(self):
        self.db = ChainSyncerDb()
        
        #f = open(os.path.join(script_dir, '..', 'sql', 'sqlite', '1.sql'), 'r')
        #sql = f.read()
        #f.close()

        #conn = SessionBase.engine.connect()
        #conn.execute(sql)

        #f = open(os.path.join(script_dir, '..', 'sql', 'sqlite', '2.sql'), 'r')
        #sql = f.read()
        #f.close()

        #conn = SessionBase.engine.connect()
        #conn.execute(sql)
        self.session = self.db.bind_session()
        self.chain_spec = ChainSpec('evm', 'foo', 42, 'bar')

    def tearDown(self):
        self.session.commit()
        self.db.release_session(self.session)
        #os.unlink(self.db_path)
