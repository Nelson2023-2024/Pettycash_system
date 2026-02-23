class TransactionLogError(Exception):
    """
    Raised when a transaction log entry fails to be created.
    Signals an internal logging failure without affecting the main operation.
    """
    pass