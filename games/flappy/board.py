from collections import deque
from random import randint

from hardware.interfaces import Key


COURT_DIMS = (20, 34)  # rows, cols - the playable area, excluding the border
BIRD_COL = 5

GRAVITY = 0.5
FLAP_VELOCITY = -1.8  # set (not added) on flap, for a responsive, classic feel
MAX_FALL_VELOCITY = 2.0

PIPE_WIDTH = 2
PIPE_GAP_SIZE = 7
PIPE_SPACING = 10  # columns between consecutive pipes' spawn points

TURN_INTERVAL = 0.1

BIRD_COLOR_HSV = (55, 1.0, 0.9)
PIPE_COLOR_HSV = (120, 0.8, 0.5)
BORDER_COLOR_HSV = (0, 0, 0.3)


class Pipe:
    __slots__ = ("col", "gap_start")

    def __init__(self, col: int, gap_start: int):
        self.col = col
        self.gap_start = gap_start


class Board:
    """Flappy Bird: Key.UP flaps - the bird's vertical velocity is set
    upward instantly (not held down for continuous lift, same feel as the
    original), and gravity pulls it back down every other turn. Pipes
    scroll from right to left with a fixed-size gap; passing one scores a
    point, touching a pipe/the ceiling/the ground ends the round."""

    def __init__(self, dimensions=COURT_DIMS):
        self.dimensions = dimensions
        self.bird_row = None
        self.bird_velocity = None
        self.pipes = None
        self.score = None
        self.game_over = False

    def start(self):
        rows, cols = self.dimensions
        self.bird_row = rows / 2
        self.bird_velocity = 0.0
        self.pipes = deque([Pipe(cols, self._random_gap_start())])
        self.score = 0
        self.game_over = False

    def is_game_over(self) -> bool:
        return self.game_over

    def _random_gap_start(self) -> int:
        rows, _ = self.dimensions
        return randint(1, rows - PIPE_GAP_SIZE - 1)

    def _advance_pipes(self):
        rows, cols = self.dimensions
        for pipe in self.pipes:
            pipe.col -= 1
        while self.pipes and self.pipes[0].col + PIPE_WIDTH < 0:
            self.pipes.popleft()
        if self.pipes[-1].col <= cols - PIPE_SPACING:
            self.pipes.append(Pipe(cols, self._random_gap_start()))

    def advance_turn(self, key: Key):
        if key == Key.UP:
            self.bird_velocity = FLAP_VELOCITY

        self.bird_velocity = min(MAX_FALL_VELOCITY, self.bird_velocity + GRAVITY)
        self.bird_row += self.bird_velocity

        rows, _ = self.dimensions
        if self.bird_row < 0 or self.bird_row >= rows:
            self.game_over = True
            return

        self._advance_pipes()

        bird_row_cell = int(self.bird_row)
        for pipe in self.pipes:
            if pipe.col <= BIRD_COL < pipe.col + PIPE_WIDTH:
                if not (pipe.gap_start <= bird_row_cell < pipe.gap_start + PIPE_GAP_SIZE):
                    self.game_over = True
                    return
            if pipe.col + PIPE_WIDTH == BIRD_COL:
                self.score += 1
