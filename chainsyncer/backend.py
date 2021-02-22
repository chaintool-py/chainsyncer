# standard imports
import logging
import uuid

# third-party imports
from chainlib.chain import ChainSpec

# local imports
from chainsyncer.db.models.sync import BlockchainSync
from chainsyncer.db.models.filter import BlockchainSyncFilter
from chainsyncer.db.models.base import SessionBase

logg = logging.getLogger()


class SyncerBackend:
    """Interface to block and transaction sync state.

    :param chain_spec: Chain spec for the chain that syncer is running for.
    :type chain_spec: cic_registry.chain.ChainSpec
    :param object_id: Unique id for the syncer session.
    :type object_id: number
    """
    def __init__(self, chain_spec, object_id):
        self.db_session = None
        self.db_object = None
        self.db_object_filter = None
        self.chain_spec = chain_spec
        self.object_id = object_id
        self.connect()
        self.disconnect()


    def connect(self):
        """Loads the state of the syncer session with the given id.
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


    def disconnect(self):
        """Commits state of sync to backend.
        """
        if self.db_object_filter != None:
            self.db_session.add(self.db_object_filter)
        self.db_session.add(self.db_object)
        self.db_session.commit()
        self.db_session.close()
        self.db_session = None
       

    def chain(self):
        """Returns chain spec for syncer

        :returns: Chain spec
        :rtype chain_spec: cic_registry.chain.ChainSpec
        """
        return self.chain_spec
   

    def get(self):
        """Get the current state of the syncer cursor.

        :returns: Block and block transaction height, respectively
        :rtype: tuple
        """
        self.connect()
        pair = self.db_object.cursor()
        (filter_state, count, digest) = self.db_object_filter.cursor()
        self.disconnect()
        return (pair, filter_state,)
   

    def set(self, block_height, tx_height):
        """Update the state of the syncer cursor
        :param block_height: Block height of cursor
        :type block_height: number
        :param tx_height: Block transaction height of cursor
        :type tx_height: number
        :returns: Block and block transaction height, respectively
        :rtype: tuple
        """
        self.connect()
        pair = self.db_object.set(block_height, tx_height)
        self.db_object_filter.clear()
        (filter_state, count, digest)= self.db_object_filter.cursor()
        self.disconnect()
        return (pair, filter_state,)


    def start(self):
        """Get the initial state of the syncer cursor.

        :returns: Initial block and block transaction height, respectively
        :rtype: tuple
        """
        self.connect()
        pair = self.db_object.start()
        (filter_state, count, digest) = self.db_object_filter.start()
        self.disconnect()
        return (pair, filter_state,)

    
    def target(self):
        """Get the target state (upper bound of sync) of the syncer cursor.

        :returns: Target block height
        :rtype: number
        """
        self.connect()
        target = self.db_object.target()
        (filter_target, count, digest) = self.db_object_filter.target()
        self.disconnect()
        return (target, filter_target,)


    @staticmethod
    def first(chain_spec):
        """Returns the model object of the most recent syncer in backend.

        :param chain: Chain spec of chain that syncer is running for.
        :type chain: cic_registry.chain.ChainSpec
        :returns: Last syncer object 
        :rtype: cic_eth.db.models.BlockchainSync
        """
        #return BlockchainSync.first(str(chain_spec))
        object_id = BlockchainSync.first(str(chain_spec))
        if object_id == None:
            return None
        return SyncerBackend(chain_spec, object_id)



    @staticmethod
    def initial(chain_spec, target_block_height, start_block_height=0):
        """Creates a new syncer session and commit its initial state to backend.

        :param chain: Chain spec of chain that syncer is running for.
        :type chain: cic_registry.chain.ChainSpec
        :param block_height: Target block height
        :type block_height: number
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

        return SyncerBackend(chain_spec, object_id)


    @staticmethod
    def resume(chain_spec, block_height):
        """Retrieves and returns all previously unfinished syncer sessions.


        :param chain_spec: Chain spec of chain that syncer is running for.
        :type chain_spec: cic_registry.chain.ChainSpec
        :param block_height: Target block height
        :type block_height: number
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
        
        for object_id in BlockchainSync.get_unsynced(session=session):
            logg.debug('block syncer resume added previously unsynced sync entry id {}'.format(object_id))
            s = SyncerBackend(chain_spec, object_id)
            syncers.append(s)

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

                syncers.append(SyncerBackend(chain_spec, object_id))

                logg.debug('block syncer resume added new sync entry from previous run id {}, start{}:{} target {}'.format(object_id, block_resume, tx_resume, block_height))

        session.close()

        return syncers


    @staticmethod
    def live(chain_spec, block_height):
        """Creates a new open-ended syncer session starting at the given block height.

        :param chain: Chain spec of chain that syncer is running for.
        :type chain: cic_registry.chain.ChainSpec
        :param block_height: Target block height
        :type block_height: number
        :returns: "Live" syncer object
        :rtype: cic_eth.db.models.BlockchainSync
        """
        object_id = None
        session = SessionBase.create_session()

        o = BlockchainSync(str(chain_spec), block_height, 0, None)
        session.add(o)
        session.flush()
        object_id = o.id

        of = BlockchainSyncFilter(o)
        session.add(of)
        session.commit()

        session.close()

        return SyncerBackend(chain_spec, object_id)


    def register_filter(self, name):
        self.connect()
        if self.db_object_filter == None:
            self.db_object_filter = BlockchainSyncFilter(self.db_object)
        self.db_object_filter.add(name)
        self.db_session.add(self.db_object_filter)
        self.disconnect()


    def complete_filter(self, n):
        self.connect()
        self.db_object_filter.set(n)
        self.disconnect()
        


class MemBackend:

    def __init__(self, chain_spec, object_id):
        self.object_id = object_id
        self.chain_spec = chain_spec
        self.block_height = 0
        self.tx_height = 0
        self.flags = 0
        self.db_session = None


    def connect(self):
        pass


    def disconnect(self):
        pass


    def set(self, block_height, tx_height):
        logg.debug('stateless backend received {} {}'.format(block_height, tx_height))
        self.block_height = block_height
        self.tx_height = tx_height


    def get(self):
        return (self.block_height, self.tx_height)
