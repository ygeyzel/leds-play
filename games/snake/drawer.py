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

    def draw_board(self):
        self._board_canvas.draw_borders(BORDER_COLOR_HSV)

        for segment in self.board.snake:
            self._board_canvas[add_positions(segment, (1, 1))] = SNAKE_COLOR_HSV

        self._board_canvas[add_positions(self.board.apple, (1, 1))] = APPLE_COLOR_HSV

        self.show()

    def show(self):
        self._matrix.show()
        if self._banner_matrix:
            self._banner_matrix.show()

    def clear(self):
        self._matrix.clear()
        if self._banner_matrix:
            self._banner_matrix.clear()
