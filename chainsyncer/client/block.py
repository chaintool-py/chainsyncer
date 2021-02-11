class Block:

    def __init__(self, hsh, obj):
        self.hash = hsh
        self.obj = obj


    def tx(self, idx):
        return NotImplementedError


    def number(self):
        return NotImplementedError



