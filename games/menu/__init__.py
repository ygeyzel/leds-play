import inspect
import os
from typing import List, Optional

from games.base import Game
from games.logo import load_logo
from games.menu.font import FONT_HEIGHT, text_shape
from games.registry import GAMES
from hardware.interfaces import Key, Matrix


LOGO_SIZE = (10, 10)
ARROW_SIZE = (5, 4)
ARROW_GAP = 3  # columns between an arrow and the logo box

ARROW_COLOR_HSV = (0, 0, 0.3)
LOGO_PLACEHOLDER_COLOR_HSV = (0, 0, 0.15)  # dim empty box until a game has a real logo.png
TEXT_COLOR_HSV = (200, 0.7, 0.3)

TEXT_GAP = 8  # blank banner columns between repeats of the scrolling name
TICK_INTERVAL = 0.07  # seconds per menu animation tick (~14fps scroll)

# Boolean shapes for Canvas.draw_shape, same convention as game/tetris's
# BLOCK_SHAPES: a filled-in triangle pointing the way the D-pad will move
# the selection.
LEFT_ARROW_SHAPE = [
    [0, 0, 0, 1],
    [0, 0, 1, 1],
    [0, 1, 1, 1],
    [0, 0, 1, 1],
    [0, 0, 0, 1],
]
RIGHT_ARROW_SHAPE = [list(reversed(row)) for row in LEFT_ARROW_SHAPE]


class MenuGame(Game):
    """The game-selection screen, implemented as a `Game` itself so it
    plugs into the same main.py loop as everything it lets you pick: LEFT/
    RIGHT cycle through `games.registry.GAMES`, ENTER "ends" the menu round
    (`is_game_over`), at which point `main.py` reads `selected_game_cls`
    and switches to it. See GAME_TEMPLATE.md."""

    NAME = "Menu"
    USED_KEYS = frozenset({Key.LEFT, Key.RIGHT, Key.ENTER})

    def __init__(
        self, matrix: Matrix, banner_matrix: Optional[Matrix] = None,
        games: Optional[List[type]] = None, current_game_file: str = None,
        score_file: str = None,
    ):
        self._matrix = matrix
        self._banner_matrix = banner_matrix
        self._games = games if games is not None else GAMES

        self._logo_canvas, self._left_arrow_canvas, self._right_arrow_canvas = \
            self._create_matrix_canvases(matrix)
        self._banner_canvas = (
            banner_matrix.create_canvas((0, 0), banner_matrix.dimensions)
            if banner_matrix else None)

        self._current_game_file = current_game_file or self._default_current_game_file()
        self._index = self._read_current_index()
        self._logo_cache = {}
        self._launched = False
        self._scroll_x = 0
        self._load_selected_text()

        super().__init__(score_file)

    @staticmethod
    def _create_matrix_canvases(matrix: Matrix):
        rows, cols = matrix.dimensions
        logo_rows, logo_cols = LOGO_SIZE
        logo_pos0 = (max(0, (rows - logo_rows) // 2), max(0, (cols - logo_cols) // 2))
        logo_canvas = matrix.create_canvas(logo_pos0, LOGO_SIZE)

        arrow_rows, arrow_cols = ARROW_SIZE
        arrow_row0 = max(0, (rows - arrow_rows) // 2)
        left_arrow_canvas = matrix.create_canvas(
            (arrow_row0, max(0, logo_pos0[1] - ARROW_GAP - arrow_cols)), ARROW_SIZE)
        right_arrow_canvas = matrix.create_canvas(
            (arrow_row0, min(cols - arrow_cols, logo_pos0[1] + logo_cols + ARROW_GAP)),
            ARROW_SIZE)

        return logo_canvas, left_arrow_canvas, right_arrow_canvas

    def _default_current_game_file(self) -> str:
        module_dir = os.path.dirname(inspect.getfile(type(self)))
        return os.path.join(module_dir, ".current_game")

    def _read_current_index(self) -> int:
        if os.path.exists(self._current_game_file):
            with open(self._current_game_file) as file:
                name = file.read().strip()
            for i, game_cls in enumerate(self._games):
                if game_cls.NAME == name:
                    return i
        return 0

    def _write_current_index(self):
        with open(self._current_game_file, "w") as file:
            file.write(self.selected_game_cls.NAME)

    def _load_selected_text(self):
        self._text_shape = text_shape(self.selected_game_cls.NAME.upper())
        self._text_width = len(self._text_shape[0])
        self._scroll_x = 0

    @property
    def selected_game_cls(self) -> type:
        return self._games[self._index]

    @property
    def score(self) -> int:
        return 0

    @property
    def turn_interval(self) -> float:
        return TICK_INTERVAL

    def start(self):
        self._launched = False

    def advance_turn(self, key: Key):
        if key == Key.LEFT:
            self._index = (self._index - 1) % len(self._games)
            self._write_current_index()
            self._load_selected_text()
        elif key == Key.RIGHT:
            self._index = (self._index + 1) % len(self._games)
            self._write_current_index()
            self._load_selected_text()
        elif key == Key.ENTER:
            self._launched = True

        self._scroll_x = (self._scroll_x + 1) % (self._text_width + TEXT_GAP)

    def is_game_over(self) -> bool:
        return self._launched

    def on_round_end(self, key_handler):
        """No wait screen - launching a game from the menu is instant."""

    def render(self):
        self._matrix.clear()
        self._draw_logo()
        self._left_arrow_canvas.draw_shape(LEFT_ARROW_SHAPE, ARROW_COLOR_HSV)
        self._right_arrow_canvas.draw_shape(RIGHT_ARROW_SHAPE, ARROW_COLOR_HSV)
        self._matrix.show()

        if self._banner_matrix:
            self._banner_matrix.clear()
            self._draw_banner_text()
            self._banner_matrix.show()

    def _draw_logo(self):
        game_cls = self.selected_game_cls
        if game_cls not in self._logo_cache:
            self._logo_cache[game_cls] = load_logo(game_cls.LOGO_PATH, LOGO_SIZE)
        logo = self._logo_cache[game_cls]

        if logo:
            self._logo_canvas.draw_color_map(logo)
        else:
            self._logo_canvas.draw_borders(LOGO_PLACEHOLDER_COLOR_HSV)

    def _draw_banner_text(self):
        banner_rows, banner_cols = self._banner_matrix.dimensions
        total_width = self._text_width + TEXT_GAP

        color_map = []
        for row in self._text_shape:
            visible_row = []
            for col in range(banner_cols):
                source_col = (col - self._scroll_x) % total_width
                lit = source_col < self._text_width and row[source_col]
                visible_row.append(TEXT_COLOR_HSV if lit else None)
            color_map.append(visible_row)

        row_offset = max(0, (banner_rows - FONT_HEIGHT) // 2)
        self._banner_canvas.draw_color_map(color_map, (row_offset, 0))
