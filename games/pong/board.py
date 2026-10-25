from random import choice

from platforms.interfaces import Key, KeyHandler

COURT_DIMS = (24, 34)  # rows, cols - the playable area, excluding the border
PADDLE_HEIGHT = 5
PADDLE_COL_INSET = 1  # the ball bounces this many cells in from the left/right border
POINTS_TO_WIN = 7

TURN_INTERVAL = 0.08

PADDLE_COLOR_HSV = (200, 0.7, 0.6)
BALL_COLOR_HSV = (0, 0, 0.9)
BORDER_COLOR_HSV = (0, 0, 0.3)

# Both paddles move continuously while held (KeyHandler.is_pressed(), like
# Snake's run boost) rather than one-shot per get_key() click, so both
# players can move in the same turn.
_LEFT_KEYS = {Key.P2_UP: -1, Key.P2_DOWN: 1}
_RIGHT_KEYS = {Key.UP: -1, Key.DOWN: 1}


class Board:
    """Two-player Pong: the left paddle (Key.P2_UP/Key.P2_DOWN - W/S in
    sim) and the right paddle (Key.UP/Key.DOWN) each guard their own edge
    of the court; missing the ball scores the other side a point. First to
    POINTS_TO_WIN ends the round."""

    def __init__(self, dimensions=COURT_DIMS):
        self.dimensions = dimensions
        self.left_paddle_row = None
        self.right_paddle_row = None
        self.ball = None
        self.ball_direction = None
        self.left_score = None
        self.right_score = None
        self.game_over = False

    def start(self):
        rows, _ = self.dimensions
        mid_row = rows // 2
        self.left_paddle_row = mid_row
        self.right_paddle_row = mid_row
        self.left_score = 0
        self.right_score = 0
        self.game_over = False
        self._serve()

    def is_game_over(self) -> bool:
        return self.game_over

    def _serve(self):
        rows, cols = self.dimensions
        self.ball = (rows // 2, cols // 2)
        self.ball_direction = (choice((-1, 1)), choice((-1, 1)))

    def _move_paddles(self, key_handler: KeyHandler):
        rows, _ = self.dimensions
        top, bottom = 0, rows - PADDLE_HEIGHT

        for key, d_row in _LEFT_KEYS.items():
            if key_handler.is_pressed(key):
                self.left_paddle_row = max(top, min(bottom, self.left_paddle_row + d_row))
        for key, d_row in _RIGHT_KEYS.items():
            if key_handler.is_pressed(key):
                self.right_paddle_row = max(top, min(bottom, self.right_paddle_row + d_row))

    @staticmethod
    def _paddle_hit(paddle_row: int, ball_row: int) -> bool:
        return paddle_row <= ball_row < paddle_row + PADDLE_HEIGHT

    def advance_turn(self, key_handler: KeyHandler):
        self._move_paddles(key_handler)

        rows, cols = self.dimensions
        row, col = self.ball
        d_row, d_col = self.ball_direction

        new_row = row + d_row
        if not (0 <= new_row < rows):
            d_row = -d_row
            new_row = row + d_row

        new_col = col + d_col
        left_col, right_col = PADDLE_COL_INSET, cols - 1 - PADDLE_COL_INSET

        if new_col <= left_col:
            if self._paddle_hit(self.left_paddle_row, new_row):
                d_col = -d_col
                new_col = col + d_col
            else:
                self.right_score += 1
                self._end_or_serve()
                return
        elif new_col >= right_col:
            if self._paddle_hit(self.right_paddle_row, new_row):
                d_col = -d_col
                new_col = col + d_col
            else:
                self.left_score += 1
                self._end_or_serve()
                return

        self.ball = (new_row, new_col)
        self.ball_direction = (d_row, d_col)

    def _end_or_serve(self):
        if self.left_score >= POINTS_TO_WIN or self.right_score >= POINTS_TO_WIN:
            self.game_over = True
        else:
            self._serve()
