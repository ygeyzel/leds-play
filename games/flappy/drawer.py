from typing import Optional

from common.common import add_positions
from games.flappy.board import (
    BIRD_COL,
    BIRD_COLOR_HSV,
    BORDER_COLOR_HSV,
    PIPE_COLOR_HSV,
    PIPE_GAP_SIZE,
    PIPE_WIDTH,
    Board,
)
from hardware.interfaces import Matrix

BOARD_POS_0 = (6, 3)


class Drawer:
    def __init__(self, matrix: Matrix, banner_matrix: Optional[Matrix] = None):
        self._matrix = matrix
        self._banner_matrix = banner_matrix

        board = Board()
        # +2/+2: one extra row/column on every side for the enclosing border.
        self._board_canvas = self._matrix.create_canvas(
            BOARD_POS_0, add_positions(board.dimensions, (2, 2)))

        self.board = board
        self._bird_color = BIRD_COLOR_HSV

    def reset_colors(self):
        """Back to the normal bird color - call at the start of a round,
        undoing any blink_board() color shift left over from a previous
        game over."""
        self._bird_color = BIRD_COLOR_HSV

    def _draw_pipe(self, col: int, gap_start: int):
        rows, cols = self.board.dimensions
        if not (0 <= col < cols):
            return
        for row in range(rows):
            if not (gap_start <= row < gap_start + PIPE_GAP_SIZE):
                self._board_canvas[add_positions((row, col), (1, 1))] = PIPE_COLOR_HSV

    def draw_board(self):
        self._board_canvas.draw_borders(BORDER_COLOR_HSV)

        for pipe in self.board.pipes:
            for col in range(pipe.col, pipe.col + PIPE_WIDTH):
                self._draw_pipe(col, pipe.gap_start)

        rows, _ = self.board.dimensions
        bird_row = max(0, min(rows - 1, int(self.board.bird_row)))
        self._board_canvas[add_positions((bird_row, BIRD_COL), (1, 1))] = self._bird_color

        self.show()

    def blink_board(self):
        """Flip the bird's color 180 degrees around the hue wheel and
        redraw - called repeatedly on game over (see FlappyGame.
        on_game_over_tick), same idea as Tetris/Snake/Pong's blink."""
        hue, saturation, value = self._bird_color
        self._bird_color = ((hue + 180) % 360, saturation, value)
        self.draw_board()

    def show(self):
        self._matrix.show()
        if self._banner_matrix:
            self._banner_matrix.show()

    def clear(self):
        self._matrix.clear()
        if self._banner_matrix:
            self._banner_matrix.clear()
