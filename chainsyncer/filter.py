# standard imports
import logging

# local imports
from .error import BackendError

logg = logging.getLogger(__name__)


class SyncFilter:
    """Manages the collection of filters on behalf of a specific backend.

    A filter is a pluggable piece of code to execute for every transaction retrieved by the syncer. Filters are executed in the sequence they were added to the instance.

    :param backend: Syncer backend to apply filter state changes to
    :type backend: chainsyncer.backend.base.Backend implementation
    """

    def __init__(self, backend):
        self.filters = []
        self.backend = backend


    def add(self, fltr):
        """Add a filter instance.

        :param fltr: Filter instance.
        :type fltr: Object instance implementing signature as in chainsyncer.filter.NoopFilter.filter
        :raises ValueError: Object instance is incorrect implementation
        """
        if getattr(fltr, 'filter') == None:
            raise ValueError('filter object must implement have method filter')
        logg.debug('added filter "{}"'.format(str(fltr)))

        self.filters.append(fltr)


    def __apply_one(self, fltr, idx, conn, block, tx, session):
        self.backend.begin_filter(idx)
        fltr.filter(conn, block, tx, session)
        self.backend.complete_filter(idx)


    def apply(self, conn, block, tx):
        """Apply all registered filters on the given transaction.

        :param conn: RPC Connection, will be passed to the filter method
        :type conn: chainlib.connection.RPCConnection
        :param block: Block object
        :type block: chainlib.block.Block
        :param tx: Transaction object
        :type tx: chainlib.tx.Tx
        :raises BackendError: Backend connection failed
        """
        session = None
        try:
            session = self.backend.connect()
        except TimeoutError as e:
            self.backend.disconnect()
            raise BackendError('database connection fail: {}'.format(e))
        i = 0
        (pair, flags) = self.backend.get()
        for f in self.filters:
            if not self.backend.check_filter(i, flags):
                logg.debug('applying filter {} {}'.format(str(f), flags))
                self.__apply_one(f, i, conn, block, tx, session)
            else:
                logg.debug('skipping previously applied filter {} {}'.format(str(f), flags))
            i += 1

        self.backend.disconnect()


class NoopFilter:
    """A noop implemenation of a sync filter.

    Logs the filter inputs at debug log level.
    """
    
    def filter(self, conn, block, tx, db_session=None):
        """Filter method implementation:

        :param conn: RPC Connection, will be passed to the filter method
        :type conn: chainlib.connection.RPCConnection
        :param block: Block object
        :type block: chainlib.block.Block
        :param tx: Transaction object
        :type tx: chainlib.tx.Tx
        :param db_session: Backend session object
        :type db_session: varies
        """
        logg.debug('noop filter :received\n{} {} {}'.format(block, tx, id(db_session)))


    def __str__(self):
        return 'noopfilter'
