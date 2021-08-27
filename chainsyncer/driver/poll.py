# standard imports
import logging
import time

# local imports
from .base import Syncer
from chainsyncer.error import (
        SyncDone,
        NoBlockForYou,
        )

logg = logging.getLogger(__name__)



class BlockPollSyncer(Syncer):
    """Syncer driver implementation of chainsyncer.driver.base.Syncer that retrieves new blocks through polling.
    """

    name = 'blockpoll'

    def loop(self, interval, conn):
        """Indefinite loop polling the given RPC connection for new blocks in the given interval.

        :param interval: Seconds to wait for next poll after processing of previous poll has been completed.
        :type interval: int
        :param conn: RPC connection
        :type conn: chainlib.connection.RPCConnection
        :rtype: tuple
        :returns: See chainsyncer.backend.base.Backend.get
        """
        (pair, fltr) = self.backend.get()
        start_tx = pair[1]

        while self.running and Syncer.running_global:
            if self.pre_callback != None:
                self.pre_callback()
            #while True and Syncer.running_global:
            while True and self.running:
                if start_tx > 0:
                    start_tx -= 1
                    continue
                try:
                    block = self.get(conn)
                except SyncDone as e:
                    logg.info('all blocks sumitted for processing: {}'.format(e))
                    return self.backend.get()
                except NoBlockForYou as e:
                    break
# TODO: To properly handle this, ensure that previous request is rolled back
#                except sqlalchemy.exc.OperationalError as e:
#                    logg.error('database error: {}'.format(e))
#                    break

                if self.block_callback != None:
                    self.block_callback(block, None)

                last_block = block
                try:
                    self.process(conn, block)
                except IndexError:
                    self.backend.set(block.number + 1, 0)
                start_tx = 0
                time.sleep(self.yield_delay)
            if self.post_callback != None:
                self.post_callback()
            time.sleep(interval)
