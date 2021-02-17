# standard imports
import hashlib

# third-party imports
from sqlalchemy import Column, String, Integer, BLOB
from sqlalchemy.ext.hybrid import hybrid_property, hybrid_method

# local imports
from .base import SessionBase


zero_digest = '{:<064s'.format('0')


class BlockchainSyncFilter(SessionBase):

    __tablename__ = 'chain_sync_filter'

    chain_sync_id = Column(Integer, ForeignKey='chain_sync.id')
    flags = Column(BLOB)
    digest = Column(String)
    count = Column(Integer)

    @staticmethod
    def set(self, names):


    def __init__(self, names, chain_sync, digest=None):
        if len(names) == 0:
            digest = zero_digest
        elif digest == None:
            h = hashlib.new('sha256')
            for n in names:
                h.update(n.encode('utf-8') + b'\x00')
            z = h.digest()
            digest = z.hex()
        self.digest = digest
        self.count = len(names)
        self.flags = bytearray((len(names) -1 ) / 8 + 1)
        self.chain_sync_id = chain_sync.id
