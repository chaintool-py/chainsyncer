# standard imports
import os
import sys
import logging
import time
import argparse
import sys
import re

# third-party imports
import confini
from cic_syncer.driver import HeadSyncer
from cic_syncer.db import dsn_from_config
from cic_syncer.db.models.base import SessionBase
from cic_syncer.client.evm.websocket import EVMWebsocketClient

logging.basicConfig(level=logging.WARNING)
logg = logging.getLogger()

config_dir = '/usr/local/etc/cic-syncer'

argparser = argparse.ArgumentParser(description='daemon that monitors transactions in new blocks')
argparser.add_argument('-p', '--provider', dest='p', type=str, help='chain rpc provider address')
argparser.add_argument('-c', type=str, default=config_dir, help='config root to use')
argparser.add_argument('-i', '--chain-spec', type=str, dest='i', help='chain spec')
argparser.add_argument('--abi-dir', dest='abi_dir', type=str, help='Directory containing bytecode and abi')
argparser.add_argument('--env-prefix', default=os.environ.get('CONFINI_ENV_PREFIX'), dest='env_prefix', type=str, help='environment prefix for variables to overwrite configuration')
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
        'CIC_CHAIN_SPEC': getattr(args, 'i'),
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

# TODO: There is too much code in this file, split it up

transfer_callbacks = []
for cb in config.get('TASKS_SYNCER_CALLBACKS', '').split(','):
    task_split = cb.split(':')
    task_queue = queue
    if len(task_split) > 1:
        task_queue = task_split[0]
    task_pair = (task_split[1], task_queue)
    transfer_callbacks.append(task_pair)


def tx_filter(w3, tx, rcpt, chain_spec):
    tx_hash_hex = tx.hash.hex()
    otx = Otx.load(tx_hash_hex)
    if otx == None:
        logg.debug('tx {} not found locally, skipping'.format(tx_hash_hex))
        return None
    logg.info('otx found {}'.format(otx.tx_hash))
    s = celery.signature(
            'cic_eth.queue.tx.set_final_status',
            [
                tx_hash_hex,
                rcpt.blockNumber,
                rcpt.status == 0,
                ],
            queue=queue,
            )
    t = s.apply_async()
    return t


re_websocket = re.compile('^wss?://')
re_http = re.compile('^https?://')
c = EVMWebsocketClient(config.get('ETH_PROVIDER'))
chain = args.i
#blockchain_provider = config.get('ETH_PROVIDER')
#if re.match(re_websocket, blockchain_provider) != None:
#    blockchain_provider = WebsocketProvider(blockchain_provider)
#elif re.match(re_http, blockchain_provider) != None:
#    blockchain_provider = HTTPProvider(blockchain_provider)
#else:
#    raise ValueError('unknown provider url {}'.format(blockchain_provider))
#

def main(): 
    #chain_spec = ChainSpec.from_chain_str(config.get('CIC_CHAIN_SPEC'))
    #c = RpcClient(chain_spec)

    block_offset = c.block_number()
    logg.debug('block offset {}'.format(block_offset))

    return
    syncer = SyncerBackend.live(chain, block_offset+1)

    for cb in config.get('TASKS_SYNCER_CALLBACKS', '').split(','):
        task_split = cb.split(':')
        task_queue = queue
        if len(task_split) > 1:
            task_queue = task_split[0]
        task_pair = (task_split[1], task_queue)
        syncer.filter.append(task_pair)

    try:
        syncer.loop(int(config.get('SYNCER_LOOP_INTERVAL')))
    except LoopDone as e:
        sys.stderr.write("sync '{}' done at block {}\n".format(args.mode, e))

    sys.exit(0)


if __name__ == '__main__':
    main()
