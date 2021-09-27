# standard imports
import logging
import uuid

# imports
from chainlib.chain import ChainSpec

# local imports
from chainsyncer.db.models.sync import BlockchainSync
from chainsyncer.db.models.filter import BlockchainSyncFilter
from chainsyncer.db.models.base import SessionBase
from .base import Backend

logg = logging.getLogger().getChild(__name__)


class SQLBackend(Backend):
    """Interface to block and transaction sync state.

    :param chain_spec: Chain spec for the chain that syncer is running for.
    :type chain_spec: cic_registry.chain.ChainSpec
    :param object_id: Unique database record id for the syncer session.
    :type object_id: int
    """

    base = None

    def __init__(self, chain_spec, object_id):
        super(SQLBackend, self).__init__(int(object_id))
        self.db_session = None
        self.db_object = None
        self.db_object_filter = None
        self.chain_spec = chain_spec
        self.connect()
        self.disconnect()


    @classmethod
    def setup(cls, dsn, debug=False, pool_size=0, *args, **kwargs):
        """Set up database connection backend.

        :param dsn: Database connection string
        :type dsn: str
        :param debug: Activate debug output in sql engine
        :type debug: bool
        :param pool_size: Size of transaction pool
        :type pool_size: int
        """
        if cls.base == None:
            cls.base = SessionBase
            cls.base.connect(dsn, debug=debug, pool_size=pool_size)


    def connect(self):
        """Loads the state of the syncer session by the given database record id.

        :raises ValueError: Database syncer object with given id does not exist
        :rtype: sqlalchemy.orm.session.Session
        :returns: Database session object
        """
        if self.db_session == None:
            self.db_session = SessionBase.create_session()

        q = self.db_session.query(BlockchainSync)
        q = q.filter(BlockchainSync.id==self.object_id)
        self.db_object = q.first()

        if self.db_object != None:
            qtwo = self.db_session.query(BlockchainSyncFilter)
            qtwo = qtwo.join(BlockchainSync)
            qtwo = qtwo.filter(BlockchainSync.id==self.db_object.id)
            self.db_object_filter = qtwo.first()

        if self.db_object == None:
            raise ValueError('sync entry with id {} not found'.format(self.object_id))

        return self.db_session


    def disconnect(self):
        """Commits state of sync to backend and frees connection resources.
        """
        if self.db_session == None:
            return

        if self.db_object_filter != None:
            self.db_session.add(self.db_object_filter)
        self.db_session.add(self.db_object)
        self.db_session.commit()
        self.db_session.close()
        self.db_session = None
       
   

    def get(self):
        """Get the current state of the syncer cursor.

        :rtype: tuple
        :returns: Block height / tx index tuple, and filter flags value
        """
        self.connect()
        pair = self.db_object.cursor()
        (filter_state, count, digest) = self.db_object_filter.cursor()
        self.disconnect()
        return (pair, filter_state,)
   

    def set(self, block_height, tx_height):
        """Update the state of the syncer cursor.

        :param block_height: New block height
        :type block_height: int
        :param tx_height: New transaction height in block
        :type tx_height: int
        :returns: Block height / tx index tuple, and filter flags value
        :rtype: tuple
        """
        self.connect()
        pair = self.db_object.set(block_height, tx_height)
        (filter_state, count, digest)= self.db_object_filter.cursor()
        self.disconnect()
        return (pair, filter_state,)


    def start(self):
        """Get the initial state of the syncer cursor.

        :returns: Block height / tx index tuple, and filter flags value
        :rtype: tuple
        """
        self.connect()
        pair = self.db_object.start()
        (filter_state, count, digest) = self.db_object_filter.start()
        self.disconnect()
        return (pair, filter_state,)

    
    def target(self):
        """Get the target state (upper bound of sync) of the syncer cursor.

        :returns: Block height and filter flags value
        :rtype: tuple
        """
        self.connect()
        target = self.db_object.target()
        (filter_target, count, digest) = self.db_object_filter.target()
        self.disconnect()
        return (target, filter_target,)


    @staticmethod
    def custom(chain_spec, target_block, block_offset=0, tx_offset=0, flags=0, flag_count=0, *args, **kwargs):
        """

        :param flags: flags bit field
        :type flags: bytes
        :param flag_count: number of flags in bit field
        :type flag_count: 
        """
        session = SessionBase.create_session()
        o = BlockchainSync(str(chain_spec), block_offset, tx_offset, target_block)
        session.add(o)
        session.commit()
        object_id = o.id
  
        of = BlockchainSyncFilter(o, flag_count, flags, kwargs.get('flags_digest'))
        session.add(of)
        session.commit()

        session.close()

        return SQLBackend(chain_spec, object_id)


    @staticmethod
    def first(chain_spec):
        """Returns the model object of the most recent syncer in backend.

        :param chain_spec: Chain spec of chain that syncer is running for.
        :type chain_spec: cic_registry.chain.ChainSpec
        :returns: Last syncer object 
        :rtype: cic_eth.db.models.BlockchainSync
        """
        object_id = BlockchainSync.first(str(chain_spec))
        if object_id == None:
            return None
        return SQLBackend(chain_spec, object_id)



    @staticmethod
    def initial(chain_spec, target_block_height, start_block_height=0):
        """Creates a new syncer session and commit its initial state to backend.

        :param chain_spec: Chain spec of chain that syncer is running for
        :type chain_spec: cic_registry.chain.ChainSpec
        :param target_block_height: Target block height
        :type target_block_height: int
        :param start_block_height: Start block height
        :type start_block_height: int
        :raises ValueError: Invalid start/target specification
        :returns: New syncer object 
        :rtype: cic_eth.db.models.BlockchainSync
        """
        if start_block_height >= target_block_height:
            raise ValueError('start block height must be lower than target block height')
        object_id = None
        session = SessionBase.create_session()
        o = BlockchainSync(str(chain_spec), start_block_height, 0, target_block_height)
        session.add(o)
        session.commit()
        object_id = o.id

        of = BlockchainSyncFilter(o)
        session.add(of)
        session.commit()

        session.close()

        return SQLBackend(chain_spec, object_id)


    @staticmethod
    def resume(chain_spec, block_height):
        """Retrieves and returns all previously unfinished syncer sessions.

        If a previous open-ended syncer is found, a new syncer will be generated to sync from where that syncer left off until the block_height given as argument.

        :param chain_spec: Chain spec of chain that syncer is running for
        :type chain_spec: cic_registry.chain.ChainSpec
        :param block_height: Target block height for previous live syncer
        :type block_height: int
        :returns: Syncer objects of unfinished syncs
        :rtype: list of cic_eth.db.models.BlockchainSync
        """
        syncers = []

        session = SessionBase.create_session()

        object_id = None

        highest_unsynced_block = 0
        highest_unsynced_tx = 0
        object_id = BlockchainSync.get_last(session=session, live=False)
        if object_id != None:
            q = session.query(BlockchainSync)
            o = q.get(object_id)
            (highest_unsynced_block, highest_unsynced_index) = o.cursor()
        
        object_ids = BlockchainSync.get_unsynced(session=session)
        session.close()

        for object_id in object_ids:
            s = SQLBackend(chain_spec, object_id)
            logg.debug('resume unfinished {}'.format(s))
            syncers.append(s)

        session = SessionBase.create_session()

        last_live_id = BlockchainSync.get_last(session=session)
        if last_live_id != None:

            q = session.query(BlockchainSync)
            o = q.get(last_live_id)

            (block_resume, tx_resume) = o.cursor()
            session.flush()

            #if block_height != block_resume:
            if highest_unsynced_block < block_resume: 

                q = session.query(BlockchainSyncFilter)
                q = q.filter(BlockchainSyncFilter.chain_sync_id==last_live_id)
                of = q.first()
                (flags, count, digest) = of.cursor()

                session.flush()

                o = BlockchainSync(str(chain_spec), block_resume, tx_resume, block_height)
                session.add(o)
                session.flush()
                object_id = o.id

                of = BlockchainSyncFilter(o, count, flags, digest)
                session.add(of)
                session.commit()

                backend = SQLBackend(chain_spec, object_id)
                syncers.append(backend)

                logg.debug('last live session resume {}'.format(backend))

        session.close()

        return syncers


    @staticmethod
    def live(chain_spec, block_height):
        """Creates a new open-ended syncer session starting at the given block height.

        :param chain: Chain spec of chain that syncer is running for.
        :type chain: cic_registry.chain.ChainSpec
        :param block_height: Start block height
        :type block_height: int
        :returns: "Live" syncer object
        :rtype: cic_eth.db.models.BlockchainSync
        """
        session = SessionBase.create_session()

        o = BlockchainSync(str(chain_spec), block_height, 0, None)
        session.add(o)
        session.flush()
        object_id = o.id

        of = BlockchainSyncFilter(o)
        session.add(of)
        session.commit()

        session.close()

        return SQLBackend(chain_spec, object_id)


    def register_filter(self, name):
        """Add filter to backend.

        No check is currently implemented to enforce that filters are the same for existing syncers. Care must be taken by the caller to avoid inconsistencies. 

        :param name: Name of filter
        :type name: str
        """
        self.connect()
        if self.db_object_filter == None:
            self.db_object_filter = BlockchainSyncFilter(self.db_object)
        self.db_object_filter.add(name)
        self.db_session.add(self.db_object_filter)
        self.disconnect()


    def begin_filter(self, n):
        """Marks start of execution of the filter indexed by the corresponding bit.

        :param n: Filter index
        :type n: int
        """
        self.connect()
        self.db_object_filter.set(n)
        self.db_session.add(self.db_object_filter)
        self.db_session.commit()
        self.disconnect()


    def complete_filter(self, n):
        self.connect()
        self.db_object_filter.release(check_bit=n)
        self.db_session.add(self.db_object_filter)
        self.db_session.commit()
        self.disconnect()


    def reset_filter(self):
        """Reset all filter states.
        """
        self.connect()
        self.db_object_filter.clear()
        self.disconnect()
