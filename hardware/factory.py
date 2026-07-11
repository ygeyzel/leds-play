from hardware.interfaces import KeyHandler, Matrix, ScoreDisplay


def create_matrix(mode: str, din_pin: int, matrix_max_x: int, matrix_max_y: int) -> Matrix:
    if mode == "rpi":
        from hardware.rpi.leds import DualMatrix
        return DualMatrix(din_pin, matrix_max_x, matrix_max_y)

    from hardware.simulator.leds import SimulatorMatrix
    return SimulatorMatrix(matrix_max_x, matrix_max_y)


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
