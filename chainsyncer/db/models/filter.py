# standard imports
import logging
import hashlib

# external imports
from sqlalchemy import Column, String, Integer, LargeBinary, ForeignKey
from sqlalchemy.ext.hybrid import hybrid_property, hybrid_method

# local imports
from .base import SessionBase
from .sync import BlockchainSync
from chainsyncer.error import LockError

zero_digest = bytes(32).hex()
logg = logging.getLogger(__name__)


class BlockchainSyncFilter(SessionBase):
    """Sync filter sql backend database interface.

    :param chain_sync: BlockchainSync object to use as context for filter
    :type chain_sync: chainsyncer.db.models.sync.BlockchainSync
    :param count: Number of filters to track
    :type count: int
    :param flags: Filter flag value to instantiate record with
    :type flags: int
    :param digest: Filter digest as integrity protection when resuming session, 256 bits, in hex
    :type digest: str
    """

    __tablename__ = 'chain_sync_filter'

    chain_sync_id = Column(Integer, ForeignKey('chain_sync.id'))
    flags_start = Column(LargeBinary)
    flags = Column(LargeBinary)
    flags_lock = Column(Integer)
    digest = Column(String(64))
    count = Column(Integer)


    def __init__(self, chain_sync, count=0, flags=None, digest=None):
        if digest == None:
            digest = zero_digest
        self.digest = digest
        self.count = count

        if flags == None:
            flags = bytearray(0)
        else: 
            bytecount = int((count - 1) / 8 + 1) 
            flags = flags.to_bytes(bytecount, 'big')
        self.flags_start = flags
        self.flags = flags
        self.flags_lock = 0

        self.chain_sync_id = chain_sync.id


    @staticmethod
    def load(sync_id, session=None):
        q = session.query(BlockchainSyncFilter)
        q = q.filter(BlockchainSyncFilter.chain_sync_id==sync_id)
        o = q.first()
        if o.is_locked():
            raise LockError('locked state for flag {} of sync id {} must be manually resolved'.format(o.flags_lock))


    def add(self, name):
        """Add a new filter to the syncer record.

        The name of the filter is hashed with the current aggregated hash sum of previously added filters.

        :param name: Filter informal name
        :type name: str
        """
        h = hashlib.new('sha256')
        h.update(bytes.fromhex(self.digest))
        h.update(name.encode('utf-8'))
        z = h.digest()

        old_byte_count = int((self.count - 1) / 8 + 1)
        new_byte_count = int((self.count) / 8 + 1)

        if old_byte_count != new_byte_count:
            self.flags = bytearray(1) + self.flags
        self.count += 1
        self.digest = z.hex()


    def start(self):
        """Retrieve the initial filter state of the syncer.

        :rtype: tuple
        :returns: Filter flag value, filter count, filter digest
        """
        return (int.from_bytes(self.flags_start, 'big'), self.count, self.digest)


    def cursor(self):
        """Retrieve the current filter state of the syncer.

        :rtype: tuple
        :returns: Filter flag value, filter count, filter digest
        """
        return (int.from_bytes(self.flags, 'big'), self.count, self.digest)


    def target(self):
        """Retrieve the target filter state of the syncer.

        The target filter value will be the integer value when all bits are set for the filter count.

        :rtype: tuple
        :returns: Filter flag value, filter count, filter digest
        """

        n = 0
        for i in range(self.count):
            n |= (1 << self.count) - 1
        return (n, self.count, self.digest)


    def is_locked(self):
        return self.flags_lock > 0


    def clear(self):
        """Set current filter flag value to zero.
        """
        if self.is_locked():
            raise LockError('flag clear attempted when lock set at {}'.format(self.flags_lock))

        self.flags = bytearray(len(self.flags))


    def set(self, n):
        """Set the filter flag at given index.

        :param n: Filter flag index
        :type n: int
        :raises IndexError: Invalid flag index
        :raises AttributeError: Flag at index already set
        """
        if self.is_locked():
            raise LockError('flag set attempted when lock set at {}'.format(self.flags_lock))

        if n > self.count:
            raise IndexError('bit flag out of range')

        self.flags_lock = n

        b = 1 << (n % 8)
        i = int(n / 8)
        byte_idx = len(self.flags)-1-i
        if (self.flags[byte_idx] & b) > 0:
            raise AttributeError('Filter bit already set')
        flags = bytearray(self.flags)
        flags[byte_idx] |= b
        self.flags = flags


    def release(self, check_bit=0):
        if check_bit > 0:
            if self.flags_lock > 0 and self.flags_lock != check_bit:
                raise LockError('release attemped on explicit bit {}, but bit {} was locked'.format(check_bit, self.flags_lock))
        self.flags_lock = 0
