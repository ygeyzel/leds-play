from collections import deque
from enum import Enum
from random import randint

from hardware.interfaces import Key


BOARD_DIMS = (16, 16)

INITIAL_LENGTH = 3
POINTS_PER_APPLE = 5

NORMAL_TURN_INTERVAL = 0.25
RUN_TURN_INTERVAL = 0.15  # a bit faster while the run key is held

SNAKE_COLOR_HSV = (120, 1, 0.4)
APPLE_COLOR_HSV = (0, 1, 0.5)


class Direction(Enum):
    UP = (-1, 0)
    DOWN = (1, 0)
    LEFT = (0, -1)
    RIGHT = (0, 1)


_OPPOSITE = {
    Direction.UP: Direction.DOWN,
    Direction.DOWN: Direction.UP,
    Direction.LEFT: Direction.RIGHT,
    Direction.RIGHT: Direction.LEFT,
}

_KEY_TO_DIRECTION = {
    Key.UP: Direction.UP,
    Key.DOWN: Direction.DOWN,
    Key.LEFT: Direction.LEFT,
    Key.RIGHT: Direction.RIGHT,
}


class Board:
    """Snake board representation"""

    def __init__(self, dimensions=BOARD_DIMS):
        self.dimensions = dimensions
        self.snake = None
        self.direction = None
        self.apple = None
        self.score = None
        self.game_over = False

    def start(self):
        """Start game"""

        rows, cols = self.dimensions
        mid_row, mid_col = rows // 2, cols // 2
        self.snake = deque((mid_row, mid_col - i) for i in range(INITIAL_LENGTH))

        self.direction = Direction.RIGHT
        self.score = 0
        self.game_over = False
        self._place_apple()

    def is_game_over(self):
        """Is game over"""

        return self.game_over

    def advance_turn(self, key: Key):
        new_direction = _KEY_TO_DIRECTION.get(key)
        if new_direction and new_direction != _OPPOSITE[self.direction]:
            self.direction = new_direction

        head_row, head_col = self.snake[0]
        d_row, d_col = self.direction.value
        new_head = (head_row + d_row, head_col + d_col)

        eating = new_head == self.apple
        # The tail cell is about to be vacated (unless the snake is growing
        # this turn), so moving into it is legal - exclude it from the
        # self-collision check.
        body_ahead = self.snake if eating else list(self.snake)[:-1]

        if self._hits_wall(new_head) or new_head in body_ahead:
            self.game_over = True
            return

        self.snake.appendleft(new_head)
        if eating:
            self.score += POINTS_PER_APPLE
            self._place_apple()
        else:
            self.snake.pop()

    def _hits_wall(self, pos) -> bool:
        row, col = pos
        rows, cols = self.dimensions
        return not (0 <= row < rows and 0 <= col < cols)

    def _place_apple(self):
        """Place the apple on a cell the snake isn't occupying"""

        rows, cols = self.dimensions
        while True:
            candidate = (randint(0, rows - 1), randint(0, cols - 1))
            if candidate not in self.snake:
                self.apple = candidate
                return
