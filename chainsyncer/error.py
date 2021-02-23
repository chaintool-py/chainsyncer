class SyncDone(Exception):
    """Exception raised when a syncing is complete.
    """
    pass

class NoBlockForYou(Exception):
    pass


class RequestError(Exception):
    pass


class BackendError(Exception):
    pass
