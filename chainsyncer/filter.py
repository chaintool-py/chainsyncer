class SyncFilter:

    def common_name(self):
        raise NotImplementedError()


    def sum(self):
        raise NotImplementedError()


    def filter(self, conn, block, tx):
        raise NotImplementedError()
