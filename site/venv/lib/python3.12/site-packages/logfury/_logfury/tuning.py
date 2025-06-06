class limit_trace_arguments:
    """
    A decorator which causes the function execution logging to omit some fields
    """

    def __init__(self, only=None, skip=None):
        """
            only - if not None, contains a whitelist (tuple of names) of arguments
                   that are safe to be logged. All others can not be logged.
            skip - if not None, contains a whitelist (tuple of names) of arguments
                   that are not safe to be logged.
        """
        self.only = only
        self.skip = skip

    def __call__(self, function):
        function._trace_only = self.only
        function._trace_skip = self.skip
        return function


def disable_trace(function):
    """
    A decorator which suppresses the function execution logging
    """
    function._trace_disable = True
    return function
