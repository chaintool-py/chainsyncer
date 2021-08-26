# standard imports
import unittest

# external imports
from chainlib.chain import ChainSpec

# local imports
from chainsyncer.backend.memory import MemBackend

# testutil imports
from tests.chainsyncer_base import TestBase


class TestBasic(TestBase):

    def test_hello(self):
        chain_spec = ChainSpec('evm', 'bloxberg', 8996, 'foo')
        backend = MemBackend(chain_spec, 'foo') 


if __name__ == '__main__':
    unittest.main()
