# standard imports
import uuid
import os
import logging

# external imports
from shep.store.file import SimpleFileStoreFactory

# local imports 
from chainsyncer.store import SyncStore

logg = logging.getLogger(__name__)


class SyncFsStore(SyncStore):

    def __init__(self, base_path, session_id=None, state_event_callback=None, filter_state_event_callback=None):
        super(SyncFsStore, self).__init__(base_path, session_id=session_id)

        create_path = False
        try:
            os.stat(self.session_path)
        except FileNotFoundError:
            create_path = True

        if create_path:
            #self.__create_path(base_path, self.default_path, session_id=session_id)
            os.makedirs(self.session_path)

        self.session_id = os.path.basename(self.session_path)
        logg.info('session id {} resolved {} path {}'.format(session_id, self.session_id, self.session_path))

        base_sync_path = os.path.join(self.session_path, 'sync')
        factory = SimpleFileStoreFactory(base_sync_path, binary=True)
        self.setup_sync_state(factory, state_event_callback)

        self.setup_filter_state(callback=filter_state_event_callback)


    def setup_filter_state(self, callback=None):
        base_filter_path = os.path.join(self.session_path, 'filter')
        factory = SimpleFileStoreFactory(base_filter_path, binary=True)
        super(SyncFsStore, self).setup_filter_state(factory, callback)


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


    def get_target(self):
        fp = os.path.join(self.session_path, 'target')
        try:
            f = open(fp, 'r')
            v = f.read()
            f.close()
            self.target = int(v)
        except FileNotFoundError as e:
            logg.debug('cant find target {} {}'.format(fp, e))
            pass


    def set_target(self, v):
        fp = os.path.join(self.session_path, 'target')
        f = open(fp, 'w')
        f.write(str(v))
        f.close()
        self.target = v


    def load_filter_list(self):
        fltr = []
        fp = os.path.join(self.session_path, 'filter_list')
        f = open(fp, 'r')
        while True:
            v = f.readline()
            if len(v) == 0:
                break
            v = v.rstrip()
            fltr.append(v) 
        f.close()
        return fltr


    def save_filter_list(self):
        fp = os.path.join(self.session_path, 'filter_list')
        f = open(fp, 'w')
        for fltr in self.filters:
            f.write(fltr.common_name() + '\n')
        f.close()
