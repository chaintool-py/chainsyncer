# standard imports
import uuid
import os
import logging

# external imports
from shep.store.file import SimpleFileStoreFactory

# local imports 
from chainsyncer.store import (
        SyncItem,
        SyncStore,
        )

logg = logging.getLogger(__name__)


class SyncFsStore(SyncStore):

    def __init__(self, base_path, session_id=None, state_event_callback=None, filter_state_event_callback=None):
        super(SyncFsStore, self).__init__(session_id=session_id)

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
        self.session_id = os.path.basename(self.session_path)

        logg.info('session id {} resolved {} path {}'.format(session_id, self.session_id, self.session_path))

        base_sync_path = os.path.join(self.session_path, 'sync')
        factory = SimpleFileStoreFactory(base_sync_path, binary=True)
        self.setup_sync_state(factory, state_event_callback)

        base_filter_path = os.path.join(self.session_path, 'filter')
        factory = SimpleFileStoreFactory(base_filter_path, binary=True)
        self.setup_filter_state(factory, filter_state_event_callback)


    def __create_path(self, base_path, default_path, session_id=None):
        logg.debug('fs store path {} does not exist, creating'.format(self.session_path))
        if session_id == None:
            session_id = str(uuid.uuid4())
        self.session_path = os.path.join(base_path, session_id)
        os.makedirs(self.session_path)
        
        if self.is_default:
            try:
                os.symlink(self.session_path, default_path)
            except FileExistsError:
                pass


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

        logg.debug('thresholds {}'.format(thresholds))
        for i in range(len(thresholds)):
            item_target = target
            if i < lim:
                item_target = thresholds[i+1] 
            o = SyncItem(block_number, item_target, self.state, self.filter_state, started=True)
            self.items[block_number] = o
            self.item_keys.append(block_number)
            logg.info('added existing {}'.format(o))

        fp = os.path.join(self.session_path, 'target')
        have_target = False
        try:
            f = open(fp, 'r')
            v = f.read()
            f.close()
            self.target = int(v)
            have_target = True
        except FileNotFoundError as e:
            pass

        if len(thresholds) == 0:
            if have_target:
                logg.warning('sync "{}" is already done, nothing to do'.format(self.session_id))
            else:
                logg.info('syncer first run target {}'.format(target))
                self.first = True
                f = open(fp, 'w')
                f.write(str(target))
                f.close()
                self.target = target
