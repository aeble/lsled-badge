"""Place rendered text rows on a badge display."""
from dataclasses import dataclass

from .i18n import LocalizedError


@dataclass(frozen=True)
class Display:
    width: int
    height: int


def text_width(text_rows: list[list[int]]) -> int:
    return len(text_rows[0]) if text_rows else 0


def lit_rows(text_rows: list[list[int]]) -> slice:
    """Rows that actually light up; centering these instead of the font box keeps text without
    descenders from sitting high and capitals in fonts with room for accents from sitting low."""
    lit = [y for y, row in enumerate(text_rows) if any(row)]
    return slice(lit[0], lit[-1] + 1) if lit else slice(None)


def layout(text_rows: list[list[int]], display: Display, fixed: bool, x_shift: int = 0) -> list[list[int]]:
    """Place the text on the display height.

    Fixed (the badge shows one screen): centered on a canvas of display.width columns. x_shift is
    how far the badge moves the content to the right; those leftmost columns stay unreachable.
    Otherwise: a strip as wide as the text, which the badge scrolls.
    """
    height = len(text_rows)
    width = text_width(text_rows)
    if height > display.height:
        raise LocalizedError("err.font_too_tall", height=height, max=display.height)

    if fixed:
        usable = display.width - x_shift
        if width > usable:
            raise LocalizedError("err.too_wide", width=width, usable=usable)
        left = max(x_shift, (display.width - width) // 2)
        canvas_width = display.width
    else:
        left = 0
        canvas_width = width

    top = (display.height - height) // 2
    canvas = [[0] * canvas_width for _ in range(display.height)]
    for y, row in enumerate(text_rows):
        canvas[top + y][left:left + width] = row
    return canvas
