from common.common import HsvColor, Position, hsv_to_rgb, is_position_out_of_range
from hardware.interfaces import Matrix
from hardware.simulator.window import get_window


UNLIT_COLOR = "#000000"
BRIGTHNESS_FACTOR = 5


class SimulatorMatrix(Matrix):
    """Pixel-perfect stand-in for DualMatrix: same dimensions, same
    (x, y)-addressed __setitem__, rendered as a tkinter pixel grid instead
    of driving real WS281x LEDs."""

    def __init__(self, matrix_max_x: int, matrix_max_y: int):
        self.matrix_max_x = matrix_max_x
        self.max_y = matrix_max_y
        self.max_x = matrix_max_x * 2

        self._window = get_window(self.dimensions)
        self._pending = {}

        canvas = self._window.canvas
        self._pixel_ids = {}
        for x in range(self.max_x):
            for y in range(self.max_y):
                x0, y0, x1, y1 = self._window.pixel_rect(x, y)
                self._pixel_ids[(x, y)] = canvas.create_rectangle(
                    x0, y0, x1, y1, fill=UNLIT_COLOR, width=0)

    @property
    def dimensions(self) -> Position:
        return (self.max_y, self.max_x)

    @property
    def _dimensions(self) -> Position:
        return (self.max_x, self.max_y)

    def __setitem__(self, index: Position, value: HsvColor):
        if is_position_out_of_range(index, (0, 0), self._dimensions):
            raise ValueError(
                f"Position {index} is out of matrix boundreis - {self.max_x, self.max_y}")
        self._pending[tuple(index)] = value

    def clear(self):
        for pos in self._pixel_ids:
            self._pending[pos] = None

    def show(self):
        canvas = self._window.canvas
        for pos, value in self._pending.items():
            adjusted_value = (value[0], value[1], min(value[2] * BRIGTHNESS_FACTOR, 1)) if value else None
            color = ("#%02x%02x%02x" % hsv_to_rgb(adjusted_value)) if value else UNLIT_COLOR
            canvas.itemconfig(self._pixel_ids[pos], fill=color)
        self._pending.clear()
        self._window.pump()
