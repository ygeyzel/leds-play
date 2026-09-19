import colorsys
import os
from typing import List, Optional

from PIL import Image

from common.common import HsvColor, Position


def load_logo(path: Optional[str], size: Position) -> Optional[List[List[Optional[HsvColor]]]]:
    """Decode the PNG at `path` and nearest-neighbor resize it to `size`
    (rows, cols), returning a `size`-shaped grid of `HsvColor` (or None for
    transparent pixels) - the same shape `Canvas.draw_color_map` expects.
    Returns None (no logo to draw) if `path` is unset or missing, so a game
    without a logo.png yet degrades gracefully instead of crashing."""

    if not path or not os.path.exists(path):
        return None

    rows, cols = size
    image = Image.open(path).convert("RGBA").resize((cols, rows), Image.NEAREST)

    grid = []
    for y in range(rows):
        row = []
        for x in range(cols):
            r, g, b, a = image.getpixel((x, y))
            row.append(_rgb_to_hsv(r, g, b) if a > 0 else None)
        grid.append(row)
    return grid


def _rgb_to_hsv(r: int, g: int, b: int) -> HsvColor:
    h, s, v = colorsys.rgb_to_hsv(r / 255, g / 255, b / 255)
    return (h * 360, s, v)
