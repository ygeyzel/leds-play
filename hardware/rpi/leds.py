from rpi_ws281x import Color, PixelStrip

from common.common import Position, HsvColor, hsv_to_rgb, is_position_out_of_range
from hardware.interfaces import Matrix


class DualMatrix(Matrix):
    def __init__(self, din_pin: int, matrix_max_x: int, matrix_max_y: int):
        self.matrix_max_x = matrix_max_x
        self.max_y = matrix_max_y
        self.max_x = matrix_max_x * 2
        self.leds_num = self.max_x * self.max_y

        self._leds = PixelStrip(self.leds_num, din_pin)
        self._leds.begin()

    # for external usage
    @property
    def dimensions(self) -> Position:
        return (self.max_y, self.max_x)

    # for internal usage
    @property
    def _dimensions(self) -> Position:
        return (self.max_x, self.max_y)

    def _get_linear_position(self, position: Position) -> int:
        x, y = position
        if x >= self.matrix_max_x:
            x -= self.matrix_max_x
            y += self.max_y

        if y % 2 == 0:
            x = self.matrix_max_x - x - 1

        return x + (y * self.matrix_max_x)

    def __setitem__(self, index: Position, value: HsvColor):
        if is_position_out_of_range(index, (0, 0), self._dimensions):
            raise ValueError(
                f"Position {index} is out of matrix boundreis - {self.max_x, self.max_y}")
        linear_position = self._get_linear_position(index)
        self._leds[linear_position] = Color(*hsv_to_rgb(value))

    def clear(self):
        self._leds[:] = Color(0, 0, 0)

    def show(self):
        self._leds.show()
