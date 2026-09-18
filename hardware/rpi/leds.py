from time import monotonic, sleep

from adafruit_raspberry_pi5_neopixel_write import neopixel_write

from common.common import Position, HsvColor, hsv_to_rgb, is_position_out_of_range
from hardware.interfaces import Matrix


DEFAULT_DIN_PIN = 4
DEFAULT_NUM_OF_MATRICES = 4
PANEL_MAX_X = 8
PANEL_MAX_Y = 32
BYTES_PER_LED = 3
# WS2812 wire time is 1.25us per bit, and the LEDs only latch a frame after
# the data line has been idle for a while (>280us on newer WS2812B; we
# leave some margin).
SECONDS_PER_LED = BYTES_PER_LED * 8 * 1.25e-6
LATCH_SECONDS = 1e-3


class _Gpio:
    """The minimal pin object neopixel_write expects (it only reads `.id`),
    so we don't need all of Blinka's `board` module for one pin number."""

    def __init__(self, pin: int):
        self.id = pin


class ChainedMatrix(Matrix):
    """A number of WS281x panels concatenated into one LED strip and
    addressed as a single matrix, panels laid side by side along x.

    Each panel is a snake-shaped strip: it runs row by row along y,
    alternating x direction every row. Every panel's x- and y-axes are reversed
    relative to the previous one (the panel is rotated 180 degrees), so the
    chain snakes panel to panel too.

    Driven through the Raspberry Pi 5's RP1 PIO (`/dev/pio0`), since
    rpi_ws281x doesn't support the Pi 5.
    """

    def __init__(
        self, din_pin: int = DEFAULT_DIN_PIN, num_of_matrices: int = DEFAULT_NUM_OF_MATRICES,
        matrix_max_x: int = PANEL_MAX_X, matrix_max_y: int = PANEL_MAX_Y,
    ):
        self.matrix_max_x = matrix_max_x
        self.num_of_matrices = num_of_matrices
        self.max_y = matrix_max_y
        self.max_x = matrix_max_x * num_of_matrices
        self.leds_per_matrix = matrix_max_x * matrix_max_y
        self.leds_num = self.leds_per_matrix * num_of_matrices

        self._gpio = _Gpio(din_pin)
        self._buffer = bytearray(self.leds_num * BYTES_PER_LED)
        self._frame_seconds = self.leds_num * SECONDS_PER_LED + LATCH_SECONDS
        self._next_frame_at = 0.0

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
        matrix_index, x = divmod(x, self.matrix_max_x)

        if matrix_index % 2 == 1:
            x = self.matrix_max_x - x - 1
            y = self.max_y - y - 1

        if y % 2 == 0:
            x = self.matrix_max_x - x - 1

        return matrix_index * self.leds_per_matrix + y * self.matrix_max_x + x

    def __setitem__(self, index: Position, value: HsvColor):
        if is_position_out_of_range(index, (0, 0), self._dimensions):
            raise ValueError(
                f"Position {index} is out of matrix boundreis - {self.max_x, self.max_y}")
        r, g, b = hsv_to_rgb(value)
        offset = self._get_linear_position(index) * BYTES_PER_LED
        # WS2812 LEDs take their color bytes in GRB order
        self._buffer[offset:offset + BYTES_PER_LED] = bytes((g, r, b))

    def clear(self):
        self._buffer[:] = bytes(len(self._buffer))

    def show(self):
        # neopixel_write only queues the frame and returns long before it's
        # on the wire. Writing again before it's been sent and latched just
        # streams both frames back to back, so none of them gets displayed.
        if (wait := self._next_frame_at - monotonic()) > 0:
            sleep(wait)
        neopixel_write(self._gpio, self._buffer)
        self._next_frame_at = monotonic() + self._frame_seconds
