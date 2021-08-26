# standard imports
import uuid
import logging
import time
import signal
import json

# external imports
from chainlib.error import JSONRPCException

# local imports
from chainsyncer.filter import SyncFilter
from chainsyncer.error import (
        SyncDone,
        NoBlockForYou,
    )

logg = logging.getLogger(__name__)


def noop_callback(block, tx):
    logg.debug('noop callback ({},{})'.format(block, tx))


class Syncer:

    running_global = True
    yield_delay=0.005
    signal_request = [signal.SIGINT, signal.SIGTERM]
    signal_set = False
    name = 'base'

    def __init__(self, backend, chain_interface, pre_callback=None, block_callback=None, post_callback=None):
        self.chain_interface = chain_interface
        self.cursor = None
        self.running = True
        self.backend = backend
        self.filter = SyncFilter(backend)
        self.block_callback = block_callback
        self.pre_callback = pre_callback
        self.post_callback = post_callback
        if not Syncer.signal_set:
            for sig in Syncer.signal_request:
                signal.signal(sig, self.__sig_terminate)
            Syncer.signal_set = True


    def __sig_terminate(self, sig, frame):
        logg.warning('got signal {}'.format(sig))
        self.terminate()


    def terminate(self):
        logg.info('termination requested!')
        Syncer.running_global = False
        Syncer.running = False


    def add_filter(self, f):
        self.filter.add(f)
        self.backend.register_filter(str(f))


    def process_single(self, conn, block, tx):
        self.backend.set(block.number, tx.index)
        self.filter.apply(conn, block, tx)

    
    def __str__(self):
        return 'syncer "{}" {}'.format(
                self.name,
                self.backend,
                )
