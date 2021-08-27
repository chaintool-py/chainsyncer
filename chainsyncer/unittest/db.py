# standard imports
import logging
import os

# external imports
import alembic
import alembic.config

# local imports
from chainsyncer.db.models.base import SessionBase
from chainsyncer.db import dsn_from_config
from chainsyncer.db.models.base import SessionBase

logg = logging.getLogger(__name__)


class ChainSyncerDb:
    """SQLITE database setup for unit tests

    :param debug: Activate sql level debug (outputs sql statements)
    :type debug: bool
    """

    base = SessionBase

    def __init__(self, debug=False):
        config = {
            'DATABASE_ENGINE': 'sqlite',
            'DATABASE_DRIVER': 'pysqlite',
            'DATABASE_NAME': 'chainsyncer.sqlite',
                }
        logg.debug('config {}'.format(config))

        self.dsn = dsn_from_config(config)

        self.base.poolable = False
        self.base.transactional = False
        self.base.procedural = False
        self.base.connect(self.dsn, debug=debug) # TODO: evaluates to "true" even if string is 0

        rootdir = os.path.join(os.path.dirname(os.path.dirname(__file__)), '..')
        dbdir = os.path.join(rootdir, 'chainsyncer', 'db')
        #migrationsdir = os.path.join(dbdir, 'migrations', config.get('DATABASE_ENGINE'))
        migrationsdir = os.path.join(dbdir, 'migrations', 'default')
        logg.info('using migrations directory {}'.format(migrationsdir))

        ac = alembic.config.Config(os.path.join(migrationsdir, 'alembic.ini'))
        ac.set_main_option('sqlalchemy.url', self.dsn)
        ac.set_main_option('script_location', migrationsdir)

        alembic.command.downgrade(ac, 'base')
        alembic.command.upgrade(ac, 'head')


    def bind_session(self, session=None):
        """Create session using underlying session base
        """
        return self.base.bind_session(session)

    
    def release_session(self, session=None):
        """Release session using underlying session base
        """
        return self.base.release_session(session)
