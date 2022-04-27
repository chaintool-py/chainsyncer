# local imports
from .base import SyncFlag


def process_flags(argparser, flags):

    if flags & SyncFlag.RANGE > 0:
        argparser.add_argument('--offset', type=int, help='Block to start sync from. Default is start of history (0).')
        argparser.add_argument('--until', type=int, default=-1, help='Block to stop sync on. Default is stop at block height of first run.')
    if flags & SyncFlag.HEAD > 0:
        argparser.add_argument('--head', action='store_true', help='Start from latest block as offset')
        argparser.add_argument('--keep-alive', action='store_true', help='Do not stop syncing when caught up')

    argparser.add_argument('--backend', type=str, help='Backend to use for state store')
