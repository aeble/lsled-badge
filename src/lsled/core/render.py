"""Place rendered text rows on a badge display."""
from dataclasses import dataclass

from .i18n import LocalizedError


@dataclass(frozen=True)
class Display:
    width: int
    height: int


def text_width(text_rows: list[list[int]]) -> int:
    return len(text_rows[0]) if text_rows else 0


def place_vertically(text_rows: list[list[int]], baseline: int, height: int) -> tuple[slice, int]:
    """Rows to keep and the display row of the first one.

    Centers what stands on the baseline; descenders hang below, and if they would touch the bottom
    edge, everything moves up so one row stays free under them. Centering the font box instead
    would put text without descenders high and capitals in fonts with room for accents low.
    """
    lit = [y for y, row in enumerate(text_rows) if any(row)]
    if not lit:
        return slice(None), (height - len(text_rows)) // 2
    first, last = lit[0], lit[-1]
    body = min(max(baseline, first), last) - first + 1
    span = last - first + 1
    margin = 1 if span <= height - 2 else 0
    top = min((height - body) // 2, height - margin - span)
    return slice(first, last + 1), top


def layout(
    text_rows: list[list[int]], display: Display, fixed: bool, top: int | None = None
) -> list[list[int]]:
    """Place the text on the display height.

    Fixed (the badge shows one screen): centered on a canvas of display.width columns.
    Otherwise: a strip as wide as the text, which the badge scrolls.
    top: display row of the first text row; centered if None.
    """
    height = len(text_rows)
    width = text_width(text_rows)
    if height > display.height:
        raise LocalizedError("err.font_too_tall", height=height, max=display.height)

    if fixed:
        if width > display.width:
            raise LocalizedError("err.too_wide", width=width, usable=display.width)
        left = (display.width - width) // 2
        canvas_width = display.width
    else:
        left = 0
        canvas_width = width

    if top is None:
        top = (display.height - height) // 2
    canvas = [[0] * canvas_width for _ in range(display.height)]
    for y, row in enumerate(text_rows):
        canvas[top + y][left:left + width] = row
    return canvas
