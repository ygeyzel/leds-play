from platforms.interfaces import ScoreDisplay
from platforms.simulator.led_board import LedBoardDisplay
from platforms.simulator.window import SCORE_CELL_GAP, SCORE_CELL_SIZE, get_window


class SimulatorScoreDisplay(ScoreDisplay):
    """Draws score (bottom) and high score (top) on two small 8x32 LED boards
    to the right of the matrix, mirroring the external ESP32 display."""

    def __init__(self):
        self._window = get_window()
        canvas = self._window.canvas

        x, y = self._window.high_score_origin
        self._high_score = LedBoardDisplay(canvas, x, y, SCORE_CELL_SIZE, SCORE_CELL_GAP)

        x, y = self._window.score_origin
        self._score = LedBoardDisplay(canvas, x, y, SCORE_CELL_SIZE, SCORE_CELL_GAP)

    def send_score(self, score, highest):
        self._high_score.set_value(highest)
        self._score.set_value(score)
        self._window.pump()
