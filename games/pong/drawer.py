from typing import Optional

from common.common import add_positions
from games.pong.board import BALL_COLOR_HSV, BORDER_COLOR_HSV, Board, PADDLE_COLOR_HSV, PADDLE_HEIGHT
from hardware.interfaces import Matrix


BOARD_POS_0 = (4, 3)


class Drawer:
    def __init__(self, matrix: Matrix, banner_matrix: Optional[Matrix] = None):
        self._matrix = matrix
        self._banner_matrix = banner_matrix

        board = Board()
        # +2/+2: one extra row/column on every side for the enclosing border.
        self._board_canvas = self._matrix.create_canvas(
            BOARD_POS_0, add_positions(board.dimensions, (2, 2)))

        self.board = board
        self._paddle_color = PADDLE_COLOR_HSV

    def reset_colors(self):
        """Back to the normal paddle color - call at the start of a round,
        undoing any blink_board() color shift left over from a previous
        game over."""
        self._paddle_color = PADDLE_COLOR_HSV

    def _draw_paddle(self, row: int, col: int):
        for i in range(PADDLE_HEIGHT):
            self._board_canvas[add_positions((row + i, col), (1, 1))] = self._paddle_color

    def draw_board(self):
        self._board_canvas.draw_borders(BORDER_COLOR_HSV)

        _, cols = self.board.dimensions
        self._draw_paddle(self.board.left_paddle_row, 0)
        self._draw_paddle(self.board.right_paddle_row, cols - 1)
        self._board_canvas[add_positions(self.board.ball, (1, 1))] = BALL_COLOR_HSV

        self.show()

    def blink_board(self):
        """Flip the paddle color 180 degrees around the hue wheel and
        redraw - called repeatedly on game over (see PongGame.
        on_game_over_tick), same idea as Tetris/Snake's board blink."""
        hue, saturation, value = self._paddle_color
        self._paddle_color = ((hue + 180) % 360, saturation, value)
        self.draw_board()

    def show(self):
        self._matrix.show()
        if self._banner_matrix:
            self._banner_matrix.show()

    def clear(self):
        self._matrix.clear()
        if self._banner_matrix:
            self._banner_matrix.clear()
