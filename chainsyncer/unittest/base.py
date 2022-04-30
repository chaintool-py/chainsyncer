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

logging.STATETRACE = 5
logging.addLevelName('STATETRACE', logging.STATETRACE)
logg = logging.getLogger(__name__)


def state_event_handler(k, v_old, v_new):
    if v_old == None:
        logg.log(logging.STATETRACE, 'sync state create key {}: -> {}'.format(k, v_new))
    else:
        logg.log(logging.STATETRACE, 'sync state change key {}: {} -> {}'.format(k, v_old, v_new))
    

def filter_state_event_handler(k, v_old, v_new):
    if v_old == None:
        logg.log(logging.STATETRACE, 'filter state create key {}: -> {}'.format(k, v_new))
    else:
        logg.log(logging.STATETRACE, 'filter state change key {}: {} -> {}'.format(k, v_old, v_new))


class MockFilterError(Exception):
    pass


class MockBlockGenerator:

    def __init__(self, offset=0):
        self.blocks = {}
        self.offset = offset
        self.cursor = offset


    def generate(self, spec=[], driver=None):
        for v in spec:
            txs = []
            for i in range(v):
                tx_hash = os.urandom(32).hex()
                tx = MockTx(0, tx_hash)
                txs.append(tx)

            block = MockBlock(self.cursor, txs)
            self.blocks[self.cursor] = block
            self.cursor += 1

        if driver != None:
            self.apply(driver)


    def apply(self, driver, offset=0):
        block_numbers = list(self.blocks.keys())
        for block_number in block_numbers:
            if block_number < offset:
                continue
            block = self.blocks[block_number]
            driver.add_block(block) 



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
        self.hash = os.urandom(32).hex()


    def tx(self, i):
        """Get block transaction at given index.

        :param i: Transaction index
        :type i: int
        """
        return MockTx(i, self.txs[i].hash)


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
        self.contents.append((block.number, tx.index, tx.hash,))
        logg.debug('filter {} result {} block {} tx {} {}'.format(self.common_name(), r, block.number, tx.index, tx.hash))
        return r


class MockDriver(SyncDriver):

    def __init__(self, store, offset=0, target=-1, interrupt_block=None, interrupt_tx=None, interrupt_global=False):
        super(MockDriver, self).__init__(store, offset=offset, target=target)
        self.blocks = {}
        self.interrupt = None
        if interrupt_block != None:
            interrupt_block = int(interrupt_block)
            if interrupt_tx == None:
                interrupt_tx = 0
            else:
                interrupt_tx = int(interrupt_tx)
            self.interrupt = (interrupt_block, interrupt_tx,)
        self.interrupt_global = interrupt_global


    def add_block(self, block):
        logg.debug('add block {} {} with {} txs'.format(block.number, block.hash, len(block.txs)))
        self.blocks[block.number] = block


    def get(self, conn, item):
        try:
            return self.blocks[item.cursor]
        except KeyError:
            raise NoBlockForYou()


    def process(self, conn, item, block):
        i = item.tx_cursor
        while self.running:
            if self.interrupt != None:
                if self.interrupt[0] == block.number and self.interrupt[1] == i:
                    logg.info('interrupt triggered at {}'.format(self.interrupt))
                    if self.interrupt_global:
                        SyncDriver.running_global = False
                    self.running = False
                    break
            tx = block.tx(i)
            self.process_single(conn, block, tx)
            item.next()
            i += 1


class MockChainInterface:

    def block_by_number(self, number):
        return ('block_by_number', number,)


    def tx_by_hash(self, hsh):
        return ('tx_by_hash', hsh,)


    def block_from_src(self, src):
        return src


    def src_normalize(self, src):
        return src


    def tx_receipt(self, hsh):
        return ('receipt', hsh,)


class MockChainInterfaceConn(MockConn):

    def __init__(self, interface):
        self.ifc = interface
        self.blocks = {}
        self.txs = {}
   

    def add_block(self, block):
        logg.debug('add block {} {} with {} txs'.format(block.number, block.hash, len(block.txs)))
        self.blocks[block.number] = block
        for tx in block.txs:
            self.txs[tx.hash] = tx
           

    def do(self, o):
        m = getattr(self, 'handle_' + o[0])
        return m(o[1])


    def handle_block_by_number(self, number):
        return self.blocks[number]



    def handle_receipt(self, hsh):
        return {}


class MockItem:

    def __init__(self, target, offset, cursor, state_key):
        self.target = target
        self.offset = offset
        self.cursor = cursor
        self.state_key = state_key
