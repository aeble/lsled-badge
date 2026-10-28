"""Display layout and "wang" packet format of LSLED badges."""
from datetime import datetime

from .i18n import t

SERVICE_UUID = "0000fee0-0000-1000-8000-00805f9b34fb"
CHAR_UUID = "0000fee1-0000-1000-8000-00805f9b34fb"

DISPLAY_WIDTH = 44
DISPLAY_HEIGHT = 11
# Measured: in static mode, bitmap column n appears on display column n+2.
# Display columns 0 and 1 are therefore unreachable in static mode.
STATIC_X_SHIFT = 2

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
SPEEDS = range(1, 9)


def fits_static(width: int) -> bool:
    return width <= DISPLAY_WIDTH - STATIC_X_SHIFT


def layout(text_rows: list[list[int]], mode: str) -> list[list[int]]:
    """Place the text on the display height.

    Static: centered on a canvas of DISPLAY_WIDTH columns, as the badge shows it.
    Otherwise: a strip as wide as the text, which the badge scrolls.
    """
    height = len(text_rows)
    width = len(text_rows[0]) if text_rows else 0
    if height > DISPLAY_HEIGHT:
        raise ValueError(t("err.font_too_tall", height=height, max=DISPLAY_HEIGHT))

    if mode == "static":
        if not fits_static(width):
            raise ValueError(t("err.too_wide", width=width, usable=DISPLAY_WIDTH - STATIC_X_SHIFT))
        left = max(STATIC_X_SHIFT, (DISPLAY_WIDTH - width) // 2)
        canvas_width = DISPLAY_WIDTH
    else:
        left = 0
        canvas_width = width

    top = (DISPLAY_HEIGHT - height) // 2
    canvas = [[0] * canvas_width for _ in range(DISPLAY_HEIGHT)]
    for y, row in enumerate(text_rows):
        canvas[top + y][left:left + width] = row
    return canvas


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


def build_packets(canvas: list[list[int]], mode: str, speed: int, brightness: int) -> list[bytes]:
    if mode == "static":
        canvas = [row[STATIC_X_SHIFT:] for row in canvas]
    bitmap, tiles = encode_tiles(canvas)

    now = datetime.now()
    header = bytearray(64)
    header[0:4] = b"wang"
    header[5] = BRIGHTNESS[brightness]
    header[8] = (speed - 1) << 4 | MODES[mode]  # message 1
    header[16:18] = tiles.to_bytes(2, "big")  # length of message 1 in tiles
    header[38:44] = bytes([now.year % 100, now.month, now.day, now.hour, now.minute, now.second])

    data = bytes(header) + bitmap
    data += bytes(-len(data) % 16)
    return [data[i:i + 16] for i in range(0, len(data), 16)]


def format_preview(canvas: list[list[int]]) -> str:
    width = len(canvas[0])
    lines = ["┌" + "─" * (2 * width) + "┐"]
    lines += ["│" + "".join("██" if pixel else "  " for pixel in row) + "│" for row in canvas]
    lines.append("└" + "─" * (2 * width) + "┘")
    return "\n".join(lines)
