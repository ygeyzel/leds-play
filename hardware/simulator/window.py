import tkinter as tk
from typing import Optional

from common.common import Position


CELL_SIZE = 18
CELL_GAP = 2

BG_COLOR = "#101010"

PANEL_PADDING = 24
SIDE_PANEL_WIDTH = 430

DIGIT_WIDTH = 26
DIGIT_HEIGHT = 46
DIGIT_ROW_GAP = 24

BUTTONS_TOP_GAP = 100
BUTTON_LEFT_GAP = 60
BUTTONS_GAP_X = 50  # horizontal gap between the two D-pads
LABEL_HEADROOM = 18  # extra room above a button row for its text label
DPAD_BLOCK_WIDTH = 3 * (40 + 8)  # rough width of a 3-col D-pad block
DPAD_BLOCK_HEIGHT = 3 * (40 + 8)  # rough height of a 3-row D-pad block
ENTER_BLOCK_HEIGHT = 40 + 8  # rough height of a single button

BANNER_MATRIX_GAP_PIXELS = 3  # gap between the banner and the board matrix, in matrix pixels


class SimulatorWindow:
    """A single Tk window shared by the simulator's matrix, key and score
    backends: one physical window standing in for the whole rig."""

    def __init__(self, matrix_dims: Position, banner_dims: Optional[Position] = None):
        rows, cols = matrix_dims

        matrix_width = cols * CELL_SIZE
        matrix_height = rows * CELL_SIZE

        if banner_dims:
            banner_rows, banner_cols = banner_dims
            banner_width = banner_cols * CELL_SIZE
            banner_height = banner_rows * CELL_SIZE
            banner_gap = BANNER_MATRIX_GAP_PIXELS * CELL_SIZE
        else:
            banner_width = banner_height = banner_gap = 0

        content_height = (
            DIGIT_HEIGHT * 2 + DIGIT_ROW_GAP
            + BUTTONS_TOP_GAP + LABEL_HEADROOM + DPAD_BLOCK_HEIGHT
            + BUTTONS_TOP_GAP + LABEL_HEADROOM + ENTER_BLOCK_HEIGHT
        )

        self.banner_origin = (0, 0)
        self.matrix_origin = (0, banner_height + banner_gap)
        side_x = max(matrix_width, banner_width) + PANEL_PADDING

        self.high_score_origin = (side_x, 24)
        self.score_origin = (side_x, 24 + DIGIT_HEIGHT + DIGIT_ROW_GAP)

        buttons_y = 24 + DIGIT_HEIGHT * 2 + DIGIT_ROW_GAP + BUTTONS_TOP_GAP + LABEL_HEADROOM
        self.buttons_origin = (side_x + BUTTON_LEFT_GAP, buttons_y)

        # 2nd D-pad sits right next to the 1st, same row.
        buttons2_x = side_x + BUTTON_LEFT_GAP + DPAD_BLOCK_WIDTH + BUTTONS_GAP_X
        self.buttons2_origin = (buttons2_x, buttons_y)

        enter_y = buttons_y + DPAD_BLOCK_HEIGHT + BUTTONS_TOP_GAP + LABEL_HEADROOM
        self.enter_button_origin = (side_x + BUTTON_LEFT_GAP, enter_y)

        total_width = side_x + SIDE_PANEL_WIDTH
        total_height = max(banner_height + banner_gap + matrix_height, content_height)

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

    def pixel_rect(self, x: int, y: int, origin: Optional[Position] = None):
        """Canvas bbox for logical pixel (x, y) within the given region
        (defaults to the board matrix's origin)."""
        ox, oy = origin if origin is not None else self.matrix_origin
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


def get_window(
    matrix_dims: Optional[Position] = None,
    banner_dims: Optional[Position] = None,
) -> SimulatorWindow:
    global _window
    if _window is None:
        if matrix_dims is None:
            raise RuntimeError(
                "SimulatorWindow hasn't been created yet - the board matrix "
                "backend must be constructed (with the final banner size "
                "already known) before the banner/key/score backends")
        _window = SimulatorWindow(matrix_dims, banner_dims)
    return _window
