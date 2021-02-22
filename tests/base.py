# standard imports
import logging
import unittest
import tempfile
import os
#import pysqlite

# external imports
from chainlib.chain import ChainSpec

# local imports
from chainsyncer.db import dsn_from_config
from chainsyncer.db.models.base import SessionBase

script_dir = os.path.realpath(os.path.dirname(__file__))

logging.basicConfig(level=logging.DEBUG)


class TestBase(unittest.TestCase):

    def setUp(self):
        db_dir = tempfile.mkdtemp()
        self.db_path = os.path.join(db_dir, 'test.sqlite')
        config = {
            'DATABASE_ENGINE': 'sqlite',
            'DATABASE_DRIVER': 'pysqlite',
            'DATABASE_NAME': self.db_path,
                }
        dsn = dsn_from_config(config)
        SessionBase.poolable = False
        SessionBase.transactional = False
        SessionBase.procedural = False
        SessionBase.connect(dsn, debug=False)

        f = open(os.path.join(script_dir, '..', 'sql', 'sqlite', '1.sql'), 'r')
        sql = f.read()
        f.close()

        conn = SessionBase.engine.connect()
        conn.execute(sql)

        f = open(os.path.join(script_dir, '..', 'sql', 'sqlite', '2.sql'), 'r')
        sql = f.read()
        f.close()

        conn = SessionBase.engine.connect()
        conn.execute(sql)

        self.chain_spec = ChainSpec('evm', 'foo', 42, 'bar')

    def tearDown(self):
        SessionBase.disconnect()
        os.unlink(self.db_path)
