"""Simulated 8x32 LED score boards, mirroring the ESP32 firmware in
leds-play-score-board: each board shows up to 8 digits of a 3x7 font with a
1px gap, right-aligned."""

# Mirror of kFont3x7 in Font3x7.h (leds-play-score-board): '0'..'9' then '-',
# 3 columns per glyph, one byte per column, bit 0 = top row.
FONT_3X7 = (
    0x7F, 0x41, 0x7F,  # '0'
    0x00, 0x00, 0x7F,  # '1'
    0x79, 0x49, 0x4F,  # '2'
    0x49, 0x49, 0x7F,  # '3'
    0x0F, 0x08, 0x7F,  # '4'
    0x4F, 0x49, 0x79,  # '5'
    0x7F, 0x49, 0x79,  # '6'
    0x01, 0x01, 0x7F,  # '7'
    0x7F, 0x49, 0x7F,  # '8'
    0x4F, 0x49, 0x7F,  # '9'
    0x08, 0x08, 0x08,  # '-'
)
MINUS_INDEX = 10

ROWS = 8
COLS = 32
GLYPH_WIDTH = 3
GLYPH_GAP = 1
NUM_DIGITS = COLS // (GLYPH_WIDTH + GLYPH_GAP)

LIT_COLOR = "#ff3b1f"
OFF_COLOR = "#241a17"


class LedBoardDisplay:
    def __init__(self, canvas, x, y, cell_size, cell_gap):
        self._canvas = canvas
        self._cells = {}
        for col in range(COLS):
            for row in range(ROWS):
                x0 = x + col * cell_size + cell_gap / 2
                y0 = y + row * cell_size + cell_gap / 2
                self._cells[(col, row)] = canvas.create_rectangle(
                    x0, y0, x0 + cell_size - cell_gap, y0 + cell_size - cell_gap,
                    fill=OFF_COLOR, width=0)
        self._lit = set()

    def set_value(self, value: int):
        text = str(max(0, int(value)))[-NUM_DIGITS:]
        lit = set()
        left = COLS - (len(text) * (GLYPH_WIDTH + GLYPH_GAP) - GLYPH_GAP)
        for i, char in enumerate(text):
            index = MINUS_INDEX if char == '-' else int(char)
            glyph = FONT_3X7[index * GLYPH_WIDTH:(index + 1) * GLYPH_WIDTH]
            for dx, column in enumerate(glyph):
                for row in range(ROWS):
                    if column & (1 << row):
                        lit.add((left + i * (GLYPH_WIDTH + GLYPH_GAP) + dx, row))
        for pos in lit ^ self._lit:
            self._canvas.itemconfig(
                self._cells[pos], fill=LIT_COLOR if pos in lit else OFF_COLOR)
        self._lit = lit
