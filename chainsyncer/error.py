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


#class AbortTx(Exception):
#    """
#    """
#    pass
