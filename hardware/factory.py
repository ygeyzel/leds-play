from typing import Optional

from common.common import Position
from hardware.interfaces import KeyHandler, Matrix, ScoreDisplay


def create_matrix(
    mode: str, din_pin: int, matrix_max_x: int, matrix_max_y: int,
    num_of_matrices: int = 2, *, banner_dims: Optional[Position] = None,
) -> Matrix:
    if mode == "rpi":
        from hardware.rpi.leds import DualMatrix
        if num_of_matrices != 2:
            print(
                f"warning: rpi backend doesn't support --num-of-matrices yet "
                f"(always chains 2 panels); ignoring requested {num_of_matrices}")
        return DualMatrix(din_pin, matrix_max_x, matrix_max_y)

    from hardware.simulator.leds import SimulatorMatrix
    return SimulatorMatrix(
        matrix_max_x, matrix_max_y, num_of_matrices,
        region="board", banner_dims=banner_dims)


def create_banner_matrix(
    mode: str, din_pin: int, matrix_max_x: int, matrix_max_y: int, num_of_matrices: int,
) -> Optional[Matrix]:
    """A second, independent LED matrix for the banner area. Not yet
    supported on real hardware (rpi mode) - only the simulator can show one
    so far, so rpi mode gets no banner (None) rather than a crash."""

    if mode == "rpi":
        if num_of_matrices:
            print(
                "warning: rpi backend doesn't support a banner display yet; "
                f"ignoring requested --size-of-banner {num_of_matrices}")
        return None

    from hardware.simulator.leds import SimulatorMatrix
    return SimulatorMatrix(matrix_max_x, matrix_max_y, num_of_matrices, region="banner")


def create_key_handler(mode: str) -> KeyHandler:
    if mode == "rpi":
        from hardware.rpi.keys import RpiKeyHandler
        return RpiKeyHandler()

    from hardware.simulator.keys import SimulatorKeyHandler
    return SimulatorKeyHandler()


def create_score_display(mode: str) -> ScoreDisplay:
    if mode == "rpi":
        from hardware.rpi.score import SerialScoreDisplay
        return SerialScoreDisplay()

    from hardware.simulator.score import SimulatorScoreDisplay
    return SimulatorScoreDisplay()
