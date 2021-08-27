# stanard imports
import logging

# third-party imports
from sqlalchemy import Column, Integer
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import (
        StaticPool,
        QueuePool,
        AssertionPool,
        NullPool,
        )

logg = logging.getLogger()

Model = declarative_base(name='Model')

CONNECTION_OVERFLOW_FACTOR = 3
CONNECTION_RECYCLE_AFTER = 60


class SessionBase(Model):
    """The base object for all SQLAlchemy enabled models. All other models must extend this.
    """
    __abstract__ = True
 
    id = Column(Integer, primary_key=True)

    engine = None
    """Database connection engine of the running aplication"""
    sessionmaker = None
    """Factory object responsible for creating sessions from the  connection pool"""
    transactional = True
    """Whether the database backend supports query transactions. Should be explicitly set by initialization code"""
    poolable = True
    """Whether the database backend supports connection pools. Should be explicitly set by initialization code"""
    procedural = True
    """Whether the database backend supports stored procedures"""
    localsessions = {}
    """Contains dictionary of sessions initiated by db model components"""


    @staticmethod
    def create_session():
        """Creates a new database session.
        """
        return SessionBase.sessionmaker()


    @staticmethod
    def _set_engine(engine):
        """Sets the database engine static property

        :param engine: The sqlalchemy engine
        :type engine: sqlalchemy.engine.Engine
        """
        SessionBase.engine = engine
        SessionBase.sessionmaker = sessionmaker(bind=SessionBase.engine)


    @staticmethod
    def connect(dsn, pool_size=16, debug=False):
        """Create new database connection engine and connect to database backend.

        The pool_size argument controls the behavior of the connection pool.

        If the pool_size is greater than 1, and the engine has connection pool settings, The connection pool will be set up with the given number of connections. By default, it allows for 3x connection overflow (CONNECTION_OVERFLOW_FACTOR), and connection recycling after 60 seconds of inactivity (CONNECTION_RECYCLE_AFTER).

        If the pool_size is 1 and debug mode is off, the StaticPool class (single connection pool) will be used. If debug is on, AssertionPool will be used (which raises assertionerror if more than a single connection is attempted at any one time by the process).

        If the underlying engine does not have pooling capabilities, the pool_size parameter toggles the connection class used. If pool_size is set to 0, the NullPool will be used (build a new connection for every session). If pool_size is set to a positive number, the StaticPool will be used, keeping a single connection for all sessions.

        :param dsn: DSN string defining connection
        :type dsn: str
        :param pool_size: Size of connection pool
        :type pool_size: int
        :param debug: Activate sql debug mode (outputs sql statements)
        :type debug: bool
        """
        e = None
        if SessionBase.poolable:
            poolclass = QueuePool
            if pool_size > 1:
                e = create_engine(
                        dsn,
                        max_overflow=pool_size * CONNECTION_OVERFLOW_FACTOR,
                        pool_pre_ping=True,
                        pool_size=pool_size,
                        pool_recycle=CONNECTION_RECYCLE_AFTER,
                        poolclass=poolclass,
                        echo=debug,
                    )
            else:
                if debug:
                    poolclass = AssertionPool
                else:
                    poolclass = StaticPool

                e = create_engine(
                        dsn,
                        poolclass=poolclass,
                        echo=debug,
                    )
        else:
            pool_class = StaticPool
            if pool_size < 1:
                pool_class = NullPool
            e = create_engine(
                    dsn,
                    poolclass=pool_class,
                    echo=debug,
                    )

        SessionBase._set_engine(e)


    @staticmethod
    def disconnect():
        """Disconnect from database and free resources.
        """
        SessionBase.engine.dispose()
        SessionBase.engine = None


    @staticmethod
    def bind_session(session=None):
        """Convenience function to enforce database session responsilibity in call stacks where it is unclear which layer will create a database session.

        If the session argument is None, the method will create and return a new database session. A reference to the database session will be statically stored in the SessionBase class, and must be explicitly released with release_session.

        When an existing session in passed as the argument, this method simply returns back the same session.

        :param session: An sqlalchemy session
        :type session: session.orm.Session
        :rtype: session.orm.Session
        :returns: An sqlalchemy session
        """
        localsession = session
        if localsession == None:
            localsession = SessionBase.create_session()
            localsession_key = str(id(localsession))
            logg.debug('creating new session {}'.format(localsession_key))
            SessionBase.localsessions[localsession_key] = localsession
        return localsession


    @staticmethod
    def release_session(session):
        """Checks if a reference to the given session exists in the SessionBase session store, and if it does commits the transaction and closes the session.

        :param session: An sqlalchemy session
        :type session: session.orm.Session
        """
        session_key = str(id(session))
        if SessionBase.localsessions.get(session_key) != None:
            logg.debug('commit and destroy session {}'.format(session_key))
            session.commit()
            session.close()
            del SessionBase.localsessions[session_key]
