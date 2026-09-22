from itertools import product
from typing import Optional, Sequence

from common.common import HsvColor, Position, add_positions, is_position_out_of_range


class Canvas:
    def __init__(self, matrix, pos0: Position, dimensions: Position):
        if any(v < 0 for v in (*pos0, *dimensions)):
            raise ValueError("Canvas arguments can't be negative")

        end_pos = add_positions(pos0, dimensions)
        for corner in (pos0, end_pos):
            if any(corner[i] > matrix.dimensions[i] for i in (0, 1)):
                raise ValueError(
                    f"Invalid canvas dimensions: {pos0} + {dimensions} is outside matrix dimensions {matrix.dimensions}")

        self._matrix = matrix
        self.dimensions = dimensions
        self.width, self.height = self.dimensions

        self.pos0 = pos0

    def __setitem__(self, index: Position, value: HsvColor):
        if is_position_out_of_range(index, (0, 0), self.dimensions):
            raise ValueError(
                f"Position {index} is out of canvas boundreis - {self.dimensions}")

        self._matrix[[index[i] + self.pos0[i]
                      for i in (1, 0)]] = value

    def fill(self, color: HsvColor):
        for i, j in product(range(self.width), range(self.height)):
            self[i, j] = color

    def draw_color_map(self, color_map: Sequence[Sequence[Optional[HsvColor]]], position: Position = (0, 0)):
        for i, line in enumerate(color_map):
            for j, color in enumerate(line):
                if color:
                    color_pos = add_positions(position, (i, j))
                    self[color_pos] = color

    def draw_shape(self, shape: Sequence[Sequence[bool]], color: HsvColor, position: Position = (0, 0)):
        def shape_iterator():
            for i in shape:
                yield (color if j else None for j in i)

        self.draw_color_map(shape_iterator(), position)

    def draw_borders(self, color: HsvColor, borders: str = "urlb"):
        vertical_line = [[1 for _ in range(self.height)]]
        horizonal_line = [[1] for _ in range(self.width)]

        shape_and_position_map = {
            "u": (horizonal_line, (0, 0)),
            "r": (vertical_line, (0, 0)),
            "l": (vertical_line, (self.width - 1, 0)),
            "b": (horizonal_line, (0, self.height - 1)),
        }

        for border in borders:
            shape, position = shape_and_position_map[border]
            self.draw_shape(shape, color, position)
