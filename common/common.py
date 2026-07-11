from functools import reduce
from typing import NewType, Sequence, Tuple


BOARD_DIMS = (20, 10)

Position = NewType('Position', Tuple[int, int])
HsvColor = NewType('HsvColor', Tuple[int, int, int])
RgbColor = NewType('RgbColor', Tuple[int, int, int])


def add_positions(*positions: Sequence[Position]) -> Position:
    return reduce(lambda p0, p1: (p0[0] + p1[0], p0[1] + p1[1]), positions)


def is_position_out_of_range(pos: Position, pos0: Position, dimensions: Position) -> bool:
    pos1 = add_positions(pos0, dimensions)
    return any(pos[i] not in range(pos0[i], pos1[i]) for i in (0, 1))


def hsv_to_rgb(hsv: HsvColor) -> RgbColor:
    h, s, v = hsv
    c = v * s
    h0 = h / 60
    x = c * (1 - abs((h0 % 2) - 1))
    m = v - c

    rgb0_by_h0 = (
        (c, x, 0),
        (x, c, 0),
        (0, c, x),
        (0, x, c),
        (x, 0, c),
        (c, 0, x)
    )

    rgb0 = rgb0_by_h0[int(h0) - 1]
    return tuple(int((color + m) * 255) for color in rgb0)
