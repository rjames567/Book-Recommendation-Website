# ------------------------------------------------------------------------------
# Logging
# ------------------------------------------------------------------------------
class Logging:
    def __init__(self, filepath="logging/", clear=True):
        self._filepath = filepath
        self._clear = clear