# standard imports
import logging

logg = logging.getLogger().getChild(__name__)


class Backend:

    def __init__(self, flags_reversed=False):
        self.filter_count = 0
        self.flags_reversed = flags_reversed
        
    
    def check_filter(self, n, flags):
        if self.flags_reversed:
            try:
                v = 1 << flags.bit_length() - 1
                return (v >> n) & flags > 0
            except ValueError:
                pass
            return False
        return flags & (1 << n) > 0
