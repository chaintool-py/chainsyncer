# standard imports
import hashlib


class SyncFilter:

    def sum(self):
        s = self.common_name()
        h = hashlib.sha256()
        h.update(s.encode('utf-8'))
        return h.digest()
        

    def filter(self, conn, block, tx):
        raise NotImplementedError()


    def common_name(self):
        s = self.__module__ + '.' + self.__class__.__name__
        return s.replace('.', '_')
