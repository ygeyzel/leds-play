from time import sleep
from unittest.mock import Mock

from tests.shared import matrix_test
from game.drawer import Drawer
from game.game_board import Block, BLOCK_SHAPES, Direction


board_pos_0 = [
    [0, 0, 0, 0, 0, 0, 0, 0, 0, 0],
    [0, 0, 0, 0, 0, 0, 0, 0, 0, 0],
    [0, 0, 0, 0, 0, 0, 0, 0, 0, 0],
    [0, 0, 0, 0, 0, 0, 0, 0, 0, 0],
    [0, 0, 0, 0, 0, 0, 0, 0, 0, 0],
    [0, 0, 0, 0, 0, 0, 0, 0, 0, 0],
    [0, 0, 0, 0, 0, 0, 0, 0, 0, 0],
    [0, 0, 0, 0, 0, 0, 0, 0, 0, 0],
    [0, 0, 0, 0, 0, 0, 0, 0, 0, 0],
    [0, 0, 0, 0, 0, 0, 0, 0, 0, 0],
    [0, 0, 0, 0, 0, 0, 0, 0, 0, 0],
    [0, 0, 0, 0, 0, 0, 0, 0, 0, 0],
    [0, 0, 0, 0, 0, 0, 0, 0, 0, 0],
    [0, 0, 0, 0, 0, 0, 0, 0, 0, 0],
    [0, 0, 0, 0, 0, 0, 0, 0, 0, 0],
    [0, 0, 0, 0, 0, 0, 0, 0, 0, 0],
    [0, 0, 0, 0, 0, 0, 0, 0, 0, 1],
    [0, 0, 0, 0, 0, 0, 0, 0, 0, 1],
    [0, 0, 0, 0, 0, 1, 0, 0, 0, 1],
    [0, 0, 0, 0, 1, 1, 1, 0, 0, 1]
]


drawer = Drawer()


@matrix_test
def test_draw_board(*args, **kwargs):
    board = drawer.board
    board._block_reach_bottom = Mock()

    current_block = Block('Z')
    next_block = Block('T')

    board.board = board_pos_0
    board.current_block = current_block
    board.current_block_pos = (12, 6)
    board.next_block = next_block

    drawer.draw_board()
    for dr in (Direction.LEFT, Direction.DOWN, Direction.RIGHT, Direction.DOWN, Direction.DOWN):
        sleep(0.3)
        drawer._matrix.clear()

        board.move_block(dr)
        print(f"\t{dr.name}")
        drawer.draw_board()



@matrix_test
def test_draw_next_shape(*args, **kwargs):
    board = drawer.board

    for shape in BLOCK_SHAPES:
        print(f"\t{shape}")
        drawer._matrix.clear()

        board.next_block = Block(shape)
        drawer.draw_board()

        sleep(0.3)


if __name__ == "__main__":
    test_draw_next_shape(matrix=drawer._matrix)
    test_draw_board(matrix=drawer._matrix)
