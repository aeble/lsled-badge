"""Use cases shared by the command line and the web server."""
from dataclasses import dataclass

from .core.fonts import load_font, render_text
from .core.i18n import LocalizedError
from .core.render import layout, text_width
from .drivers import Driver


@dataclass
class Composition:
    canvas: list[list[int]]
    mode: str
    text_width: int
    autoscrolled: bool
    # Columns usable in a one-screen mode; None when the badge scrolls the text
    usable_width: int | None


def compose(text: str, font: str, bold: bool, mode: str, autoscroll: bool, driver: Driver) -> Composition:
    """Render the text for the driver's display; with autoscroll, one-screen modes fall back to left if too wide."""
    if not text:
        raise LocalizedError("err.empty_text")
    if mode not in driver.modes:
        raise LocalizedError("err.mode_unsupported", driver=driver.name, mode=mode, modes=", ".join(driver.modes))
    text_rows = render_text(text, load_font(font), bold)
    width = text_width(text_rows)
    autoscrolled = autoscroll and driver.is_fixed(mode) and width > driver.usable_width(mode)
    if autoscrolled:
        mode = "left"
    fixed = driver.is_fixed(mode)
    canvas = layout(text_rows, driver.display, fixed, driver.x_shift.get(mode, 0))
    return Composition(canvas, mode, width, autoscrolled, driver.usable_width(mode) if fixed else None)
