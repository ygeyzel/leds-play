import tkinter as tk
from typing import Optional

from common.common import Position


CELL_SIZE = 18
CELL_GAP = 2

BG_COLOR = "#000000"

PANEL_PADDING = 24
SIDE_PANEL_WIDTH = 220

DIGIT_WIDTH = 26
DIGIT_HEIGHT = 46
DIGIT_ROW_GAP = 24

BUTTONS_TOP_GAP = 100
BUTTON_LEFT_GAP = 60


class SimulatorWindow:
    """A single Tk window shared by the simulator's matrix, key and score
    backends: one physical window standing in for the whole rig."""

    def __init__(self, matrix_dims: Position):
        rows, cols = matrix_dims

        matrix_width = cols * CELL_SIZE
        matrix_height = rows * CELL_SIZE

        side_x = matrix_width + PANEL_PADDING
        content_height = (
            DIGIT_HEIGHT * 2 + DIGIT_ROW_GAP + BUTTONS_TOP_GAP + 3 * (40 + 8)
        )

        self.matrix_origin = (0, 0)
        self.high_score_origin = (side_x, 24)
        self.score_origin = (side_x, 24 + DIGIT_HEIGHT + DIGIT_ROW_GAP)
        self.buttons_origin = (
            side_x + BUTTON_LEFT_GAP, 24 + DIGIT_HEIGHT * 2 + DIGIT_ROW_GAP + BUTTONS_TOP_GAP)

        total_width = side_x + SIDE_PANEL_WIDTH
        total_height = max(matrix_height, content_height)

        self.root = tk.Tk()
        self.root.title("LEDs Play — Simulator")
        self.root.resizable(False, False)
        self.root.protocol("WM_DELETE_WINDOW", self._on_close)

        self.canvas = tk.Canvas(
            self.root, width=total_width, height=total_height,
            bg=BG_COLOR, highlightthickness=0)
        self.canvas.pack()

        self.root.focus_set()

        self._closed = False

    def pixel_rect(self, x: int, y: int):
        """Canvas bbox for logical matrix pixel (x, y)."""
        ox, oy = self.matrix_origin
        x0 = ox + x * CELL_SIZE + CELL_GAP / 2
        y0 = oy + y * CELL_SIZE + CELL_GAP / 2
        x1 = ox + (x + 1) * CELL_SIZE - CELL_GAP / 2
        y1 = oy + (y + 1) * CELL_SIZE - CELL_GAP / 2
        return x0, y0, x1, y1

    def _on_close(self):
        self._closed = True

    def pump(self):
        if self._closed:
            raise SystemExit
        try:
            self.root.update_idletasks()
            self.root.update()
        except tk.TclError:
            self._closed = True
        if self._closed:
            raise SystemExit


_window: Optional[SimulatorWindow] = None


def get_window(matrix_dims: Optional[Position] = None) -> SimulatorWindow:
    global _window
    if _window is None:
        if matrix_dims is None:
            raise RuntimeError(
                "SimulatorWindow hasn't been created yet - the matrix backend "
                "must be constructed before the key/score backends")
        _window = SimulatorWindow(matrix_dims)
    return _window
