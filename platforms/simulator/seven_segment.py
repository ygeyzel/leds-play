SEGMENTS = {
    '0': "abcdef",
    '1': "bc",
    '2': "abged",
    '3': "abgcd",
    '4': "fgbc",
    '5': "afgcd",
    '6': "afedcg",
    '7': "abc",
    '8': "abcdefg",
    '9': "abcdfg",
}

LIT_COLOR = "#ff3b1f"
OFF_COLOR = "#241a17"


class _Digit:
    def __init__(self, canvas, x, y, width, height, thickness=6):
        t = thickness
        w, h = width, height
        hh = h / 2

        def hseg(x0, y0, x1):
            return (x0 + t / 2, y0, x1 - t / 2, y0, x1, y0 + t / 2,
                     x1 - t / 2, y0 + t, x0 + t / 2, y0 + t, x0, y0 + t / 2)

        def vseg(x0, y0, y1):
            return (x0, y0 + t / 2, x0 + t / 2, y0, x0 + t, y0 + t / 2,
                     x0 + t, y1 - t / 2, x0 + t / 2, y1, x0, y1 - t / 2)

        coords = {
            'a': hseg(x, y, x + w),
            'g': hseg(x, y + hh - t / 2, x + w),
            'd': hseg(x, y + h - t, x + w),
            'f': vseg(x, y, y + hh),
            'e': vseg(x, y + hh, y + h),
            'b': vseg(x + w - t, y, y + hh),
            'c': vseg(x + w - t, y + hh, y + h),
        }

        self._canvas = canvas
        self._ids = {
            seg: canvas.create_polygon(*pts, fill=OFF_COLOR, outline="")
            for seg, pts in coords.items()
        }

    def set_char(self, char: str):
        lit = SEGMENTS.get(char, "")
        for seg, item in self._ids.items():
            self._canvas.itemconfig(item, fill=LIT_COLOR if seg in lit else OFF_COLOR)


class SevenSegmentDisplay:
    def __init__(self, canvas, x, y, num_digits=6, digit_width=26,
                 digit_height=46, gap=8):
        self._num_digits = num_digits
        self._digits = [
            _Digit(canvas, x + i * (digit_width + gap), y, digit_width, digit_height)
            for i in range(num_digits)
        ]

    def set_value(self, value: int):
        text = str(max(0, int(value)))[-self._num_digits:].rjust(self._num_digits)
        for char, digit in zip(text, self._digits):
            digit.set_char(char.strip())
