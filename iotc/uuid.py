import os
import ubinascii
import random


class UUID:
    def __init__(self, bytes):
        if len(bytes) != 16:
            raise ValueError('bytes arg must be 16 bytes long')
        self._bytes = bytes

    @property
    def hex(self):
        return ubinascii.hexlify(self._bytes).decode()

    def __str__(self):
        h = self.hex
        return '-'.join((h[0:8], h[8:12], h[12:16], h[16:20], h[20:32]))

    def __repr__(self):
        return "<UUID: %s>" % str(self)


def uuid4():
    """Generates a random UUID compliant to RFC 4122 pg.14"""
    num = bytearray(random.getrandbits(16))
    num[6] = (num[6] & 0x0F) | 0x40
    num[8] = (num[8] & 0x3F) | 0x80
    return UUID(bytes=num)