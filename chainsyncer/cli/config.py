# external imports
from chainsyncer.cli import SyncFlag


def process_config(config, args, flags):
        args_override = {}

        args_override['SYNCER_BACKEND'] = getattr(args, 'backend')

        if flags & SyncFlag.RANGE:
            args_override['SYNCER_OFFSET'] = getattr(args, 'offset')
            args_override['SYNCER_LIMIT'] = getattr(args, 'until')

        config.dict_override(args_override, 'local cli args')

        if flags & SyncFlag.HEAD:
            config.add(getattr(args, 'keep_alive'), '_KEEP_ALIVE')
            config.add(getattr(args, 'head'), '_HEAD')

        return config
