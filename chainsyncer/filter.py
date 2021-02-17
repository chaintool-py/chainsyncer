# standard imports
import logging

logg = logging.getLogger(__name__)

class SyncFilter:

    def __init__(self, safe=True):
        self.safe = safe
        self.filters = []


    def add(self, fltr):
        if getattr(fltr, 'filter') == None:
            raise ValueError('filter object must implement have method filter')
        logg.debug('added filter {}'.format(str(fltr)))

        self.filters.append(fltr)
   

    def apply(self, conn, block, tx):
        for f in self.filters:
            logg.debug('applying filter {}'.format(str(f)))
            f.filter(conn, block, tx)


class NoopFilter(SyncFilter):
    
    def filter(self, conn, block, tx):
        logg.debug('noop filter :received\n{} {}'.format(block, tx))


    def __str__(self):
        return 'noopfilter'
