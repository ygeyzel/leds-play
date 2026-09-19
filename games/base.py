import inspect
import os
from abc import ABC, abstractmethod
from time import sleep, time

from hardware.interfaces import Key, KeyHandler


class Game(ABC):
    """Contract every game implements, so `main.py`'s menu can run any of
    them uniformly. See GAME_TEMPLATE.md for the full per-game template
    this belongs to.

    By convention (not enforced by this ABC - Python can't check
    constructor signatures) every subclass's `__init__` accepts
    `(matrix, banner_matrix=None, score_file=None)`: the menu creates the
    one real `Matrix`/banner `Matrix` pair for the whole process and hands
    them to whichever game is currently active, so hardware only gets
    initialized once."""

    NAME: str
    LOGO_PATH: str = None  # not implemented yet, see GAME_TEMPLATE.md step 4
    USED_KEYS: frozenset

    BGM_PATH = None
    SFX_PATHS = {}

    def __init__(self, score_file: str = None):
        self._score_file = score_file or self._default_score_file()
        self.best_score = self._read_best_score()

    def _default_score_file(self) -> str:
        module_dir = os.path.dirname(inspect.getfile(type(self)))
        return os.path.join(module_dir, ".best_score")

    def _read_best_score(self) -> int:
        if os.path.exists(self._score_file):
            with open(self._score_file) as file:
                value = file.read()
                if value.isdigit():
                    return int(value)
        return 0

    def _update_best_score(self):
        if self.score > self.best_score:
            self.best_score = self.score
            with open(self._score_file, "w") as file:
                file.write(str(self.best_score))

    @abstractmethod
    def start(self):
        """Reset game state for a new round."""

    @property
    @abstractmethod
    def score(self) -> int:
        ...

    @property
    @abstractmethod
    def turn_interval(self) -> float:
        """Seconds to wait between turns; may vary during play (e.g.
        speeding up with level)."""

    @abstractmethod
    def advance_turn(self, key: Key):
        ...

    @abstractmethod
    def is_game_over(self) -> bool:
        ...

    @abstractmethod
    def render(self):
        """Draw the current state to this game's matrices."""

    def on_game_over_tick(self):
        """Called repeatedly while waiting after game over (e.g. to run a
        blink animation). Defaults to a plain re-render."""
        self.render()

    def on_round_end(self, key_handler: KeyHandler):
        """Called once a round ends naturally (`is_game_over()` became
        true). Default: wait on a blinking screen (via `on_game_over_tick`)
        for a keypress, with a minimum pause, before control returns to the
        menu. The menu itself overrides this to return immediately - it has
        no "game over" of its own to show off."""
        key_handler.flush()
        end_time = time()

        while key_handler.get_key() == Key.NO_KEY or time() - end_time < 2:
            self.on_game_over_tick()
            sleep(0.2)
