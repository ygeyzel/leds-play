from abc import ABC, abstractmethod
from enum import Enum

from common.common import HsvColor, Position
from platforms.canvas import Canvas


class Key(Enum):
    NO_KEY = 0
    UP = 1
    DOWN = 2
    LEFT = 3
    RIGHT = 4
    P2_UP = 5
    P2_DOWN = 6
    P2_LEFT = 7
    P2_RIGHT = 8
    ENTER = 9
    PAUSE = 10
    MUTE = 11


class Matrix(ABC):
    """Contract an LED matrix backend must satisfy so game code never
    talks to hardware (or the simulator) directly."""

    @property
    @abstractmethod
    def dimensions(self) -> Position:
        ...

    @abstractmethod
    def __setitem__(self, index: Position, value: HsvColor):
        ...

    @abstractmethod
    def clear(self):
        ...

    @abstractmethod
    def show(self):
        ...

    def create_canvas(self, pos0: Position, dimensions: Position) -> Canvas:
        return Canvas(self, pos0, dimensions)


class KeyHandler(ABC):
    """Contract a button/key input backend must satisfy."""

    @abstractmethod
    def get_key(self) -> Key:
        ...

    @abstractmethod
    def flush(self):
        ...

    def pump(self):
        """Process any pending input events. A no-op unless a backend
        (e.g. the simulator, which needs to service its GUI event loop)
        requires it."""

    def is_pressed(self, key: Key) -> bool:
        """Whether `key` is being held down right now - independent of
        get_key()'s one-shot click-on-release reporting. For a continuous
        modifier (e.g. a run/boost key) rather than a discrete command.
        Default: never held, for a backend that doesn't track this."""
        return False

    def is_toggled(self, key: Key) -> bool:
        """Whether `key` is currently toggled on - a persistent on/off
        state flipped by each completed click (e.g. Key.PAUSE, Key.MUTE),
        independent of get_key()'s one-shot reporting and is_pressed()'s
        momentary hold. Default: never toggled, for a backend that
        doesn't support this yet."""
        return False

    def set_active_keys(self, keys):
        """Tell the backend which keys the currently active game (or the
        menu) actually reads (its USED_KEYS), so it can show that - e.g.
        the simulator dims an inactive button's on-screen button to gray
        instead of its usual red, the way real hardware might light (or
        not) that button's own inner LED.
        Default: no-op, for a backend that doesn't support this yet."""


class AudioPlayer(ABC):
    """Contract an audio backend must satisfy so game code never talks to
    pygame.mixer (or any other backend) directly."""

    @abstractmethod
    def play_bgm(self, path: str, loop: bool = True):
        """Start background music from `path`, replacing whatever was
        already playing. Muted has no immediate audible effect but is
        remembered - see set_muted()."""

    @abstractmethod
    def stop_bgm(self):
        """Stop whatever background music is currently playing."""

    @abstractmethod
    def play_sfx(self, path: str):
        """Play a one-shot sound effect from `path`, without interrupting
        any currently-playing background music. A no-op while muted."""

    @abstractmethod
    def set_muted(self, muted: bool):
        """Mute/unmute all audio. Muting stops any background music
        outright (sound effects are too short-lived to need stopping
        mid-play); unmuting resumes the most recent play_bgm() call, if
        any, from the start."""


class ScoreDisplay(ABC):
    """Contract a score-display backend must satisfy."""

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        pass

    @abstractmethod
    def send_score(self, score: int, highest: int):
        ...
