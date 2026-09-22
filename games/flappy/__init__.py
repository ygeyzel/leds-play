import os
from typing import Optional

from games.base import Game
from games.flappy.board import TURN_INTERVAL
from games.flappy.drawer import Drawer
from platforms.interfaces import AudioPlayer, Key, KeyHandler, Matrix


class FlappyGame(Game):
    NAME = "Flappy Bird"
    LOGO_PATH = os.path.join(os.path.dirname(__file__), "logo.png")
    USED_KEYS = frozenset({Key.UP})

    def __init__(
        self, matrix: Matrix, banner_matrix: Optional[Matrix] = None,
        key_handler: Optional[KeyHandler] = None, audio_player: Optional[AudioPlayer] = None,
        score_file: str = None,
    ):
        # audio_player unused - Flappy Bird has no sound assets yet,
        # accepted for the shared Game constructor convention.
        self._drawer = Drawer(matrix, banner_matrix)
        self._board = self._drawer.board

        super().__init__(score_file)

    def start(self):
        self._board.start()
        self._drawer.reset_colors()

    @property
    def score(self) -> int:
        return self._board.score

    @property
    def turn_interval(self) -> float:
        return TURN_INTERVAL

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
