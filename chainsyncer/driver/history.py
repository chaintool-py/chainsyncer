# standard imports
import logging

# external imports
from chainlib.error import RPCException

# local imports
from .head import HeadSyncer
from chainsyncer.error import SyncDone
from chainlib.error import RPCException

logg = logging.getLogger(__name__)


class HistorySyncer(HeadSyncer):

    name = 'history'

    def __init__(self, backend, chain_interface, pre_callback=None, block_callback=None, post_callback=None):
        super(HeadSyncer, self).__init__(backend, chain_interface, pre_callback, block_callback, post_callback)
        self.block_target = None
        (block_number, flags) = self.backend.target()
        if block_number == None:
            raise AttributeError('backend has no future target. Use HeadSyner instead')
        self.block_target = block_number
        logg.debug('block target {}'.format(self.block_target))


    def get(self, conn):
        (height, flags) = self.backend.get()
        if self.block_target < height[0]:
            raise SyncDone(self.block_target)
        block_number = height[0]
        block_hash = []
        o = self.chain_interface.block_by_number(block_number)
        try:
            r = conn.do(o)
        # TODO: Disambiguate whether error is temporary or permanent, if permanent, SyncDone should be raised, because a historical sync is attempted into the future
        except RPCException:
            r = None
        if r == None:
            raise SyncDone() #NoBlockForYou()
        b = self.chain_interface.block_from_src(r)

        return b
