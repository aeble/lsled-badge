"""LSLED badges (service fee0, characteristic fee1) with the plaintext "wang" protocol."""
from datetime import datetime

from ..core.render import Display
from .base import Driver, Write

SERVICE_UUID = "0000fee0-0000-1000-8000-00805f9b34fb"
CHAR_UUID = "0000fee1-0000-1000-8000-00805f9b34fb"

MODES = {
    "left": 0,
    "right": 1,
    "up": 2,
    "down": 3,
    "static": 4,
    "animation": 5,
    "snowflake": 6,
    "picture": 7,
    "laser": 8,
}
# Header byte 5, by percent
BRIGHTNESS = {100: 0x00, 75: 0x10, 50: 0x20, 25: 0x40}


def encode_tiles(canvas: list[list[int]]) -> tuple[bytes, int]:
    """Split the canvas into tiles 8 columns wide, 11 bytes each (one byte per row)."""
    tiles = (len(canvas[0]) + 7) // 8
    bitmap = bytearray()
    for tile in range(tiles):
        for row in canvas:
            byte = 0
            for pixel in row[tile * 8:tile * 8 + 8]:
                byte = (byte << 1) | pixel
            byte <<= 8 - len(row[tile * 8:tile * 8 + 8])
            bitmap.append(byte)
    return bytes(bitmap), tiles


class LsledDriver(Driver):
    name = "lsled"
    # Measured on a 44x11 badge: in static mode, bitmap column n appears on display column n+2
    display = Display(width=44, height=11, static_x_shift=2)
    modes = tuple(MODES)
    service_uuid = SERVICE_UUID
    name_prefixes = ("LSLED",)

    def build_writes(self, canvas: list[list[int]], mode: str, speed: int, brightness: int) -> list[Write]:
        if mode == "static":
            canvas = [row[self.display.static_x_shift:] for row in canvas]
        bitmap, tiles = encode_tiles(canvas)
        # The badge only knows four steps; take the nearest, ties go to the brighter one
        level = min(BRIGHTNESS, key=lambda step: (abs(step - brightness), -step))

        now = datetime.now()
        header = bytearray(64)
        header[0:4] = b"wang"
        header[5] = BRIGHTNESS[level]
        header[8] = (speed - 1) << 4 | MODES[mode]  # message 1
        header[16:18] = tiles.to_bytes(2, "big")  # length of message 1 in tiles
        header[38:44] = bytes([now.year % 100, now.month, now.day, now.hour, now.minute, now.second])

        data = bytes(header) + bitmap
        data += bytes(-len(data) % 16)
        return [Write(CHAR_UUID, data[i:i + 16]) for i in range(0, len(data), 16)]
