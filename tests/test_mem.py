# standard imports
import unittest
import logging

# external imports
from chainlib.chain import ChainSpec

# local imports
from chainsyncer.backend.memory import MemBackend

# testutil imports
from tests.chainsyncer_base import TestBase

logging.basicConfig(level=logging.DEBUG)


class TestMem(TestBase):

    def test_backend_mem_custom(self):
        chain_spec = ChainSpec('evm', 'bloxberg', 8996, 'foo')
        flags = int(5).to_bytes(2, 'big')
        flag_count = 10
        flags_target = (2 ** 10) - 1
        backend = MemBackend.custom(chain_spec, 666, 42, 2, flags, flag_count, object_id='xyzzy')
        self.assertEqual(((42, 2), flags), backend.start())
        self.assertEqual(((42, 2), flags), backend.get())
        self.assertEqual((666, flags_target), backend.target())
        self.assertEqual(backend.object_id, 'xyzzy')


if __name__ == '__main__':
    unittest.main()
