# third-party imports
from hexathon import strip_0x


def hex_to_int(hx, endianness='big'):
    hx = strip_0x(hx)
    if len(hx) % 2 == 1:
        hx = '0' + hx
    b = bytes.fromhex(hx)
    return int.from_bytes(b, endianness)
