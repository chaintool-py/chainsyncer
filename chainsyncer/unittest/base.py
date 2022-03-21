# standard imports
import os
import logging
import hashlib

# external imports
from hexathon import add_0x
from shep.state import State

# local imports
#from chainsyncer.driver.history import HistorySyncer
from chainsyncer.error import NoBlockForYou
from chainsyncer.driver import SyncDriver

logg = logging.getLogger().getChild(__name__)


class MockFilterError(Exception):
    pass


class MockConn:
    """Noop connection mocker.

    :param o: Object to execute rpc call for
    :type o: dict
    """
    def do(self, o):
        pass


class MockTx:
    """Minimal mocked tx object.

    :param index: Transaction index in block
    :type index: int
    :param tx_hash: Transaction hash
    :type tx_hash: str
    """
    def __init__(self, index, tx_hash):
        self.hash = tx_hash
        self.index = index


    def apply_receipt(self, rcpt):
        """Save receipt source in mock tx object.

        :param rcpt: Transaction receipt
        :type rcpt: dict
        """
        self.rcpt = rcpt


class MockBlock:

    def __init__(self, number, txs):
        """Minimal mocked block object.

        :param number: Block number
        :type number: int
        :param txs: Transaction list to include in block
        :type txs: list
        """
        self.number = number
        self.txs = txs


    def tx(self, i):
        """Get block transaction at given index.

        :param i: Transaction index
        :type i: int
        """
        return MockTx(i, self.txs[i])


class MockStore(State):

    def __init__(self, bits=0):
        super(MockStore, self).__init__(bits, check_alias=False) 

    
    def start(self, offset=0, target=-1):
        pass


class MockFilter:

    def __init__(self, name, brk=None, brk_hard=None, z=None):
        self.name = name
        if z == None:
            h = hashlib.sha256()
            h.update(self.name.encode('utf-8'))
            z = h.digest()
        self.z = z
        self.brk = brk
        self.brk_hard = brk_hard
        self.contents = []


    def sum(self):
        return self.z


    def common_name(self):
        return self.name 


    def filter(self, conn, block, tx):
        r = False
        self.contents.append((block.number, tx.index, tx.hash,))
        if self.brk_hard != None:
            r = True
            if self.brk_hard > 0:
                r = True
            self.brk_hard -= 1
            if r:
                raise MockFilterError()
        if self.brk != None:
            if self.brk > 0:
                r = True
            self.brk -= 1
        logg.debug('filter {} r {}'.format(self.common_name(), r))
        return r


class MockDriver(SyncDriver):

    def __init__(self, store, offset=0, target=-1):
        super(MockDriver, self).__init__(store, offset=offset, target=target)
        self.blocks = {}


    def add_block(self, block):
        self.blocks[block.number] = block


    def get(self, conn, item):
        return self.blocks[item.cursor]


    def process(self, conn, item, block, tx_start):
        i = tx_start
        while True:
            tx = block.tx(i)
            self.process_single(conn, block, tx)
            item.next()
            i += 1
