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
    """Logger-only callback for pre- and post processing.

    :param block: Block object
    :type block: chainlib.block.Block
    :param tx: Transaction object
    :type tx: chainlib.tx.Tx
    """
    logg.debug('noop callback ({},{})'.format(block, tx))


class Syncer:
    """Base class for syncer implementations.

    :param backend: Syncer state backend
    :type backend: chainsyncer.backend.base.Backend implementation
    :param chain_interface: Chain interface implementation 
    :type chain_interface: chainlib.interface.ChainInterface implementation
    :param pre_callback: Function to call before polling. Function will receive no arguments.
    :type pre_callback: function 
    :param block_callback: Function to call before processing txs in a retrieved block. Function should have signature as chainsyncer.driver.base.noop_callback
    :type block_callback: function
    :param post_callback: Function to call after polling. Function will receive no arguments.
    :type post_callback: function 
    """

    running_global = True
    """If set to false syncer will terminate polling loop."""
    yield_delay=0.005
    """Delay between each processed block."""
    signal_request = [signal.SIGINT, signal.SIGTERM]
    """Signals to catch to request shutdown."""
    signal_set = False
    """Whether shutdown signal has been received."""
    name = 'base'
    """Syncer name, to be overriden for each extended implementation."""

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
        """Set syncer to terminate as soon as possible.
        """
        logg.info('termination requested!')
        Syncer.running_global = False
        self.running = False


    def add_filter(self, f):
        """Add filter to be processed for each transaction.

        :param f: Filter
        :type f: Object instance implementing signature as in chainsyncer.filter.NoopFilter.filter
        """
        self.filter.add(f)
        self.backend.register_filter(str(f))


    def process_single(self, conn, block, tx):
        """Set syncer backend cursor to the given transaction index and block height, and apply all registered filters on transaction.

        :param conn: RPC connection instance
        :type conn: chainlib.connection.RPCConnection
        :param block: Block object
        :type block: chainlib.block.Block
        :param block: Transaction object
        :type block: chainlib.tx.Tx
        """
        self.backend.set(block.number, tx.index)
        self.filter.apply(conn, block, tx)


    def loop(self, interval, conn):
        raise NotImplementedError()
  

    def process(self, conn, block):
        raise NotImplementedError()


    def get(self, conn):
        raise NotImplementedError()


    def __str__(self):
        return 'syncer "{}" {}'.format(
                self.name,
                self.backend,
                )
