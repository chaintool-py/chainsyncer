# standard imports
import os
import sys
import logging
import time
import argparse
import sys
import re

# external imports
import confini
from chainlib.eth.connection import HTTPConnection
from chainlib.eth.block import block_latest
from chainlib.chain import ChainSpec

# local imports
from chainsyncer.driver import HeadSyncer
from chainsyncer.db import dsn_from_config
from chainsyncer.db.models.base import SessionBase
from chainsyncer.backend import SyncerBackend
from chainsyncer.error import LoopDone
from chainsyncer.filter import NoopFilter

logging.basicConfig(level=logging.WARNING)
logg = logging.getLogger()

config_dir = '/usr/local/etc/cic-syncer'


class Handler:

    def __init__(self, method, domain):
        self.method = method
        self.domain = domain

    def handle(self, getter, tx, chain):
        logg.debug('noop tx {} chain {} method {} domain {}'.format(tx, chain, self.method, self.domain))
handler = getattr(Handler, 'handle')


argparser = argparse.ArgumentParser(description='daemon that monitors transactions in new blocks')
argparser.add_argument('-p', '--provider', dest='p', type=str, help='chain rpc provider address')
argparser.add_argument('-c', type=str, default=config_dir, help='config root to use')
argparser.add_argument('-i', '--chain-spec', type=str, dest='i', help='chain spec')
argparser.add_argument('--abi-dir', dest='abi_dir', type=str, help='Directory containing bytecode and abi')
argparser.add_argument('--env-prefix', default=os.environ.get('CONFINI_ENV_PREFIX'), dest='env_prefix', type=str, help='environment prefix for variables to overwrite configuration')
argparser.add_argument('--offset', type=int, help='block number to start sync')
argparser.add_argument('-q', type=str, default='cic-eth', help='celery queue to submit transaction tasks to')
argparser.add_argument('-v', help='be verbose', action='store_true')
argparser.add_argument('-vv', help='be more verbose', action='store_true')
args = argparser.parse_args(sys.argv[1:])

if args.v == True:
    logging.getLogger().setLevel(logging.INFO)
elif args.vv == True:
    logging.getLogger().setLevel(logging.DEBUG)

config_dir = os.path.join(args.c)
os.makedirs(config_dir, 0o777, True)
config = confini.Config(config_dir, args.env_prefix)
config.process()
# override args
args_override = {
        'SYNCER_CHAIN_SPEC': getattr(args, 'i'),
        'ETH_PROVIDER': getattr(args, 'p'),
        }
config.dict_override(args_override, 'cli flag')
config.censor('PASSWORD', 'DATABASE')
config.censor('PASSWORD', 'SSL')
logg.debug('config loaded from {}:\n{}'.format(config_dir, config))

#app = celery.Celery(backend=config.get('CELERY_RESULT_URL'),  broker=config.get('CELERY_BROKER_URL'))

queue = args.q

dsn = dsn_from_config(config)
SessionBase.connect(dsn)

conn = HTTPConnection(config.get('ETH_PROVIDER'))

chain = ChainSpec.from_chain_str(config.get('SYNCER_CHAIN_SPEC'))

block_offset = args.offset


def main(): 
    global block_offset 

    if block_offset == None:
        o = block_latest()
        r = conn.do(o)
        block_offset = r[1]

    syncer_backend = SyncerBackend.live(chain, 0)
    syncer = HeadSyncer(syncer_backend)
    fltr = NoopFilter()
    syncer.add_filter(fltr)

    try:
        logg.debug('block offset {}'.format(block_offset))
        syncer.loop(int(config.get('SYNCER_LOOP_INTERVAL')), conn)
    except LoopDone as e:
        sys.stderr.write("sync '{}' done at block {}\n".format(args.mode, e))

    sys.exit(0)


if __name__ == '__main__':
    main()
