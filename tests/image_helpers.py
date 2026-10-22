"""Small image fixtures for picture API tests."""
import struct
import zlib


def palette_png():
    colors = [(211, 151, 178), (240, 215, 222), (193, 177, 216), (183, 202, 181)]
    width, height = 640, 360
    row = b''.join(bytes(colors[min(3, x // 160)]) for x in range(width))
    raw = (b'\0' + row) * height
    def chunk(kind, data):
        return struct.pack('!I', len(data)) + kind + data + struct.pack('!I', zlib.crc32(kind + data) & 0xffffffff)
    return b'\x89PNG\r\n\x1a\n' + chunk(b'IHDR', struct.pack('!2I5B', width, height, 8, 2, 0, 0, 0)) + chunk(b'IDAT', zlib.compress(raw)) + chunk(b'IEND', b'')
