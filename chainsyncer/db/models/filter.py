# standard imports
import logging
import hashlib

# external imports
from sqlalchemy import Column, String, Integer, BLOB, ForeignKey
from sqlalchemy.ext.hybrid import hybrid_property, hybrid_method

# local imports
from .base import SessionBase
from .sync import BlockchainSync

zero_digest = bytearray(32)
logg = logging.getLogger(__name__)


class BlockchainSyncFilter(SessionBase):

    __tablename__ = 'chain_sync_filter'

    chain_sync_id = Column(Integer, ForeignKey('chain_sync.id'))
    flags_start = Column(BLOB)
    flags = Column(BLOB)
    digest = Column(BLOB)
    count = Column(Integer)


    def __init__(self, chain_sync, count=0, flags=None, digest=zero_digest):
        self.digest = digest
        self.count = count

        if flags == None:
            flags = bytearray(0)
        self.flags_start = flags
        self.flags = flags

        self.chain_sync_id = chain_sync.id


    def add(self, name):
        h = hashlib.new('sha256')
        h.update(self.digest)
        h.update(name.encode('utf-8'))
        z = h.digest()

        old_byte_count = int((self.count - 1) / 8 + 1)
        new_byte_count = int((self.count) / 8 + 1)

        logg.debug('old new {} {}'.format(old_byte_count, new_byte_count))
        if old_byte_count != new_byte_count:
            self.flags = bytearray(1) + self.flags
        self.count += 1
        self.digest = z


    def start(self):
        return int.from_bytes(self.flags_start, 'big')


    def cursor(self):
        return int.from_bytes(self.flags, 'big')


    def clear(self):
        self.flags = 0


    def target(self):
        n = 0
        for i in range(self.count):
            n |= (1 << self.count) - 1
        return n


    def set(self, n):
        if n > self.count:
            raise IndexError('bit flag out of range')

        b = 1 << (n % 8)
        i = int((n - 1) / 8 + 1)
        if self.flags[i] & b > 0:
            SessionBase.release_session(session)
            raise AttributeError('Filter bit already set')
        flags = bytearray(self.flags)
        flags[i] |= b
        self.flags = flags
