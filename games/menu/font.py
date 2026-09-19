"""A tiny 3x5 pixel font, just enough to spell game names on the banner."""

from typing import List

FONT_HEIGHT = 5
FONT_WIDTH = 3

_GLYPHS = {
    "A": ["010", "101", "111", "101", "101"],
    "B": ["110", "101", "110", "101", "110"],
    "C": ["011", "100", "100", "100", "011"],
    "D": ["110", "101", "101", "101", "110"],
    "E": ["111", "100", "110", "100", "111"],
    "F": ["111", "100", "110", "100", "100"],
    "G": ["011", "100", "101", "101", "011"],
    "H": ["101", "101", "111", "101", "101"],
    "I": ["111", "010", "010", "010", "111"],
    "J": ["001", "001", "001", "101", "010"],
    "K": ["101", "101", "110", "101", "101"],
    "L": ["100", "100", "100", "100", "111"],
    "M": ["101", "111", "111", "101", "101"],
    "N": ["101", "111", "111", "111", "101"],
    "O": ["010", "101", "101", "101", "010"],
    "P": ["110", "101", "110", "100", "100"],
    "Q": ["010", "101", "101", "111", "011"],
    "R": ["110", "101", "110", "101", "101"],
    "S": ["011", "100", "010", "001", "110"],
    "T": ["111", "010", "010", "010", "010"],
    "U": ["101", "101", "101", "101", "111"],
    "V": ["101", "101", "101", "101", "010"],
    "W": ["101", "101", "111", "111", "101"],
    "X": ["101", "101", "010", "101", "101"],
    "Y": ["101", "101", "010", "010", "010"],
    "Z": ["111", "001", "010", "100", "111"],
    "0": ["111", "101", "101", "101", "111"],
    "1": ["010", "110", "010", "010", "111"],
    "2": ["111", "001", "111", "100", "111"],
    "3": ["111", "001", "111", "001", "111"],
    "4": ["101", "101", "111", "001", "001"],
    "5": ["111", "100", "111", "001", "111"],
    "6": ["111", "100", "111", "101", "111"],
    "7": ["111", "001", "001", "001", "001"],
    "8": ["111", "101", "111", "101", "111"],
    "9": ["111", "101", "111", "001", "111"],
    " ": ["000", "000", "000", "000", "000"],
}


def glyph_shape(char: str) -> List[List[bool]]:
    """A FONT_HEIGHT x FONT_WIDTH boolean shape for `char`, in the row-major
    form `Canvas.draw_shape` expects. Unknown characters render blank."""

    rows = _GLYPHS.get(char.upper(), _GLYPHS[" "])
    return [[c == "1" for c in row] for row in rows]


def text_shape(text: str, gap: int = 1) -> List[List[bool]]:
    """A FONT_HEIGHT x (len(text) * (FONT_WIDTH + gap) - gap) boolean shape
    spelling out `text`, letters separated by `gap` blank columns."""

    glyphs = [glyph_shape(c) for c in text]
    spacer = [[False] * gap] * FONT_HEIGHT

    rows = [[] for _ in range(FONT_HEIGHT)]
    for i, glyph in enumerate(glyphs):
        if i:
            for row, pad_row in zip(rows, spacer):
                row.extend(pad_row)
        for row, glyph_row in zip(rows, glyph):
            row.extend(glyph_row)
    return rows
