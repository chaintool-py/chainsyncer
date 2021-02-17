# standard imports
import unittest

# external imports
from chainlib.chain import ChainSpec

# local imports
from chainsyncer.backend import SyncerBackend

# testutil imports
from tests.base import TestBase


class TestBasic(TestBase):

    def test_hello(self):
        chain_spec = ChainSpec('evm', 'bloxberg', 8996, 'foo')
        backend = SyncerBackend(chain_spec, 'foo') 


if __name__ == '__main__':
    unittest.main()
