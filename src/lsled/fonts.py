"""Load bitmap fonts and render text into pixel rows."""
import json
from dataclasses import dataclass
from pathlib import Path

from .i18n import t

FONT_DIR = Path(__file__).parent / "fonts"


@dataclass
class Font:
    name: str
    description: str
    height: int
    glyphs: dict[str, list[str]]

    def glyph(self, char: str) -> list[str] | None:
        # Fonts without lower case show the capital letter instead
        return self.glyphs.get(char) or self.glyphs.get(char.upper())


def available_fonts() -> list[str]:
    return sorted(path.stem for path in FONT_DIR.glob("*.json"))


def read_font_file(name: str) -> dict:
    path = FONT_DIR / f"{name}.json"
    if not path.exists():
        raise ValueError(t("err.unknown_font", name=name, fonts=", ".join(available_fonts())))
    return json.loads(path.read_text(encoding="utf-8"))


def load_font(name: str) -> Font:
    data = read_font_file(name)
    return Font(name=name, description=data["description"], height=data["height"], glyphs=data["glyphs"])


def render_text(text: str, font: Font, bold: bool = False) -> list[list[int]]:
    """Set the text with one empty column between glyphs; returns font.height pixel rows."""
    missing = sorted({char for char in text if font.glyph(char) is None})
    if missing:
        raise ValueError(t("err.missing_glyphs", font=font.name, chars="".join(missing)))

    rows: list[list[int]] = [[] for _ in range(font.height)]
    for index, char in enumerate(text):
        for y, pattern in enumerate(font.glyph(char)):
            bits = [1 if pixel == "#" else 0 for pixel in pattern]
            if bold:
                # Bold: additionally set every pixel one column to the right
                bits = [a | b for a, b in zip(bits + [0], [0] + bits)]
            if index:
                rows[y].append(0)
            rows[y].extend(bits)
    return rows
