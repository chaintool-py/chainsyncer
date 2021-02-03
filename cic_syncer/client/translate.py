import re

re_hex = r'^[0-9a-fA-Z]+$'
def is_hex(hx):
    m = re.match(re_hex, hx)
    if m == None:
        raise ValueError('not valid hex {}'.format(hx))

    return hx


def strip_0x(hx):
    if len(hx) >= 2 and hx[:2] == '0x':
        hx = hx[2:]
    return is_hex(hx)


def hex_to_int(hx, endianness='big'):
    hx = strip_0x(hx)
    b = bytes.fromhex(hx)
    return int.from_bytes(b, endianness)
