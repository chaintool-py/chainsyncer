class LoopDone(Exception):
    """Exception raised when a syncing is complete.
    """
    pass


class RequestError(Exception):
    pass


class BackendError(Exception):
    pass
