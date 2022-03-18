# standard imports
import uuid
import os
import logging

# external imports
from shep.store.file import SimpleFileStoreFactory
from shep.persist import PersistedState
from shep.error import StateInvalid

# local imports 
from chainsyncer.state import SyncState
from chainsyncer.error import (
        LockError,
        FilterDone,
        InterruptError,
        IncompleteFilterError,
        SyncDone,
        )
logg = logging.getLogger(__name__)


# NOT thread safe
class SyncFsItem:
    
    def __init__(self, offset, target, sync_state, filter_state, started=False, ignore_invalid=False):
        self.offset = offset
        self.target = target
        self.sync_state = sync_state
        self.filter_state = filter_state
        self.state_key = str(offset)
        match_state = self.sync_state.NEW
        if started:
            match_state = self.sync_state.SYNC
        v = self.sync_state.get(self.state_key)
        self.cursor = int.from_bytes(v, 'big')

        if self.filter_state.state(self.state_key) & self.filter_state.from_name('LOCK') and not ignore_invalid:
            raise LockError(s)

        self.count = len(self.filter_state.all(pure=True)) - 3
        self.skip_filter = False
        if self.count == 0:
            self.skip_filter = True
        else:
            self.filter_state.move(self.state_key, self.filter_state.from_name('RESET'))


    def __check_done(self):
        if self.filter_state.state(self.state_key) & self.filter_state.from_name('INTERRUPT') > 0:
            raise InterruptError(self.state_key)
        if self.filter_state.state(self.state_key) & self.filter_state.from_name('DONE') > 0:
            raise FilterDone(self.state_key)


    def reset(self):
        if self.filter_state.state(self.state_key) & self.filter_state.from_name('LOCK') > 0:
            raise LockError('reset attempt on {} when state locked'.format(self.state_key))
        if self.filter_state.state(self.state_key) & self.filter_state.from_name('DONE') == 0:
            raise IncompleteFilterError('reset attempt on {} when incomplete'.format(self.state_key))
        self.filter_state.move(self.state_key, self.filter_state.from_name('RESET'))

        v = self.sync_state.get(self.state_key)
        block_number = int.from_bytes(v, 'big')
        block_number += 1
        if self.target >= 0 and block_number > self.target:
            raise SyncDone(self.target)

        v = block_number.to_bytes(4, 'big')
        self.sync_state.replace(self.state_key, v)
        

    def advance(self):
        if self.skip_filter:
            raise FilterDone()
        self.__check_done()

        if self.filter_state.state(self.state_key) & self.filter_state.from_name('LOCK') > 0:
            raise LockError('advance attempt on {} when state locked'.format(self.state_key))
        done = False
        try:
            self.filter_state.next(self.state_key)
        except StateInvalid:
            done = True
        if done:
            self.filter_state.set(self.state_key, self.filter_state.from_name('DONE'))
            raise FilterDone()
        self.filter_state.set(self.state_key, self.filter_state.from_name('LOCK'))
       

    def release(self, interrupt=False):
        if self.skip_filter:
            raise FilterDone()
        if interrupt:
            self.filter_state.unset(self.state_key, self.filter_state.from_name('LOCK'))
            self.filter_state.set(self.state_key, self.filter_state.from_name('INTERRUPT'))
            self.filter_state.set(self.state_key, self.filter_state.from_name('DONE'))
            return

        state = self.filter_state.state(self.state_key)
        if state & self.filter_state.from_name('LOCK') == 0:
            raise LockError('release attempt on {} when state unlocked'.format(self.state_key))
        self.filter_state.unset(self.state_key, self.filter_state.from_name('LOCK'))
        

    def __str__(self):
        return 'syncitem offset {} target {} cursor {}'.format(self.offset, self.target, self.cursor)



class SyncFsStore:

    def __init__(self, base_path, session_id=None):
        self.session_id = None
        self.session_path = None
        self.is_default = False
        self.first = False
        self.target = None
        self.items = {}
        self.item_keys = []
        self.started = False

        default_path = os.path.join(base_path, 'default')

        if session_id == None:
            self.session_path = os.path.realpath(default_path)
            self.is_default = True
        else:
            if session_id == 'default':
                self.is_default = True
            given_path = os.path.join(base_path, session_id)
            self.session_path = os.path.realpath(given_path)

        create_path = False
        try:
            os.stat(self.session_path)
        except FileNotFoundError:
            create_path = True

        if create_path:
            self.__create_path(base_path, default_path, session_id=session_id)

        logg.info('session id {} resolved {} path {}'.format(session_id, self.session_id, self.session_path))

        factory = SimpleFileStoreFactory(self.session_path, binary=True)
        self.state = PersistedState(factory.add, 2)
        self.state.add('SYNC')
        self.state.add('DONE')

        base_filter_path = os.path.join(self.session_path, 'filter')
        factory = SimpleFileStoreFactory(base_filter_path, binary=True)
        filter_state_backend = PersistedState(factory.add, 0, check_alias=False)
        self.filter_state = SyncState(filter_state_backend)
        self.filters = []
   

    def register(self, fltr):
        self.filters.append(fltr)
        self.filter_state.register(fltr)


    def __create_path(self, base_path, default_path, session_id=None):
        logg.debug('fs store path {} does not exist, creating'.format(self.session_path))
        if session_id == None:
            session_id = str(uuid.uuid4())
        self.session_path = os.path.join(base_path, session_id)
        os.makedirs(self.session_path)
        self.session_id = os.path.basename(self.session_path)
        
        if self.is_default:
            try:
                os.symlink(self.session_path, default_path)
            except FileExistsError:
                pass


    def __load(self, target):
        
        self.state.sync(self.state.NEW)
        self.state.sync(self.state.SYNC)

        thresholds_sync = []
        for v in self.state.list(self.state.SYNC):
            block_number = int(v)
            thresholds_sync.append(block_number)
            logg.debug('queue resume {}'.format(block_number))
        thresholds_new = []
        for v in self.state.list(self.state.NEW):
            block_number = int(v)
            thresholds_new.append(block_number)
            logg.debug('queue new range {}'.format(block_number))

        thresholds_sync.sort()
        thresholds_new.sort()
        thresholds = thresholds_sync + thresholds_new
        lim = len(thresholds) - 1
        for i in range(len(thresholds)):
            item_target = target
            if i < lim:
                item_target = thresholds[i+1] 
            o = SyncFsItem(block_number, item_target, self.state, self.filter_state, started=True)
            self.items[block_number] = o
            self.item_keys.append(block_number)
            logg.info('added {}'.format(o))

        fp = os.path.join(self.session_path, str(target))
        if len(thresholds) == 0:
            logg.info('syncer first run')
            self.first = True
            f = open(fp, 'w')
            f.write(str(target))
            f.close()

        f = open(fp, 'r')
        v = f.read()
        f.close()
        self.target = int(v)

        logg.debug('target {}'.format(self.target))


    def start(self, offset=0, target=-1):
        self.__load(target)

        if self.first:
            block_number = offset
            block_number_bytes = block_number.to_bytes(4, 'big')
            block_number_str = str(block_number)
            self.state.put(block_number_str, block_number_bytes)
            self.filter_state.put(block_number_str)
            o = SyncFsItem(block_number, target, self.state, self.filter_state)
            self.items[block_number] = o
            self.item_keys.append(block_number)
        elif offset > 0:
            logg.warning('block number argument {} for start ignored for already initiated sync {}'.format(offset, self.session_id))
        self.started = True

        self.item_keys.sort()


    def stop(self):
        if self.target == 0:
            block_number = self.height + 1
            block_number_bytes = block_number.to_bytes(4, 'big')
            self.state.put(str(block_number), block_number_bytes)


    def get(self, k):
        return self.items[k]


    def next_item(self):
        try:
            k = self.item_keys.pop(0)
        except IndexError:
            return None
        return self.items[k]


    def connect(self):
        self.filter_state.connect()


    def disconnect(self):
        self.filter_state.disconnect()
