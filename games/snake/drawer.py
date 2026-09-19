from typing import Optional

from common.common import add_positions
from games.snake.board import APPLE_COLOR_HSV, Board, SNAKE_COLOR_HSV
from hardware.interfaces import Matrix


BOARD_POS_0 = (6, 2)
BORDER_COLOR_HSV = (0, 0, 0.4)  # white box around the play area


class Drawer:
    def __init__(self, matrix: Matrix, banner_matrix: Optional[Matrix] = None):
        self._matrix = matrix
        self._banner_matrix = banner_matrix

        board = Board()
        # +2/+2: one extra row/column on every side for the enclosing border.
        self._board_canvas = self._matrix.create_canvas(
            BOARD_POS_0, add_positions(board.dimensions, (2, 2)))

        self.board = board
        self._snake_color = SNAKE_COLOR_HSV

    def reset_colors(self):
        """Back to the normal snake color - call at the start of a round,
        undoing any blink_board() color shift left over from a previous
        game over."""
        self._snake_color = SNAKE_COLOR_HSV

    def draw_board(self):
        self._board_canvas.draw_borders(BORDER_COLOR_HSV)

        for segment in self.board.snake:
            self._board_canvas[add_positions(segment, (1, 1))] = self._snake_color

        self._board_canvas[add_positions(self.board.apple, (1, 1))] = APPLE_COLOR_HSV

        self.show()

    def blink_board(self):
        """Flip the snake's color 180 degrees around the hue wheel and
        redraw - called repeatedly on game over (see SnakeGame.
        on_game_over_tick) so the snake visibly flashes, same idea as
        Tetris's board blink."""
        hue, saturation, value = self._snake_color
        self._snake_color = ((hue + 180) % 360, saturation, value)
        self.draw_board()

    def show(self):
        self._matrix.show()
        if self._banner_matrix:
            self._banner_matrix.show()

    def clear(self):
        self._matrix.clear()
        if self._banner_matrix:
            self._banner_matrix.clear()
