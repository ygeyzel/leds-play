import os
from typing import Optional

from games.base import Game
from games.tetris.drawer import Drawer
from platforms.interfaces import AudioPlayer, Key, KeyHandler, Matrix


class TetrisGame(Game):
    NAME = "Tetris"
    LOGO_PATH = os.path.join(os.path.dirname(__file__), "logo.png")
    USED_KEYS = frozenset({Key.UP, Key.DOWN, Key.LEFT, Key.RIGHT})

    _ASSETS_DIR = os.path.dirname(__file__)
    BGM_PATH = os.path.join(_ASSETS_DIR, "bg_music.mp3")
    SFX_PATHS = {
        "game_over": os.path.join(_ASSETS_DIR, "game-over.wav"),
        "line_clear": os.path.join(_ASSETS_DIR, "1-line-clear.wav"),
        "tetris_clear": os.path.join(_ASSETS_DIR, "4-lines-clear.wav"),
    }

    def __init__(
        self, matrix: Matrix, banner_matrix: Optional[Matrix] = None,
        key_handler: Optional[KeyHandler] = None, audio_player: Optional[AudioPlayer] = None,
        score_file: str = None,
    ):
        # key_handler unused - Tetris only needs get_key()'s one-shot
        # clicks, accepted for the shared Game constructor convention.
        self._drawer = Drawer(matrix, banner_matrix)
        self._board = self._drawer.board
        self._board.burn_animation = self._drawer.burn_animation
        self._board.on_lines_cleared = self._play_line_clear_sfx
        self._audio_player = audio_player

        super().__init__(score_file)

    def start(self):
        self._board.start()
        self._update_best_score()
        if self._audio_player:
            self._audio_player.play_bgm(self.BGM_PATH, loop=True)

    def stop(self):
        if self._audio_player:
            self._audio_player.stop_bgm()

    def _play_line_clear_sfx(self, lines: int):
        if not self._audio_player:
            return
        sfx = self.SFX_PATHS["tetris_clear"] if lines >= 4 else self.SFX_PATHS["line_clear"]
        self._audio_player.play_sfx(sfx)

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

    def on_round_end(self, key_handler):
        if self._audio_player:
            self._audio_player.stop_bgm()
            self._audio_player.play_sfx(self.SFX_PATHS["game_over"])
            self._audio_player.play_bgm(self.BGM_PATH, loop=True)
        return super().on_round_end(key_handler)
