"""Use cases shared by the command line and the web server."""
from dataclasses import dataclass

from .core.fonts import load_font, render_text
from .core.i18n import LocalizedError
from .core.render import fits_static, layout, text_width
from .drivers import Driver


@dataclass
class Composition:
    canvas: list[list[int]]
    mode: str
    text_width: int
    autoscrolled: bool


def compose(text: str, font: str, bold: bool, mode: str, autoscroll: bool, driver: Driver) -> Composition:
    """Render the text for the driver's display; with autoscroll, static falls back to left if too wide."""
    if not text:
        raise LocalizedError("err.empty_text")
    if mode not in driver.modes:
        raise LocalizedError("err.mode_unsupported", driver=driver.name, mode=mode, modes=", ".join(driver.modes))
    text_rows = render_text(text, load_font(font), bold)
    autoscrolled = autoscroll and mode == "static" and not fits_static(text_rows, driver.display)
    if autoscrolled:
        mode = "left"
    canvas = layout(text_rows, driver.display, static=mode == "static")
    return Composition(canvas, mode, text_width(text_rows), autoscrolled)
