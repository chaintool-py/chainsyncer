class SyncDone(Exception):
    """Exception raised when a syncing is complete.
    """
    pass


class NoBlockForYou(Exception):
    """Exception raised when attempt to retrieve a block from network that does not (yet) exist.
    """
    pass


class RequestError(Exception):
    """Base exception for RPC query related errors.
    """
    pass


class BackendError(Exception):
    """Base exception for syncer state backend related errors.
    """
    pass


class LockError(Exception):
    """Base exception for attempting to manipulate a locked property
    """
    pass


class FilterDone(Exception):
    """Exception raised when all registered filters have been executed
    """
    pass


class InterruptError(FilterDone):
    """Exception for interrupting or attempting to use an interrupted sync
    """
    pass


class IncompleteFilterError(Exception):
    """Exception raised if filter reset is executed prematurely
    """
    pass


class FilterInitializationError(BackendError):
    """Exception raised if filter state does not match the registered filters
    """
    pass

#class AbortTx(Exception):
#    """
#    """
#    pass
