def apply_flag(flag):
    flag.add('range')
    flag.add('head')
    flag.alias('sync_range_ext', 'range', 'head')
    return flag


def apply_arg(arg):
    arg.add_long('offset', 'range', typ=int, help='Block to start sync from. Default is start of history (0).')
    arg.add_long('until', 'range', typ=int, default=-1, help='Block to stop sync on. Default is stop at block height of first run.')
    arg.add_long('single', 'range', typ=bool, help='Execute a single sync, regardless of previous states')
    arg.add_long('head', 'head', typ=bool, help='Start from latest block as offset')
    arg.add_long('keep-alive', 'head', typ=bool, help='Do not stop syncing when caught up')
    return arg
