import os
from typing import Optional

from games.base import Game
from games.pong.board import TURN_INTERVAL
from games.pong.drawer import Drawer
from hardware.interfaces import Key, KeyHandler, Matrix


class PongGame(Game):
    NAME = "Pong"
    LOGO_PATH = os.path.join(os.path.dirname(__file__), "logo.png")
    # Both paddles are read continuously via KeyHandler.is_pressed() each
    # turn (see Board.advance_turn) rather than as one-shot get_key()
    # commands, so advance_turn's key argument goes unused here.
    USED_KEYS = frozenset({Key.UP, Key.DOWN, Key.P2_UP, Key.P2_DOWN})

    def __init__(
        self, matrix: Matrix, banner_matrix: Optional[Matrix] = None,
        key_handler: Optional[KeyHandler] = None, score_file: str = None,
    ):
        self._drawer = Drawer(matrix, banner_matrix)
        self._board = self._drawer.board
        self._key_handler = key_handler

        super().__init__(score_file)

    def start(self):
        self._board.start()
        self._drawer.reset_colors()

    @property
    def score(self) -> int:
        """The left paddle's (W/S) live score."""
        return self._board.left_score

    @property
    def best_score(self) -> int:
        """Repurposed to show the right paddle's (arrow keys) live score
        on the second 7-segment row - a 2-player match has no meaningful
        persisted high score, so nothing is ever written to disk (the
        setter below is a no-op, same trick MenuGame's best_score uses)."""
        return self._board.right_score

    @best_score.setter
    def best_score(self, value):
        pass  # Game.__init__ assigns this; Pong's is always derived, see the getter

    @property
    def turn_interval(self) -> float:
        return TURN_INTERVAL

    def advance_turn(self, key: Key):
        if self._key_handler is not None:
            self._board.advance_turn(self._key_handler)

    def is_game_over(self) -> bool:
        return self._board.is_game_over()

    def render(self):
        self._drawer.clear()
        self._drawer.draw_board()

    def on_game_over_tick(self):
        self._drawer.blink_board()
