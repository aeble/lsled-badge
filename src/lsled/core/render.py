"""Place rendered text rows on a badge display."""
from dataclasses import dataclass

from .i18n import LocalizedError


@dataclass(frozen=True)
class Display:
    width: int
    height: int
    # Columns the badge shifts static content to the right; those leftmost columns stay unreachable
    static_x_shift: int = 0

    @property
    def static_width(self) -> int:
        return self.width - self.static_x_shift


def text_width(text_rows: list[list[int]]) -> int:
    return len(text_rows[0]) if text_rows else 0


def fits_static(text_rows: list[list[int]], display: Display) -> bool:
    return text_width(text_rows) <= display.static_width


def layout(text_rows: list[list[int]], display: Display, static: bool) -> list[list[int]]:
    """Place the text on the display height.

    Static: centered on a canvas of display.width columns, as the badge shows it.
    Otherwise: a strip as wide as the text, which the badge scrolls.
    """
    height = len(text_rows)
    width = text_width(text_rows)
    if height > display.height:
        raise LocalizedError("err.font_too_tall", height=height, max=display.height)

    if static:
        if not fits_static(text_rows, display):
            raise LocalizedError("err.too_wide", width=width, usable=display.static_width)
        left = max(display.static_x_shift, (display.width - width) // 2)
        canvas_width = display.width
    else:
        left = 0
        canvas_width = width

    top = (display.height - height) // 2
    canvas = [[0] * canvas_width for _ in range(display.height)]
    for y, row in enumerate(text_rows):
        canvas[top + y][left:left + width] = row
    return canvas
