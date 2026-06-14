#!/usr/bin/env python3
"""Genera PNGs simples para EAS sin dependencias externas."""

import struct
import zlib
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent / 'assets'
ROOT.mkdir(parents=True, exist_ok=True)

# #0f766e
R, G, B = 15, 118, 110


def png_rgb(size: int, path: Path) -> None:
    raw = b''.join(
        b'\x00' + bytes([R, G, B]) * size
        for _ in range(size)
    )
    compressed = zlib.compress(raw, 9)

    def chunk(tag: bytes, data: bytes) -> bytes:
        return struct.pack('>I', len(data)) + tag + data + struct.pack('>I', zlib.crc32(tag + data) & 0xFFFFFFFF)

    ihdr = struct.pack('>IIBBBBB', size, size, 8, 2, 0, 0, 0)
    png = b'\x89PNG\r\n\x1a\n'
    png += chunk(b'IHDR', ihdr)
    png += chunk(b'IDAT', compressed)
    png += chunk(b'IEND', b'')
    path.write_bytes(png)
    print(f'✓ {path}')


for name, size in (
    ('icon.png', 1024),
    ('adaptive-icon.png', 1024),
    ('splash-icon.png', 512),
):
    png_rgb(size, ROOT / name)
