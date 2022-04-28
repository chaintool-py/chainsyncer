# SPDX-License-Identifier: GPL-3.0-or-later

# standard imports
import os
import logging
import sys
import importlib

# external imports
import chainlib.cli
from shep.persist import PersistedState

# local imports
import chainsyncer.cli
from chainsyncer.settings import ChainsyncerSettings
from chainsyncer.store import SyncStore
from chainsyncer.filter import FilterState

logging.basicConfig(level=logging.WARNING)
logg = logging.getLogger()


arg_flags = chainlib.cli.argflag_std_base | chainlib.cli.Flag.CHAIN_SPEC
argparser = chainlib.cli.ArgumentParser(arg_flags)
argparser.add_argument('--state-dir', type=str, dest='state_dir', help='State directory')
argparser.add_positional('action', type=str, help='Action to take on lock. Repeat means re-run the locked filter. Continue means resume execution for next filter.')

sync_flags = chainsyncer.cli.SyncFlag.RANGE | chainsyncer.cli.SyncFlag.HEAD
chainsyncer.cli.process_flags(argparser, sync_flags)

args = argparser.parse_args()

base_config_dir = chainsyncer.cli.config_dir,
config = chainlib.cli.Config.from_args(args, arg_flags, base_config_dir=base_config_dir)
config = chainsyncer.cli.process_config(config, args, sync_flags)
config.add(args.state_dir, '_STATE_DIR', False)
logg.debug('config loaded:\n{}'.format(config))

settings = ChainsyncerSettings()
settings.process_sync_backend(config)
logg.debug('settings:\n{}'.format(str(settings)))



def main():
    if settings.get('SYNCER_BACKEND') == 'mem':
        raise ValueError('cannot unlock volatile state store')

    if settings.get('SYNCER_BACKEND') == 'fs': 
        syncer_store_module = importlib.import_module('shep.store.file')
        syncer_store_class = getattr(syncer_store_module, 'SimpleFileStoreFactory')
    elif settings.get('SYNCER_BACKEND') == 'rocksdb':
        syncer_store_module = importlib.import_module('shep.store.rocksdb')
        syncer_store_class = getattr(syncer_store_module, 'RocksdbStoreFactory')
    else:
        raise NotImplementedError('cannot use backend: {}'.format(config.get('SYNCER_BACKEND')))
       
    state_dir = config.get('_STATE_DIR')

    factory = syncer_store_class(state_dir)
    store = SyncStore(state_dir, no_session=True)
    #base_state = PersistedState(factory.add, 0, check_alias=False)
    #state = FilterState(base_state, scan=True)
    store.setup_filter_state(factory=factory)
    store.connect()
    store.filter_state.scan()
    locked_state = store.filter_state.list(store.filter_state.from_name('RESET'))
    print(locked_state)
#    if locked_state == None:
#        sys.stderr.write('state in {} backend "{}" is not locked\n'.format(state_dir, config.get('SYNCER_BACKEND')))
#        sys.exit(1)




if __name__ == '__main__':
    main()
