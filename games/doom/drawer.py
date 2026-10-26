import colorsys
import math
from functools import lru_cache
from typing import Optional

from games.doom.board import ESCAPED_TIME, HURT_TIME, MAX_DEPTH, PLAYER_HP, Board, cast_ray
from platforms.interfaces import Matrix

# Every pixel of the board is lit (walls/ceiling/floor), unlike the other
# games' mostly-dark screens, so colors are scaled way down on output.
BRIGHTNESS = 0.2

CEILING_COLOR = (0, 0, 0)
FLOOR_COLOR = (0, 0, 0)
FLASH_COLOR = (255, 230, 60)
MUZZLE_COLOR = (255, 140, 30)
GUN_COLOR = (110, 110, 125)
GUN_DARK = (60, 60, 70)
CROSSHAIR_COLOR = (255, 255, 255)
HURT_TINT = (255, 0, 0)
ESCAPED_TINT = (40, 230, 80)
UNKNOWN_WALL_COLOR = (128, 128, 128)

# Gun drawn at the bottom centre of the view: (dx from centre-left, dy from bottom).
GUN = [
    ((0, -5), GUN_DARK), ((1, -5), GUN_DARK),
    ((0, -4), GUN_DARK), ((1, -4), GUN_DARK),
] + [((dx, dy), GUN_COLOR) for dy in (-3, -2, -1, 0) for dx in (-1, 0, 1, 2)]


def _lerp(a, b, t):
    return tuple(int(a[i] + (b[i] - a[i]) * t) for i in range(3))


def _scale(color, factor):
    return tuple(max(0, min(255, int(c * factor))) for c in color)


def _shade(dist):
    return 1 / (1 + dist * dist * 0.03)


@lru_cache(maxsize=8192)
def _to_hsv(rgb):
    h, s, v = colorsys.rgb_to_hsv(*(c / 255 for c in rgb))
    return (h * 360, s, v * BRIGHTNESS)


class Drawer:
    """Raycasts the board's maze into a full-board first-person view. The
    frame is built as RGB rows (blending is simpler there) and only pixels
    that changed since the last frame are written to the matrix."""

    def __init__(self, matrix: Matrix, banner_matrix: Optional[Matrix] = None):
        self._matrix = matrix
        self._banner_matrix = banner_matrix
        self._canvas = matrix.create_canvas((0, 0), matrix.dimensions)
        self.height, self.width = matrix.dimensions

        self.board = Board(matrix.dimensions)
        self._shown = None
        self._blink_on = False

    def reset(self):
        """Forget what's on the matrix (the menu or a previous round drew
        over it), so the next frame repaints every pixel."""
        self._shown = [[None] * self.width for _ in range(self.height)]
        self._blink_on = False
        if self._banner_matrix:
            self._banner_matrix.clear()
            self._banner_matrix.show()

    def draw_board(self, tint_override=None):
        board = self.board
        frame = self._render_view()
        self._draw_hud(frame)

        if tint_override is not None:
            self._tint(frame, HURT_TINT, tint_override)
        elif board.is_game_over():
            self._tint(frame, HURT_TINT, 0.45)
        elif board.hurt:
            self._tint(frame, HURT_TINT, 0.45 * board.hurt / HURT_TIME)
        elif board.escaped:
            self._tint(frame, ESCAPED_TINT, 0.45 * board.escaped / ESCAPED_TIME)

        self._show_frame(frame)

    def blink_board(self):
        """Pulse the red "you're dead" tint - called repeatedly on game
        over (see DoomGame.on_game_over_tick)."""
        self._blink_on = not self._blink_on
        self.draw_board(0.6 if self._blink_on else 0.2)

    # -- view

    def _render_view(self):
        board = self.board
        grid, colors, player = board.grid, board.colors, board.player
        half = self.height / 2
        frame = [[CEILING_COLOR if y < half else FLOOR_COLOR] * self.width
                 for y in range(self.height)]

        dir_x, dir_y, plane_x, plane_y = board.camera.vectors(player)
        zbuffer = [MAX_DEPTH] * self.width

        for x in range(self.width):
            camera_x = 2 * (x + 0.5) / self.width - 1
            ray_dx = dir_x + plane_x * camera_x
            ray_dy = dir_y + plane_y * camera_x
            dist, hit_x, hit_y, side = cast_ray(grid, player.x, player.y, ray_dx, ray_dy)
            zbuffer[x] = dist

            line_h = self.height / dist
            top = int(round(half - line_h / 2))
            bottom = int(round(half + line_h / 2))
            # side 0 = ray hit an east/west face, side 1 = a north/south face.
            base = colors.get((hit_x, hit_y), (UNKNOWN_WALL_COLOR,) * 2)[side]
            color = _scale(base, (0.7 if side else 1.0) * _shade(dist))
            for y in range(max(0, top), min(self.height, bottom)):
                frame[y][x] = color

        npc = board.npc
        screen_x, depth = board.camera.project(player, npc.x, npc.y)
        if screen_x is not None:
            self._draw_sprite(frame, zbuffer, screen_x, depth, npc.pose(), npc.color())
        return frame

    def _draw_sprite(self, frame, zbuffer, screen_x, depth, pose, color):
        color = _scale(color, _shade(depth))
        # Use the largest version that fits without shrinking, else the smallest.
        for bitmap, height in pose:
            cell = (self.height / depth) * height / len(bitmap)  # screen px per bitmap px
            if cell >= 1:
                break
        rows, cols = len(bitmap), len(bitmap[0])
        floor_y = self.height / 2 + self.height / depth / 2
        top = floor_y - rows * cell
        left = screen_x - cols * cell / 2

        def span(start, origin, limit):
            """Bitmap pixels under the screen pixel starting at `start`."""
            if cell >= 1:
                # Enlarged: sample the pixel centre, which keeps lines thin.
                i = math.floor((start + 0.5 - origin) / cell)
                return range(i, i + 1) if 0 <= i < limit else range(0)
            # Shrunk: light the pixel if any bitmap pixel it covers is set, so
            # thin lines don't disappear between samples.
            lo = max(0, math.floor((start - origin) / cell))
            hi = min(limit, math.ceil((start + 1 - origin) / cell))
            return range(lo, hi)

        for x in range(max(0, math.floor(left)), min(self.width, math.ceil(left + cols * cell))):
            if depth >= zbuffer[x]:
                continue
            us = span(x, left, cols)
            for y in range(max(0, math.floor(top)), min(self.height, math.ceil(floor_y))):
                marks = {bitmap[v][u] for v in span(y, top, rows) for u in us}
                if "*" in marks:
                    frame[y][x] = FLASH_COLOR
                elif "#" in marks:
                    frame[y][x] = color

    # -- HUD

    def _draw_hud(self, frame):
        """Overlay gun, crosshair and health bar on the frame."""
        board = self.board
        firing = board.firing > 0
        cx = self.width // 2 - 1
        recoil = 1 if firing else 0
        for (dx, dy), color in GUN:
            y = self.height - 1 + dy + recoil
            if 0 <= y < self.height:
                frame[y][cx + dx] = color
        if firing:
            frame[self.height - 6][cx] = frame[self.height - 6][cx + 1] = FLASH_COLOR
            frame[self.height - 7][cx] = frame[self.height - 7][cx + 1] = MUZZLE_COLOR

        # Faint ticks either side of centre, blended so they don't hide the target.
        mid = self.height // 2
        for x in (self.width // 2 - 3, self.width // 2 + 2):
            frame[mid][x] = _lerp(frame[mid][x], CROSSHAIR_COLOR, 0.5)

        t = max(0, board.hp) / PLAYER_HP
        bar = (int(255 * (1 - t)), int(220 * t), 40)
        for x in range(math.ceil(t * self.width)):
            frame[0][x] = bar

    @staticmethod
    def _tint(frame, tint, amount):
        for row in frame:
            for x, c in enumerate(row):
                row[x] = _lerp(c, tint, amount)

    # -- output

    def _show_frame(self, frame):
        canvas, shown = self._canvas, self._shown
        for y, row in enumerate(frame):
            shown_row = shown[y]
            for x, color in enumerate(row):
                if shown_row[x] != color:
                    shown_row[x] = color
                    canvas[y, x] = _to_hsv(color)
        self._matrix.show()
