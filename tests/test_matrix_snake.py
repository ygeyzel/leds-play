"""Manual matrix check: a 5x3 rectangle snakes across the whole board, from
the top-left corner to the bottom-right one, changing color as it moves.
Any panel wired in the wrong order/direction shows up as the rectangle
jumping or tearing instead of moving smoothly.

    python -m tests.test_matrix_snake            # on the Pi (needs sudo)
    python -m tests.test_matrix_snake sim        # simulator
"""

import argparse
from itertools import product
from time import sleep

from game.drawer import MATRIX_DPIN, MATRIX_HEIGHT, NUM_OF_MATRICES, SINGLE_MATRIX_WIDTH
from hardware.factory import create_matrix


RECT_WIDTH = 5
RECT_HEIGHT = 3
HUE_STEP = 7
COLOR_SATURATION = 1
COLOR_VALUE = 0.1


def snake_path(max_x: int, max_y: int):
    """Top-left (x, y) corners of the rectangle along the snake: sweep a
    row band left to right, step down to the next band, sweep it right to
    left, and so on. The last band is clamped to the bottom edge."""

    last_x = max_x - RECT_WIDTH
    last_y = max_y - RECT_HEIGHT

    band_ys = list(range(0, last_y + 1, RECT_HEIGHT))
    if band_ys[-1] != last_y:
        band_ys.append(last_y)

    y = 0
    for band, band_y in enumerate(band_ys):
        xs = range(last_x + 1) if band % 2 == 0 else range(last_x, -1, -1)
        x_edge = xs[0]
        while y < band_y:
            yield x_edge, y
            y += 1
        for x in xs:
            yield x, band_y


def parse_args():
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("mode", nargs="?", choices=["rpi", "sim"], default="rpi")
    parser.add_argument("--num-of-matrices", type=int, default=NUM_OF_MATRICES)
    parser.add_argument("--din-pin", type=int, default=MATRIX_DPIN)
    parser.add_argument("--delay", type=float, default=0.03, help="seconds per step")
    return parser.parse_args()


def main():
    args = parse_args()
    matrix = create_matrix(
        args.mode, args.din_pin, SINGLE_MATRIX_WIDTH, MATRIX_HEIGHT, args.num_of_matrices)
    max_y, max_x = matrix.dimensions
    print(f"board is {max_x}x{max_y} (x*y), {args.num_of_matrices} panels")

    try:
        hue = 0
        for x0, y0 in snake_path(max_x, max_y):
            matrix.clear()
            color = (hue, COLOR_SATURATION, COLOR_VALUE)
            for dx, dy in product(range(RECT_WIDTH), range(RECT_HEIGHT)):
                matrix[x0 + dx, y0 + dy] = color
            matrix.show()
            hue = (hue + HUE_STEP) % 360
            sleep(args.delay)

        input("Reached the bottom-right corner. Press Enter to clear\n")
    finally:
        matrix.clear()
        matrix.show()


if __name__ == "__main__":
    main()
