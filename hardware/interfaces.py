from abc import ABC, abstractmethod
from enum import Enum

from common.common import HsvColor, Position
from hardware.canvas import Canvas


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


class ScoreDisplay(ABC):
    """Contract a score-display backend must satisfy."""

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        pass

    @abstractmethod
    def send_score(self, score: int, highest: int):
        ...
