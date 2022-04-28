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
from chainsyncer.filter import (
        FilterState,
        SyncFilter,
        )

logging.basicConfig(level=logging.WARNING)
logg = logging.getLogger()

valid_fwd = [
        'fwd',
        'forward',
        'next',
        'continue',
        ]

valid_rwd = [
        'rwd',
        'rewind',
        'current',
        'back',
        'repeat',
        'replay',
        ]

action_is_forward = False

arg_flags = chainlib.cli.argflag_std_base | chainlib.cli.Flag.CHAIN_SPEC
argparser = chainlib.cli.ArgumentParser(arg_flags)
argparser.add_argument('--state-dir', type=str, dest='state_dir', help='State directory')
argparser.add_positional('action', type=str, help='Action to take on lock. Repeat means re-run the locked filter. Continue means resume execution for next filter.')

sync_flags = chainsyncer.cli.SyncFlag.RANGE | chainsyncer.cli.SyncFlag.HEAD
chainsyncer.cli.process_flags(argparser, sync_flags)

args = argparser.parse_args()

if args.action in valid_fwd:
    action_is_forward = True
elif args.action not in valid_rwd:
    sys.stderr.write('action argument must be one of {} or {}\n'.format(valid_rwd, valid_fwd))
    sys.exit(1)


base_config_dir = chainsyncer.cli.config_dir,
config = chainlib.cli.Config.from_args(args, arg_flags, base_config_dir=base_config_dir)
config = chainsyncer.cli.process_config(config, args, sync_flags)
config.add(args.state_dir, '_STATE_DIR', False)
logg.debug('config loaded:\n{}'.format(config))

settings = ChainsyncerSettings()
settings.process_sync_backend(config)
logg.debug('settings:\n{}'.format(str(settings)))


class FilterInNameOnly(SyncFilter):

    def __init__(self, k):
        self.k = k


    def common_name(self):
        return self.k


def main():
    if settings.get('SYNCER_BACKEND') == 'mem':
        raise ValueError('cannot unlock volatile state store')

    state_dir = config.get('_STATE_DIR')

    if config.get('SYNCER_BACKEND') == 'fs': 
            syncer_store_module = importlib.import_module('chainsyncer.store.fs')
            syncer_store_class = getattr(syncer_store_module, 'SyncFsStore')
    elif config.get('SYNCER_BACKEND') == 'rocksdb':
        syncer_store_module = importlib.import_module('chainsyncer.store.rocksdb')
        syncer_store_class = getattr(syncer_store_module, 'SyncRocksDbStore')
    else:
        syncer_store_module = importlib.import_module(config.get('SYNCER_BACKEND'))
        syncer_store_class = getattr(syncer_store_module, 'SyncStore')

    logg.info('using engine {} module {}.{}'.format(config.get('SYNCER_BACKEND'), syncer_store_module.__file__, syncer_store_class.__name__))

    store = syncer_store_class(state_dir)
    
    filter_list = store.load_filter_list()
    for i, k in enumerate(filter_list):
        fltr = FilterInNameOnly(k)
        store.register(fltr)
        filter_list[i] = k.upper()

    store.connect()
    store.start(ignore_lock=True)

    lock_state = store.filter_state.from_name('LOCK')
    locked_item = store.filter_state.list(lock_state)
    if len(locked_item) == 0:
        sys.stderr.write('Sync filter in {} is not locked\n'.format(state_dir))
        sys.exit(1)
    elif len(locked_item) > 1:
        sys.stderr.write('More than one locked item encountered in {}. That should never happen, so I do not know what to do next.\n'.format(state_dir))
        sys.exit(1)

    locked_item_key = locked_item[0]
    locked_item = store.get(int(locked_item_key))
    locked_state = store.filter_state.state(locked_item_key) - lock_state
    locked_state_name = store.filter_state.name(locked_state)
    logg.info('found item "{}" in locked state {}'.format(locked_item, store.filter_state.name(locked_state)))

    if action_is_forward:
        k = locked_state_name
        filter_index = None
        filter_index = filter_list.index(k)
        filter_pos = filter_index + 1
        filter_count = len(filter_list)
        logg.debug('Locked filter {} found at position {} of {}'.format(k, filter_pos, filter_count))
        if filter_pos == filter_count:
            logg.info('Locked filter {} is the last filter in the list. Executing filter reset'.format(k))
            locked_item.reset(check_incomplete=False)
        else:
            locked_item.advance(ignore_lock=True)
            store.filter_state.unset(locked_item_key, lock_state)
    else:
        filter_mask = 0xf
        filter_state = store.filter_state.mask(locked_state, filter_mask)
        logg.info('Chosen action is "{}": will continue execution at previous filter {}'.format(args.action, store.filter_state.name(filter_state)))
        store.filter_state.unset(locked_item_key, lock_state)


if __name__ == '__main__':
    main()
