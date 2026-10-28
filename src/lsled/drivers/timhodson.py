"""Badges with service fee9 and AES-encrypted commands, as reverse-engineered by Tim Hodson.

Protocol, key and cell encoding come from https://github.com/timhodson/ble-led-badge (MIT).
Upload: DATS command, encrypted data packets on the upload characteristic, DATCP command,
then MODE, LIGHT and SPEED commands.
"""
from Crypto.Cipher import AES

from ..core.render import Display
from .base import Driver, Write

SERVICE_UUID = "0000fee9-0000-1000-8000-00805f9b34fb"
COMMAND = "d44bc439-abfd-45a2-b575-925416129600"
IMAGE_UPLOAD = "d44bc439-abfd-45a2-b575-92541612960a"
NOTIFY = "d44bc439-abfd-45a2-b575-925416129601"

AES_KEY = bytes([0x34, 0x52, 0x2A, 0x5B, 0x7A, 0x6E, 0x49, 0x2C, 0x08, 0x09, 0x0A, 0x9D, 0x8D, 0x2A, 0x23, 0xF8])

MODES = {"static": 1, "left": 3, "right": 4, "up": 5, "down": 6, "snowflake": 7}

CELL_WIDTH = 6
# Byte holding rows 0-7 of each cell column, and byte holding rows 8-11 of each column pair
ROW_BYTE = {0: 0, 1: 2, 2: 3, 3: 5, 4: 6, 5: 8}
NIBBLE_BYTE = {0: 1, 1: 1, 2: 4, 3: 4, 4: 7, 5: 7}
# Payload bytes per upload packet; the first byte of each packet holds the length
CHUNK = 15


def encrypt(block: bytes) -> bytes:
    return AES.new(AES_KEY, AES.MODE_ECB).encrypt(block.ljust(16, b"\0"))


def command(name: str, *args: int) -> bytes:
    payload = name.encode("ascii") + bytes(args)
    return encrypt(bytes([len(payload)]) + payload)


def encode_cells(canvas: list[list[int]]) -> bytes:
    """Encode a 12-row canvas in cells of 6 columns x 12 rows, 9 bytes each."""
    width = len(canvas[0])
    data = bytearray()
    for left in range(0, width, CELL_WIDTH):
        cell = bytearray(9)
        for col in range(CELL_WIDTH):
            for row in range(12):
                x = left + col
                if x >= width or not canvas[row][x]:
                    continue
                if row < 8:
                    cell[ROW_BYTE[col]] |= 1 << (7 - row)
                else:
                    # Even columns use the upper nibble, odd columns the lower one
                    shift = (7 if col % 2 == 0 else 3) - (row - 8)
                    cell[NIBBLE_BYTE[col]] |= 1 << shift
        data += cell
    return bytes(data)


class TimHodsonDriver(Driver):
    name = "timhodson"
    # From the badge type string STYPE12X48N; static offset not measured
    display = Display(width=48, height=12)
    modes = tuple(MODES)
    service_uuid = SERVICE_UUID
    notify_characteristics = (NOTIFY,)

    def build_writes(self, pages: list[list[list[int]]], mode: str, speed: int, brightness: int) -> list[Write]:
        # max_messages is 1: the PLAY command may show image sequences, but that is untested
        data = encode_cells(pages[0])
        # Pause after DATS stands in for waiting on the DATSOK notification
        writes = [Write(COMMAND, command("DATS", len(data) >> 8, len(data) & 0xFF, 0, 0), pause=0.5)]
        for offset in range(0, len(data), CHUNK):
            chunk = data[offset:offset + CHUNK]
            writes.append(Write(IMAGE_UPLOAD, encrypt(bytes([len(chunk)]) + chunk), response=False, pause=0.01))
        writes += [
            Write(COMMAND, command("DATCP"), pause=0.1),
            Write(COMMAND, command("MODE", MODES[mode])),
            Write(COMMAND, command("LIGHT", round(brightness * 255 / 100))),
            # Range 0-255 per Tim's notes, direction untested; 1-8 is spread over it
            Write(COMMAND, command("SPEED", round((speed - 1) * 255 / 7))),
        ]
        return writes
