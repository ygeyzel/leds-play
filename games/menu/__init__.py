import inspect
import os
from typing import List, Optional

from games.base import Game, default_score_file, read_best_score
from games.logo import load_logo
from games.menu.font import FONT_HEIGHT, text_shape
from games.registry import GAMES
from hardware.interfaces import Key, Matrix


LOGO_SIZE = (12, 12)
SMALL_LOGO_SIZE = (6, 6)
PREVIEW_COUNT = 2  # small logos above each arrow, innermost aligned with it
PREVIEW_LOGO_GAP = 1  # columns between adjacent small logos
PREVIEW_ROW_GAP = 2  # rows between the preview strip and the arrow below it
ARROW_SIZE = (5, 4)
ARROW_GAP = 3  # columns between an arrow and the logo box

ARROW_COLOR_HSV = (0, 0, 0.3)
LOGO_PLACEHOLDER_COLOR_HSV = (0, 0, 0.15)  # dim empty box until a game has a real logo.png
TEXT_COLOR_HSV = (200, 0.7, 0.3)

BANNER_LOGO_PADDING = 3  # blank columns on each side of the small logo separator
TEXT_GAP = SMALL_LOGO_SIZE[0] + 2 * BANNER_LOGO_PADDING  # gap between name repeats, sized to fit it
TICK_INTERVAL = 0.07  # seconds per menu animation tick (~14fps scroll)
ARROW_BLINK_TICKS = 3  # ~0.2s the clicked arrow blanks out once, same color otherwise

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
        key_handler=None, games: Optional[List[type]] = None,
        current_game_file: str = None, score_file: str = None,
    ):
        # key_handler unused - the menu only needs get_key()'s one-shot
        # clicks, accepted for the shared Game constructor convention.
        self._matrix = matrix
        self._banner_matrix = banner_matrix
        self._games = games if games is not None else GAMES

        (
            self._logo_canvas, self._left_arrow_canvas, self._right_arrow_canvas,
            self._prev_logo_canvases, self._next_logo_canvases,
        ) = self._create_matrix_canvases(matrix)
        self._banner_canvas = (
            banner_matrix.create_canvas((0, 0), banner_matrix.dimensions)
            if banner_matrix else None)

        self._current_game_file = current_game_file or self._default_current_game_file()
        self._index = self._read_current_index()
        self._logo_cache = {}
        self._launched = False
        self._scroll_x = 0
        self._left_blink_ticks = 0
        self._right_blink_ticks = 0
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
        left_arrow_col = max(0, logo_pos0[1] - ARROW_GAP - arrow_cols)
        right_arrow_col = min(cols - arrow_cols, logo_pos0[1] + logo_cols + ARROW_GAP)
        left_arrow_canvas = matrix.create_canvas((arrow_row0, left_arrow_col), ARROW_SIZE)
        right_arrow_canvas = matrix.create_canvas((arrow_row0, right_arrow_col), ARROW_SIZE)

        # PREVIEW_COUNT small logos in a row above each arrow - previous
        # games above the left arrow, next games above the right one.
        # Index 0 (nearest the big logo) is flush with its arrow's *outer*
        # edge - left edge for the left side, right edge for the right -
        # so it doesn't overhang past the arrow on the side that matters,
        # then the rest extend further outward from there. The two sides
        # are mirror images of each other (this matters once
        # SMALL_LOGO_SIZE differs from ARROW_SIZE's width - same anchoring
        # on both sides would overhang on one side and starve the other).
        small_rows, small_cols = SMALL_LOGO_SIZE
        small_row0 = max(0, arrow_row0 - PREVIEW_ROW_GAP - small_rows)
        right_arrow_right_edge = right_arrow_col + arrow_cols

        prev_logo_canvases = [
            matrix.create_canvas(
                (small_row0, max(0, left_arrow_col - i * (PREVIEW_LOGO_GAP + small_cols))),
                SMALL_LOGO_SIZE)
            for i in range(PREVIEW_COUNT)
        ]
        next_logo_canvases = [
            matrix.create_canvas(
                (small_row0, min(
                    cols - small_cols,
                    right_arrow_right_edge - small_cols + i * (PREVIEW_LOGO_GAP + small_cols))),
                SMALL_LOGO_SIZE)
            for i in range(PREVIEW_COUNT)
        ]

        return (
            logo_canvas, left_arrow_canvas, right_arrow_canvas,
            prev_logo_canvases, next_logo_canvases)

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
    def best_score(self) -> int:
        """The selected game's best score, not the menu's own (it never
        scores) - shown on the score display while browsing, so it
        updates live as LEFT/RIGHT change the selection."""
        return read_best_score(default_score_file(self.selected_game_cls))

    @best_score.setter
    def best_score(self, value):
        pass  # Game.__init__ assigns this; the menu's is always derived, see the getter

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
            self._left_blink_ticks = ARROW_BLINK_TICKS
        elif key == Key.RIGHT:
            self._index = (self._index + 1) % len(self._games)
            self._write_current_index()
            self._load_selected_text()
            self._right_blink_ticks = ARROW_BLINK_TICKS
        elif key == Key.ENTER:
            self._launched = True

        self._left_blink_ticks = max(0, self._left_blink_ticks - 1)
        self._right_blink_ticks = max(0, self._right_blink_ticks - 1)
        self._scroll_x = (self._scroll_x + 1) % (self._text_width + TEXT_GAP)

    def is_game_over(self) -> bool:
        return self._launched

    def on_round_end(self, key_handler):
        """No wait screen - launching a game from the menu is instant."""

    def render(self):
        self._matrix.clear()
        self._draw_logo()
        self._draw_preview_logos()
        self._draw_arrow(self._left_arrow_canvas, LEFT_ARROW_SHAPE, self._left_blink_ticks)
        self._draw_arrow(self._right_arrow_canvas, RIGHT_ARROW_SHAPE, self._right_blink_ticks)
        self._matrix.show()

        if self._banner_matrix:
            self._banner_matrix.clear()
            self._draw_banner_text()
            self._banner_matrix.show()

    @staticmethod
    def _draw_arrow(canvas, shape, blink_ticks: int):
        if blink_ticks <= 0:
            canvas.draw_shape(shape, ARROW_COLOR_HSV)
        # else: skip drawing - the arrow blanks out once, same color as always

    def _load_cached_logo(self, game_cls: type, size):
        key = (game_cls, size)
        if key not in self._logo_cache:
            self._logo_cache[key] = self._load_logo_for_size(game_cls, size)
        return self._logo_cache[key]

    @staticmethod
    def _load_logo_for_size(game_cls: type, size):
        """At SMALL_LOGO_SIZE, prefer a hand-tuned logo_small.png next to
        LOGO_PATH (written by tools/logo_editor.py once its small canvas is
        edited directly) over resizing the big logo.png down - falling
        back to that resize when no such file exists, same as always."""
        path = game_cls.LOGO_PATH
        if size == SMALL_LOGO_SIZE and path:
            small_path = os.path.join(os.path.dirname(path), "logo_small.png")
            small_logo = load_logo(small_path, size)
            if small_logo is not None:
                return small_logo
        return load_logo(path, size)

    def _draw_logo(self):
        self._draw_logo_into(self._logo_canvas, self.selected_game_cls, LOGO_SIZE)

    def _draw_preview_logos(self):
        count = len(self._games)
        for i, canvas in enumerate(self._prev_logo_canvases):
            game_cls = self._games[(self._index - (i + 1)) % count]
            self._draw_logo_into(canvas, game_cls, SMALL_LOGO_SIZE)
        for i, canvas in enumerate(self._next_logo_canvases):
            game_cls = self._games[(self._index + (i + 1)) % count]
            self._draw_logo_into(canvas, game_cls, SMALL_LOGO_SIZE)

    def _draw_logo_into(self, canvas, game_cls: type, size):
        logo = self._load_cached_logo(game_cls, size)
        if logo:
            canvas.draw_color_map(logo)
        else:
            canvas.draw_borders(LOGO_PLACEHOLDER_COLOR_HSV)

    def _draw_banner_text(self):
        """Scrolls the selected game's name across the banner, with a
        small copy of its own logo as the separator between repeats
        (instead of a blank gap)."""
        banner_rows, banner_cols = self._banner_matrix.dimensions
        total_width = self._text_width + TEXT_GAP

        small_cols, small_rows = SMALL_LOGO_SIZE
        logo = self._load_cached_logo(self.selected_game_cls, SMALL_LOGO_SIZE)
        text_row0 = max(0, (banner_rows - FONT_HEIGHT) // 2)
        logo_row0 = max(0, (banner_rows - small_rows) // 2)

        color_map = [[None] * banner_cols for _ in range(banner_rows)]
        for col in range(banner_cols):
            source_col = (col - self._scroll_x) % total_width

            if source_col < self._text_width:
                for font_row, pixels in enumerate(self._text_shape):
                    if pixels[source_col]:
                        color_map[text_row0 + font_row][col] = TEXT_COLOR_HSV
            elif logo:
                logo_col = source_col - self._text_width - BANNER_LOGO_PADDING
                if 0 <= logo_col < small_cols:
                    for logo_row in range(small_rows):
                        pixel = logo[logo_row][logo_col]
                        if pixel:
                            color_map[logo_row0 + logo_row][col] = pixel

        self._banner_canvas.draw_color_map(color_map)
