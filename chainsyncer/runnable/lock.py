# SPDX-License-Identifier: GPL-3.0-or-later

# standard imports
import os
import logging
import sys
import importlib

# external imports
import chainlib.cli

# local imports
import chainsyncer.cli
from chainsyncer.settings import ChainsyncerSettings

logging.basicConfig(level=logging.WARNING)
logg = logging.getLogger()


arg_flags = chainlib.cli.argflag_std_base | chainlib.cli.Flag.CHAIN_SPEC
argparser = chainlib.cli.ArgumentParser(arg_flags)
argparser.add_argument('--state-dir', type=str, dest='state_dir', help='State directory')
argparser.add_argument('--session-id', type=str, dest='session_id', help='Session id for state')
argparser.add_argument('--action', type=str, choices=['repeat', 'continue'], help='Action to take on lock. Repeat means re-run the locked filter. Continue means resume execution for next filter.')
argparser.add_positional('tx', type=str, help='Transaction hash to unlock')

sync_flags = chainsyncer.cli.SyncFlag.RANGE | chainsyncer.cli.SyncFlag.HEAD
chainsyncer.cli.process_flags(argparser, sync_flags)

args = argparser.parse_args()

base_config_dir = chainsyncer.cli.config_dir,
config = chainlib.cli.Config.from_args(args, arg_flags, base_config_dir=base_config_dir)
config = chainsyncer.cli.process_config(config, args, sync_flags)
config.add(args.state_dir, '_STATE_DIR', False)
config.add(args.session_id, '_SESSION_ID', False)
logg.debug('config loaded:\n{}'.format(config))

settings = ChainsyncerSettings()
settings.process_sync_backend(config)


def main():
    state_dir = None
    if settings.get('SYNCER_BACKEND') == 'mem':
        raise ValueError('cannot unlock volatile state store')

    if settings.get('SYNCER_BACKEND') == 'fs': 
        syncer_store_module = importlib.import_module('chainsyncer.store.fs')
        syncer_store_class = getattr(syncer_store_module, 'SyncFsStore')
    elif settings.get('SYNCER_BACKEND') == 'rocksdb':
        syncer_store_module = importlib.import_module('chainsyncer.store.rocksdb')
        syncer_store_class = getattr(syncer_store_module, 'SyncRocksDbStore')
    else:
        syncer_store_module = importlib.import_module(settings.get('SYNCER_BACKEND'))
        syncer_store_class = getattr(syncer_store_module, 'SyncStore')
        
    state_dir = os.path.join(config.get('_STATE_DIR'), settings.get('SYNCER_BACKEND'))
    sync_path = os.path.join(config.get('_SESSION_ID'), 'sync', 'filter')
    sync_store = syncer_store_class(state_dir, session_id=sync_path)

    logg.info('session is {}'.format(sync_store.session_id))


if __name__ == '__main__':
    main()
