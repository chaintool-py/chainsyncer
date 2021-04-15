# standard imports
import logging

# external imports
import sqlalchemy

# local imports
from .error import BackendError

logg = logging.getLogger(__name__)


class SyncFilter:

    def __init__(self, backend, safe=True):
        self.safe = safe
        self.filters = []
        self.backend = backend


    def add(self, fltr):
        if getattr(fltr, 'filter') == None:
            raise ValueError('filter object must implement have method filter')
        logg.debug('added filter "{}"'.format(str(fltr)))

        self.filters.append(fltr)
   

    def apply(self, conn, block, tx):
        session = None
        try:
            session = self.backend.connect()
        except sqlalchemy.exc.TimeoutError as e:
            self.backend.disconnect()
            raise BackendError('database connection fail: {}'.format(e))
        i = 0
        (pair, flags) = self.backend.get()
        for f in self.filters:
            i += 1
            if flags & (1 << (i - 1)) > 0:
                logg.debug('skipping previously applied filter {}'.format(str(f)))
                continue
            logg.debug('applying filter {}'.format(str(f)))
            f.filter(conn, block, tx, session)
            self.backend.complete_filter(i)
        if session != None:
            self.backend.disconnect()


class NoopFilter:
    
    def filter(self, conn, block, tx, db_session=None):
        logg.debug('noop filter :received\n{} {} {}'.format(block, tx, id(db_session)))


    def __str__(self):
        return 'noopfilter'
