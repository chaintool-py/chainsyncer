def process_config(config, arg, args, flags):
        args_override = {}

        args_override['SYNCER_BACKEND'] = getattr(args, 'backend')

        if arg.match('range', flags):
            args_override['SYNCER_OFFSET'] = getattr(args, 'offset')
            args_override['SYNCER_LIMIT'] = getattr(args, 'until')

        config.dict_override(args_override, 'local cli args')

        if arg.match('head', flags):
            config.add(getattr(args, 'keep_alive'), '_KEEP_ALIVE')
            config.add(getattr(args, 'head'), '_HEAD')

        config.add(getattr(args, 'single'), '_SINGLE')

        return config
