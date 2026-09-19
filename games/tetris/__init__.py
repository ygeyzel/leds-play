from typing import Optional

from games.base import Game
from games.tetris.drawer import Drawer
from hardware.interfaces import Key, Matrix


class TetrisGame(Game):
    NAME = "Tetris"
    USED_KEYS = frozenset({Key.UP, Key.DOWN, Key.LEFT, Key.RIGHT})

    def __init__(
        self, matrix: Matrix, banner_matrix: Optional[Matrix] = None,
        score_file: str = None,
    ):
        self._drawer = Drawer(matrix, banner_matrix)
        self._board = self._drawer.board
        self._board.burn_animation = self._drawer.burn_animation

        super().__init__(score_file)

    def start(self):
        self._board.start()
        self._update_best_score()

    @property
    def score(self) -> int:
        return self._board.score

    @property
    def turn_interval(self) -> float:
        return 1 / self._board.level

    def advance_turn(self, key: Key):
        self._board.advance_turn(key)
        self._update_best_score()

    def is_game_over(self) -> bool:
        return self._board.is_game_over()

    def render(self):
        self._drawer.clear()
        self._drawer.draw_board()

    def on_game_over_tick(self):
        self._drawer.blink_board()
