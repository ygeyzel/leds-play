from hardware.interfaces import ScoreDisplay
from hardware.simulator.seven_segment import SevenSegmentDisplay
from hardware.simulator.window import get_window


class SimulatorScoreDisplay(ScoreDisplay):
    """Draws score (bottom) and high score (top) as 7-segment digits to
    the right of the matrix, mirroring the external ESP32 display."""

    def __init__(self):
        self._window = get_window()
        canvas = self._window.canvas

        x, y = self._window.high_score_origin
        self._high_score = SevenSegmentDisplay(canvas, x, y)

        x, y = self._window.score_origin
        self._score = SevenSegmentDisplay(canvas, x, y)

    def send_score(self, score, highest):
        self._high_score.set_value(highest)
        self._score.set_value(score)
        self._window.pump()
