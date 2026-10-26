import os
from time import monotonic
from typing import Optional

from games.base import Game
from games.doom.drawer import Drawer
from platforms.interfaces import AudioPlayer, Key, KeyHandler, Matrix

TURN_INTERVAL = 1 / 30
# Longest step the world advances in one turn, so a slow frame (or
# coming back from Key.PAUSE) doesn't teleport anything through a wall.
MAX_DT = 0.1


class DoomGame(Game):
    NAME = "DOOM"
    LOGO_PATH = os.path.join(os.path.dirname(__file__), "logo.png")
    # All read continuously via KeyHandler.is_pressed() (held = keep
    # moving/turning/firing): UP/DOWN move, LEFT/RIGHT turn, P2_LEFT/
    # P2_RIGHT strafe, P2_UP fires.
    USED_KEYS = frozenset({
        Key.UP, Key.DOWN, Key.LEFT, Key.RIGHT,
        Key.P2_UP, Key.P2_LEFT, Key.P2_RIGHT,
    })

    def __init__(
        self, matrix: Matrix, banner_matrix: Optional[Matrix] = None,
        key_handler: Optional[KeyHandler] = None, audio_player: Optional[AudioPlayer] = None,
        score_file: str = None,
    ):
        # audio_player unused - DOOM has no sound assets yet, accepted
        # for the shared Game constructor convention.
        self._drawer = Drawer(matrix, banner_matrix)
        self._board = self._drawer.board
        self._key_handler = key_handler
        self._last_turn = None

        super().__init__(score_file)

    def start(self):
        self._board.start()
        self._drawer.reset()
        self._last_turn = monotonic()

    @property
    def score(self) -> int:
        return self._board.score

    @property
    def turn_interval(self) -> float:
        return TURN_INTERVAL

    def _held(self, key: Key) -> bool:
        return self._key_handler is not None and self._key_handler.is_pressed(key)

    def advance_turn(self, key: Key):
        now = monotonic()
        dt = min(now - self._last_turn, MAX_DT)
        self._last_turn = now

        held = self._held
        self._board.advance(
            dt,
            forward=held(Key.UP) - held(Key.DOWN),
            turn=held(Key.RIGHT) - held(Key.LEFT),
            strafe=held(Key.P2_RIGHT) - held(Key.P2_LEFT),
            # A tap shorter than one turn never shows up as held, but
            # still arrives as a one-shot click.
            fire=held(Key.P2_UP) or key == Key.P2_UP,
        )
        self._update_best_score()

    def is_game_over(self) -> bool:
        return self._board.is_game_over()

    def render(self):
        self._drawer.draw_board()

    def on_game_over_tick(self):
        self._drawer.blink_board()
