# standard imports
import datetime

# third-party imports
from sqlalchemy import Column, String, Integer, DateTime, Text, Boolean
from sqlalchemy.ext.hybrid import hybrid_property, hybrid_method

# local imports
from .base import SessionBase


class BlockchainSync(SessionBase):
    """Syncer control backend.

    :param chain_str: Chain spec string representation
    :type chain_str: str
    :param block_start: Block number to start sync from
    :type block_start: number
    :param tx_start: Block transaction number to start sync from
    :type tx_start: number
    :param block_target: Block number to sync until, inclusive
    :type block_target: number
    """
    __tablename__ = 'chain_sync'

    blockchain = Column(String)
    """Chainspec string specifying the blockchain the syncer is running against."""
    block_start = Column(Integer)
    """The block height at the start of syncer."""
    tx_start = Column(Integer)
    """The transaction index at the start of syncer."""
    block_cursor = Column(Integer)
    """The block height for the current state of the syncer."""
    tx_cursor = Column(Integer)
    """The transaction index for the current state of the syncer."""
    block_target = Column(Integer)
    """The block height at which the syncer should terminate. Will be None for an open-ended syncer."""
    date_created = Column(DateTime, default=datetime.datetime.utcnow)
    """Datetime when syncer was first created."""
    date_updated = Column(DateTime)
    """Datetime of the latest update of the syncer state."""

    def __init__(self, chain_str, block_start, tx_start, block_target=None):
        self.blockchain = chain_str
        self.block_start = block_start
        self.tx_start = tx_start
        self.block_cursor = block_start
        self.tx_cursor = tx_start
        self.block_target = block_target
        self.date_created = datetime.datetime.utcnow()
        self.date_updated = datetime.datetime.utcnow()


    @staticmethod
    def first(chain_str, session=None):
        """Check if a sync session for the specified chain already exists.

        :param chain_str: Chain spec string representation
        :type chain_str: str
        :param session: Session to use. If not specified, a separate session will be created for this method only.
        :type session: sqlalchemy.orm.session.Sessoin
        :returns: Database primary key id of sync record, or None if insert failed
        :rtype: number
        """
        session = SessionBase.bind_session(session)

        q = session.query(BlockchainSync.id)
        q = q.filter(BlockchainSync.blockchain==chain_str)
        o = q.first()

        if o == None:
            SessionBase.release_session(session)
            return None

        sync_id = o.id

        SessionBase.release_session(session)

        return sync_id


    @staticmethod
    def get_last(session=None, live=True):
        """Get the most recent syncer record.

        If live is set, only the latest open-ended syncer will be returned.

        :param session: Session to use. If not specified, a separate session will be created for this method only.
        :type session: SqlAlchemy Session
        :param live: Match only open-ended syncers
        :type live: bool
        :returns: Syncer database id 
        :rtype: int
        """
        session = SessionBase.bind_session(session)

        q = session.query(BlockchainSync.id)
        if live:
            q = q.filter(BlockchainSync.block_target==None)
        else:
            q = q.filter(BlockchainSync.block_target!=None)
        q = q.order_by(BlockchainSync.date_created.desc())
        object_id = q.first()

        SessionBase.release_session(session)

        if object_id == None:
            return None

        return object_id[0]


    @staticmethod
    def get_unsynced(session=None):
        """Get previous bounded sync sessions that did not complete.

        :param session: Session to use. If not specified, a separate session will be created for this method only.
        :type session: SqlAlchemy Session
        :returns: Syncer database ids
        :rtype: list
        """
        unsynced = []
        local_session = False
        if session == None:
            session = SessionBase.create_session()
            local_session = True
        q = session.query(BlockchainSync.id)
        q = q.filter(BlockchainSync.block_target!=None)
        q = q.filter(BlockchainSync.block_cursor<BlockchainSync.block_target)
        q = q.order_by(BlockchainSync.date_created.asc())
        for u in q.all():
            unsynced.append(u[0])
        if local_session:
            session.close()

        return unsynced


    def set(self, block_height, tx_height):
        """Set the cursor height of the syncer instance.

        Only manipulates object, does not transaction or commit to backend.

        :param block_height: Block number
        :type block_height: number
        :param tx_height: Block transaction number
        :type tx_height: number
        :rtype: tuple
        :returns: Stored block height, transaction index
        """
        self.block_cursor = block_height
        self.tx_cursor = tx_height
        self.date_updated = datetime.datetime.utcnow()
        return (self.block_cursor, self.tx_cursor,)


    def cursor(self):
        """Get current state of cursor from cached instance.

        :returns: Block height, transaction index
        :rtype: tuple
        """
        return (self.block_cursor, self.tx_cursor)


    def start(self):
        """Get sync block start position from cached instance.

        :returns: Block height, transaction index
        :rtype: tuple
        """
        return (self.block_start, self.tx_start)


    def target(self):
        """Get sync block upper bound from cached instance.

        :returns: Block number. Returns None if syncer is open-ended.
        :rtype: int
        """
        return self.block_target


    def chain(self):
        """Get chain string representation for which the cached instance represents.
        """
        return self.blockchain


    def __str__(self):
        return """object_id: {}
start: {}:{}
cursor: {}:{}
target: {}
""".format(
        self.id,
        self.block_start,
        self.tx_start,
        self.block_cursor,
        self.tx_cursor,
        self.block_target,
        )
