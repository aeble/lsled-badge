"""Convert figlet fonts (.flf) into our JSON font format.

Only useful for fonts that draw pixels with a fill character, such as those in
figlet/fonts/bdffonts. Every character except space and hardblank counts as a pixel.
"""
from pathlib import Path

from .i18n import LocalizedError

# Required characters of every .flf file after ASCII 32-126, in this order
GERMAN_CODES = [196, 214, 220, 228, 246, 252, 223]


def parse_code(token: str) -> int:
    if token.lower().startswith(("0x", "-0x")):
        return int(token, 16)
    if token.startswith("0") and len(token) > 1:
        return int(token, 8)
    return int(token)


def read_flf(path: Path) -> tuple[int, dict[int, list[str]], str]:
    lines = path.read_text(encoding="latin-1").splitlines()
    header = lines[0].split()
    if not header[0].startswith("flf2a"):
        raise LocalizedError("err.not_flf", path=path)
    hardblank = header[0][5]
    height = int(header[1])
    comment_lines = int(header[5])
    # The comment block carries copyright and license notices, which must travel with the font
    comment = "\n".join(line.rstrip() for line in lines[1:1 + comment_lines])

    def glyph_at(start: int) -> list[str]:
        rows = []
        for line in lines[start:start + height]:
            endmark = line[-1] if line else "@"
            rows.append(line.rstrip(endmark).replace(hardblank, " "))
        return rows

    glyphs = {}
    position = 1 + comment_lines
    for code in [*range(32, 127), *GERMAN_CODES]:
        glyphs[code] = glyph_at(position)
        position += height
    # Optional characters follow, each preceded by a code line ("196 Adieresis")
    while position + height < len(lines) + 1 and lines[position].strip():
        code = parse_code(lines[position].split()[0])
        if 32 <= code < 127 or code >= 160:
            glyphs[code] = glyph_at(position + 1)
        position += 1 + height
    return height, glyphs, comment


def convert_flf(path: Path, max_height: int) -> dict:
    height, raw, comment = read_flf(path)
    pixels = {code: [[ch != " " for ch in row] for row in rows] for code, rows in raw.items()}

    # Drop rows at top and bottom that no glyph uses
    used_rows = [y for y in range(height) if any(any(rows[y]) for rows in pixels.values() if y < len(rows))]
    if not used_rows:
        raise LocalizedError("err.no_pixels", path=path)
    top, bottom = used_rows[0], used_rows[-1] + 1
    if bottom - top > max_height:
        raise LocalizedError("err.font_too_tall", height=bottom - top, max=max_height)

    glyphs = {}
    for code, rows in pixels.items():
        rows = rows[top:bottom]
        width = max((len(row) for row in rows), default=0)
        rows = [row + [False] * (width - len(row)) for row in rows]
        used_cols = [x for x in range(width) if any(row[x] for row in rows)]
        if used_cols:
            # Strip empty side columns: the renderer adds its own one-column gap
            left, right = used_cols[0], used_cols[-1] + 1
        elif code == 32:
            left, right = 0, max(1, width // 2)
        else:
            continue  # glyph is empty in this font
        glyphs[chr(code)] = ["".join("#" if pixel else "." for pixel in row[left:right]) for row in rows]

    return {
        "description": f"figlet {path.name}" + (f": {comment.splitlines()[0]}" if comment else ""),
        "notice": comment,
        "height": bottom - top,
        "glyphs": glyphs,
    }
