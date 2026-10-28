"""Use cases shared by the command line and the web server."""
from dataclasses import dataclass

from .core.fonts import Font, load_font, render_text
from .core.i18n import LocalizedError
from .core.render import layout, lit_rows, text_width
from .drivers import Driver

# What to do with text too wide for a one-screen mode
OVERFLOW = ("error", "scroll", "pages")


@dataclass
class Composition:
    # One canvas per message; more than one only when the text was split into pages
    pages: list[list[list[int]]]
    mode: str
    text_width: int
    autoscrolled: bool
    # Columns usable in a one-screen mode; None when the badge scrolls the text
    usable_width: int | None


def split_pages(text: str, font: Font, bold: bool, usable: int) -> list[list[list[int]]]:
    """Break the text at spaces into pages that each fit into usable columns."""
    pages: list[str] = []
    for word in text.split():
        candidate = f"{pages[-1]} {word}" if pages else word
        if pages and text_width(render_text(candidate, font, bold)) <= usable:
            pages[-1] = candidate
            continue
        width = text_width(render_text(word, font, bold))
        if width > usable:
            raise LocalizedError("err.word_too_wide", word=word, width=width, usable=usable)
        pages.append(word)
    return [render_text(page, font, bold) for page in pages]


def compose(text: str, font: str, bold: bool, mode: str, overflow: str, driver: Driver) -> Composition:
    """Render the text for the driver's display, handling text too wide for one-screen modes per overflow."""
    if not text.strip():
        raise LocalizedError("err.empty_text")
    if mode not in driver.modes:
        raise LocalizedError("err.mode_unsupported", driver=driver.name, mode=mode, modes=", ".join(driver.modes))
    loaded = load_font(font)
    text_rows = render_text(text, loaded, bold)
    width = text_width(text_rows)
    too_wide = driver.is_fixed(mode) and width > driver.usable_width(mode)

    autoscrolled = too_wide and overflow == "scroll"
    if autoscrolled:
        mode = "left"
    pages = [text_rows]
    if too_wide and overflow == "pages":
        pages = split_pages(text, loaded, bold, driver.usable_width(mode))
        if len(pages) > driver.max_messages:
            raise LocalizedError("err.too_many_pages", count=len(pages), max=driver.max_messages)

    # Trim every page to the rows lit in the whole text, so all pages share one baseline
    rows_used = lit_rows(text_rows)
    fixed = driver.is_fixed(mode)
    canvases = [layout(rows[rows_used], driver.display, fixed, driver.x_shift.get(mode, 0)) for rows in pages]
    return Composition(canvases, mode, width, autoscrolled, driver.usable_width(mode) if fixed else None)
