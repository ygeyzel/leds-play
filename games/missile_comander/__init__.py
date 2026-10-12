import os
from typing import Optional

from games.base import Game
from games.missile_comander.board import TURN_INTERVAL
from games.missile_comander.drawer import Drawer
from platforms.interfaces import Key, KeyHandler, Matrix, AudioPlayer


class MissileCommandGame(Game):
    NAME = "missile"
    LOGO_PATH = os.path.join(os.path.dirname(__file__), "logo.png")
    # Both paddles are read continuously via KeyHandler.is_pressed() each
    # turn (see Board.advance_turn) rather than as one-shot get_key()
    # commands, so advance_turn's key argument goes unused here.
    USED_KEYS = frozenset({Key.UP, Key.DOWN, Key.P2_UP, Key.P2_DOWN})

    def __init__(
        self, matrix: Matrix, banner_matrix: Optional[Matrix] = None,
        key_handler: Optional[KeyHandler] = None, audio_player: Optional[AudioPlayer] = None,
        score_file: str = None,

    ):
        self._matrix = matrix
        self._banner_matrix = banner_matrix
        self._canvas = matrix.create_canvas((0, 0), matrix.dimensions)
        
        self._drawer = Drawer(matrix, banner_matrix)
        self._board = self._drawer.board
        self._key_handler = key_handler
        
        super().__init__(score_file)

    def start(self):
        self._board.start()
        self._drawer.draw_board()

    @property
    def score(self) -> int:
        """The left paddle's (W/S) live score."""
        return self._board.score

    @property
    def turn_interval(self) -> float:
        return TURN_INTERVAL

    def advance_turn(self, key: Key):
        self._update_best_score()
        if self._key_handler is not None:
            self._board.advance_turn(self._key_handler)

    def is_game_over(self) -> bool:
        return self._board.is_game_over()

    def render(self):
        self._drawer.clear()
        self._drawer.draw_board()

    def on_game_over_tick(self):
        self._board.start()

        # no function drawer.blink_board, need to reaset the game some other way or implement!