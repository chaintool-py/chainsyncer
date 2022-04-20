# standard imports
import os
import logging

# local imports
from shep.persist import PersistedState
from shep.error import StateInvalid
from chainsyncer.filter import FilterState
from chainsyncer.error import (
        LockError,
        FilterDone,
        InterruptError,
        IncompleteFilterError,
        SyncDone,
        )

logg = logging.getLogger(__name__)


def sync_state_serialize(block_height, tx_index, block_target):
    b = block_height.to_bytes(4, 'big')
    b += tx_index.to_bytes(4, 'big')
    b += block_target.to_bytes(4, 'big', signed=True)
    return b


def sync_state_deserialize(b):
    block_height = int.from_bytes(b[:4], 'big')
    tx_index = int.from_bytes(b[4:8], 'big')
    block_target = int.from_bytes(b[8:], 'big', signed=True)
    return (block_height, tx_index, block_target,)


# NOT thread safe
class SyncItem:
    
    def __init__(self, offset, target, sync_state, filter_state, started=False, ignore_invalid=False):
        self.offset = offset
        self.target = target
        self.sync_state = sync_state
        self.filter_state = filter_state
        self.state_key = str(offset)

        logg.debug('get key {}'.format(self.state_key))
        v = self.sync_state.get(self.state_key)

        (self.cursor, self.tx_cursor, self.target) = sync_state_deserialize(v)

        if self.filter_state.state(self.state_key) & self.filter_state.from_name('LOCK') and not ignore_invalid:
            raise LockError(self.state_key)

        self.count = len(self.filter_state.all(pure=True)) - 4
        self.skip_filter = False
        if self.count == 0:
            self.skip_filter = True
        elif not started:
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

        
    def next(self, advance_block=False):
        v = self.sync_state.state(self.state_key)
        if v == self.sync_state.DONE:
            raise SyncDone(self.target)
        elif v == self.sync_state.NEW:
            self.sync_state.next(self.state_key)

        v = self.sync_state.get(self.state_key)
        (block_number, tx_index, target) = sync_state_deserialize(v)
        if advance_block:
            block_number += 1
            tx_index = 0
            if self.target >= 0 and block_number > self.target:
                self.sync_state.move(self.state_key, self.sync_state.DONE)
                raise SyncDone(self.target)
        else:
            tx_index += 1

        self.cursor = block_number
        self.tx_cursor = tx_index

        b = sync_state_serialize(block_number, tx_index, target)
        self.sync_state.replace(self.state_key, b)


    def __find_advance(self):
        v = self.filter_state.state(self.state_key)


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
            raise FilterDone()
        self.filter_state.set(self.state_key, self.filter_state.from_name('LOCK'))
       

    def release(self, interrupt=False):
        if self.skip_filter:
            return False
        if interrupt:
            self.filter_state.unset(self.state_key, self.filter_state.from_name('LOCK'))
            self.filter_state.set(self.state_key, self.filter_state.from_name('INTERRUPT'))
            self.filter_state.set(self.state_key, self.filter_state.from_name('DONE'))
            return False

        state = self.filter_state.state(self.state_key)
        if state & self.filter_state.from_name('LOCK') == 0:
            raise LockError('release attempt on {} when state unlocked'.format(self.state_key))
        self.filter_state.unset(self.state_key, self.filter_state.from_name('LOCK'))
        try:
            c = self.filter_state.peek(self.state_key)
            logg.debug('peeked {}'.format(c))
        except StateInvalid:
            self.filter_state.set(self.state_key, self.filter_state.from_name('DONE'))
            return False
        return True
       

    def __str__(self):
        return 'syncitem offset {} target {} cursor {}'.format(self.offset, self.target, self.cursor)


class SyncStore:

    def __init__(self, path, session_id=None):
        self.session_id = None
        self.session_path = None
        self.is_default = False
        self.first = False
        self.target = None
        self.items = {}
        self.item_keys = []
        self.started = False
        self.thresholds = []
        self.default_path = os.path.join(path, 'default')

        if session_id == None:
            self.session_path = os.path.realpath(self.default_path)
            self.is_default = True
        else:
            if session_id == 'default':
                self.is_default = True
            given_path = os.path.join(path, session_id)
            self.session_path = os.path.realpath(given_path)


    def setup_sync_state(self, factory, event_callback):
        self.state = PersistedState(factory.add, 2, event_callback=event_callback)
        self.state.add('SYNC')
        self.state.add('DONE')


    def setup_filter_state(self, factory, event_callback):
        filter_state_backend = PersistedState(factory.add, 0, check_alias=False, event_callback=event_callback)
        self.filter_state = FilterState(filter_state_backend, scan=factory.ls)
        self.filters = []


    def set_target(self, v):
        pass


    def get_target(self):
        return None


    def register(self, fltr):
        self.filters.append(fltr)
        self.filter_state.register(fltr)


    def start(self, offset=0, target=-1):
        if self.started:
            return

        self.load(target)

        if self.first:
            state_bytes = sync_state_serialize(offset, 0, target)
            block_number_str = str(offset)
            self.state.put(block_number_str, state_bytes)
            self.filter_state.put(block_number_str)
            o = SyncItem(offset, target, self.state, self.filter_state)
            self.items[offset] = o
            self.item_keys.append(offset)
        elif offset > 0:
            logg.warning('block number argument {} for start ignored for already initiated sync {}'.format(offset, self.session_id))
        self.started = True

        self.item_keys.sort()


    def stop(self, item):
        if item.target == -1:
            state_bytes = sync_state_serialize(item.cursor, 0, item.cursor)
            self.state.replace(str(item.offset), state_bytes)
            self.filter_state.put(str(item.cursor))

            SyncItem(item.offset, -1, self.state, self.filter_state)
            logg.info('New sync state start at block number {} for next head sync backfill'.format(item.cursor))

            self.state.move(item.state_key, self.state.DONE)

            state_bytes = sync_state_serialize(item.cursor, 0, -1)
            self.state.put(str(item.cursor), state_bytes)


    def load(self, target):
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
            o = SyncItem(block_number, item_target, self.state, self.filter_state, started=True)
            self.items[block_number] = o
            self.item_keys.append(block_number)
            logg.info('added existing {}'.format(o))

        self.get_target()
        
        if len(thresholds) == 0:
            if self.target != None:
                logg.warning('sync "{}" is already done, nothing to do'.format(self.session_id))
            else:
                logg.info('syncer first run target {}'.format(target))
                self.first = True
                self.set_target(target)


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
