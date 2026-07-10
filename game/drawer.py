from itertools import product
from time import sleep
from game.game_board import Board
from common.common import add_positions, BOARD_DIMS
from hardware.leds import DualMatrix


BOARD_POS_0 = (8, 2)
SINGLE_MATRIX_WIDTH = 8
MATRIX_HEIGHT = 32
MATRIX_DPIN = 18

NEXT_CELL_POS_0 = (1, 4)
NEXT_CELL_HEIGHT_WIDTH = (7, 8)


BORDER_COLOR_HSV = (20, 0, 0.05)
NEXT_CELL_BORDER_COLOR_HSV = (20, 0, 0.05)


class Drawer:
    def __init__(self):
        self._matrix = DualMatrix(
            MATRIX_DPIN, SINGLE_MATRIX_WIDTH, MATRIX_HEIGHT)
        board = Board(BOARD_DIMS)

        self._board_canvas = self._matrix.create_canvas(
            BOARD_POS_0,  add_positions(board.dimensions_for_canvas(), (1, 2)))

        self._next_cell_canvas = self._matrix.create_canvas(
            NEXT_CELL_POS_0, NEXT_CELL_HEIGHT_WIDTH)

        self.board = board

    def _draw_board_current_block(self):
        if block := self.board.current_block:
            draw_pos = add_positions(self.board.current_block_pos, (0, 1))
            self._board_canvas.draw_shape(
                block.shape, block.color, draw_pos)

    def _draw_next_block_cell(self):
        self._next_cell_canvas.draw_borders(NEXT_CELL_BORDER_COLOR_HSV)

        if block := self.board.next_block:
            pos_in_cell = tuple(int((cell_dim - shape_dim) / 2) for cell_dim,
                                shape_dim in zip(NEXT_CELL_HEIGHT_WIDTH, block.size()))
            self._next_cell_canvas.draw_shape(block.shape, block.color, pos_in_cell)

    def draw_board(self):
        self._board_canvas.draw_color_map(self.board.board, (0, 1))
        self._board_canvas.draw_borders(BORDER_COLOR_HSV, "ulb")
        self._draw_board_current_block()
        self._draw_next_block_cell()

        self.show()

    def blink_board(self):
        board = self.board.board
        for i, j in product(range(len(board)), range(len(board[0]))):
            if color := board[i][j]:
                color = ((180 + color[0]) % 360, color[1], color[2])
                board[i][j] = color

        self._board_canvas.draw_color_map(self.board.board, (0, 1))
        self.show()

    def burn_animation(self, row: int):
        self.clear()
        self.draw_board()

        row_colors = self .board.board[row] 
        for _ in range(50):
            row_colors = [(c[0], c[1], c[2] * 0.7) for c in row_colors]
            self._board_canvas.draw_color_map([row_colors], (row, 1))
            self.show()
            sleep(0.01)

    def show(self):
        self._matrix.show()

    def clear(self):
        self._matrix.clear()

