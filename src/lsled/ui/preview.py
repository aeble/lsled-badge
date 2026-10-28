"""Terminal view of a canvas."""


def format_preview(canvas: list[list[int]]) -> str:
    width = len(canvas[0])
    lines = ["┌" + "─" * (2 * width) + "┐"]
    lines += ["│" + "".join("██" if pixel else "  " for pixel in row) + "│" for row in canvas]
    lines.append("└" + "─" * (2 * width) + "┘")
    return "\n".join(lines)
