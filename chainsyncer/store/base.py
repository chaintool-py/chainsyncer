# standard imports
import os
import logging

# local imports
from shep.persist import PersistedState
from shep import State
from shep.error import StateInvalid
from chainsyncer.filter import FilterState
from chainsyncer.error import (
        LockError,
        FilterDone,
        InterruptError,
        IncompleteFilterError,
        SyncDone,
        FilterInitializationError,
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
    
    def __init__(self, offset, target, sync_state, filter_state, started=False, ignore_lock=False):
        self.offset = offset
        self.target = target
        self.sync_state = sync_state
        self.filter_state = filter_state
        self.state_key = str(offset)

        v = self.sync_state.get(self.state_key)

        (self.cursor, self.tx_cursor, self.target) = sync_state_deserialize(v)

        filter_state = self.filter_state.state(self.state_key)
        if filter_state  & self.filter_state.from_name('LOCK') > 0 and not ignore_lock:
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


    def reset(self, check_incomplete=True):
        if check_incomplete:
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


    def advance(self, ignore_lock=False):
        if self.skip_filter:
            raise FilterDone()
        self.__check_done()

        if self.filter_state.state(self.state_key) & self.filter_state.from_name('LOCK') > 0:
            if ignore_lock:
                self.filter_state.unset(self.state_key, self.filter_state.from_name('LOCK'))
            else:
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
        if interrupt == True:
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
        self.session_id = session_id
        self.session_path = None
        self.is_default = False
        self.first = False
        self.target = None
        self.items = {}
        self.item_keys = []
        self.started = False
        self.thresholds = []
        self.session_path = path


    def setup_sync_state(self, factory=None, event_callback=None):
        if factory == None:
            self.state = State(2, event_callback=event_callback)
        else:
            self.state = PersistedState(factory.add, 2, event_callback=event_callback)
        self.state.add('SYNC')
        self.state.add('DONE')


    def setup_filter_state(self, factory=None, event_callback=None):
        if factory == None:
            filter_state_backend = State(0, check_alias=False, event_callback=event_callback)
            self.filter_state = FilterState(filter_state_backend)
        else:
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


    def start(self, offset=0, target=-1, ignore_lock=False):
        if self.started:
            return

        self.save_filter_list() 
        
        self.load(target, ignore_lock=ignore_lock)

        if self.first:
            state_bytes = sync_state_serialize(offset, 0, target)
            block_number_str = str(offset)
            self.state.put(block_number_str, contents=state_bytes)
            self.filter_state.put(block_number_str)
            o = SyncItem(offset, target, self.state, self.filter_state, ignore_lock=ignore_lock)
            k = str(offset)
            self.items[k] = o
            self.item_keys.append(k)
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
            self.state.put(str(item.cursor), contents=state_bytes)


    def load(self, target, ignore_lock=False):
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
            o = SyncItem(block_number, item_target, self.state, self.filter_state, started=True, ignore_lock=ignore_lock)
            k = str(block_number)
            self.items[k] = o
            self.item_keys.append(k)
            logg.info('added existing {}'.format(o))

        v = self.get_target()
        if v != None:
            target = v
        
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


    def save_filter_list(self):
        raise NotImplementedError()
       

    def load_filter_list(self):
        raise NotImplementedError()


    def __get_locked_item(self):
        locked_item = self.filter_state.list(self.filter_state.state_store.LOCK)
        
        if len(locked_item) == 0:
            logg.error('Sync filter in store {} is not locked\n'.format(self))
            return None
        elif len(locked_item) > 1:
            raise FilterInitializationError('More than one locked filter item encountered in store {}. That should never happen, so I do not know what to do next.\n'.format(self))
        return locked_item[0]


    def __get_filter_index(self, k):
        i = -1
        fltrs = self.load_filter_list()
        for fltr in fltrs:
            i += 1
            if k == fltr.upper():
                logg.debug('lock filter match at filter list index {}'.format(i))
        return (i, fltrs,)


    def unlock_filter(self, revert=False):
        locked_item_key = self.__get_locked_item()
        if locked_item_key == None:
            return False
        locked_item = self.get(locked_item_key)
        state = self.filter_state.state(locked_item_key)
        locked_state = state - self.filter_state.state_store.LOCK
        locked_state_name = self.filter_state.name(locked_state)

        logg.debug('found locked item {} in state {}'.format(locked_item, locked_state))

        (i, fltrs) = self.__get_filter_index(locked_state_name)

        if i == -1:
            raise FilterInitializationError('locked state {} ({}) found for item {}, but matching filter has not been registered'.format(locked_state_name, locked_state, locked_item))

        direction = None
        if revert:
            self.__unlock_previous(locked_item, fltrs, i)
            new_state = self.filter_state.state(locked_item_key)
            direction = 'previous'
        else:
            self.__unlock_next(locked_item, fltrs, i)
            new_state = self.filter_state.state(locked_item_key)
            direction = 'next'

        logg.info('chainstate unlock to {} {} ({}) -> {} ({})'.format(direction, self.filter_state.name(state), state, self.filter_state.name(new_state), new_state))

        return True


    def __unlock_next(self, item, lst, index):
        if index == len(lst) - 1:
            item.reset(check_incomplete=False)
        else:
            item.release()


    def __unlock_previous(self, item, lst, index):
        if index == 0:
            item.reset(check_incomplete=False)
        else:
            new_state_str = lst[index - 1]
            new_state = self.filter_state.state_store.from_name(new_state_str)
            self.filter_state.state_store.move(item.state_key, new_state)


    def peek_current_filter(self):
        pass
