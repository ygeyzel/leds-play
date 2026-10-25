import inspect
import os
from abc import ABC, abstractmethod
from time import sleep, time

from platforms.interfaces import Key, KeyHandler

RESTART_KEYS = frozenset({Key.UP, Key.DOWN, Key.LEFT, Key.RIGHT})


def default_score_file(game_cls: type) -> str:
    """Where `game_cls`'s `.best_score` lives by default: next to its own
    module. A module-level function (not tied to a `Game` instance) so the
    menu can look up any game's best score just from its class, to show it
    while that game is only selected, not yet playing."""
    module_dir = os.path.dirname(inspect.getfile(game_cls))
    return os.path.join(module_dir, ".best_score")


def read_best_score(score_file: str) -> int:
    if os.path.exists(score_file):
        with open(score_file) as file:
            value = file.read()
            if value.isdigit():
                return int(value)
    return 0


class Game(ABC):
    """Contract every game implements, so `main.py`'s menu can run any of
    them uniformly. See GAME_TEMPLATE.md for the full per-game template
    this belongs to.

    By convention (not enforced by this ABC - Python can't check
    constructor signatures) every subclass's `__init__` accepts `(matrix,
    banner_matrix=None, key_handler=None, score_file=None)`: `main.py`
    creates the one real `Matrix`/banner `Matrix`/`KeyHandler` for the
    whole process and hands them to whichever game is currently active, so
    hardware only gets initialized once. `key_handler` is only needed by a
    game that reads continuous hold state via `KeyHandler.is_pressed()`
    (e.g. a run/boost key) rather than just `get_key()`'s one-shot clicks;
    most games can ignore it."""

    NAME: str
    LOGO_PATH: str = None  # path to this game's logo.png; None = menu placeholder box
    USED_KEYS: frozenset

    BGM_PATH = None
    SFX_PATHS = {}

    def __init__(self, score_file: str = None):
        self._score_file = score_file or default_score_file(type(self))
        self.best_score = read_best_score(self._score_file)

    def _update_best_score(self):
        if self.score > self.best_score:
            self.best_score = self.score
            with open(self._score_file, "w") as file:
                file.write(str(self.best_score))

    @abstractmethod
    def start(self):
        """Reset game state for a new round."""

    def stop(self):
        """Called once when this game is being left for something else
        (the menu, or a different game) - not on a same-instance restart,
        where start() runs again instead. Default: no-op; a game with
        background music should stop it here, so it doesn't keep playing
        into whatever runs next."""

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

    def on_round_end(self, key_handler: KeyHandler) -> bool:
        """Called once a round ends naturally (`is_game_over()` became
        true). Default: wait on a blinking screen (via `on_game_over_tick`)
        for a keypress, with a minimum pause. Returns True if an arrow key
        was what ended the wait - `main.py` then restarts this same game
        with a fresh score - or False for anything else (e.g. ENTER),
        which returns to the menu instead. The menu itself overrides this
        to return immediately - it has no "game over" of its own to show
        off, and its return value is never consulted."""
        key_handler.flush()
        end_time = time()
        last_key = Key.NO_KEY

        while last_key == Key.NO_KEY or time() - end_time < 2:
            key = key_handler.get_key()
            if key != Key.NO_KEY:
                last_key = key
            self.on_game_over_tick()
            sleep(0.2)

        return last_key in RESTART_KEYS
