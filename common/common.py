from functools import reduce
from typing import NewType, Sequence, Tuple


BOARD_DIMS = (20, 10)

Position = NewType('Position', Tuple[int, int])
HsvColor = NewType('HsvColor', Tuple[int, int, int])
RgbColor = NewType('RgbColor', Tuple[int, int, int])


def add_positions(*positions: Sequence[Position]) -> Position:
    return reduce(lambda p0, p1: (p0[0] + p1[0], p0[1] + p1[1]), positions)
