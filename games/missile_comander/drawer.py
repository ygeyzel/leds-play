from typing import Optional

from common.common import add_positions
from games.missile_comander.board import Board
from games.missile_comander.colors import HSVColor, HSVNeutral

from platforms.interfaces import Matrix


BOARD_POS_0 = (0, 0)





SHIP_COLOR_HSV = HSVColor.BLUE.value
SHIP2_COLOR_HSV = HSVColor.MAGENTA.value
METEOR_COLOR_HSV = HSVColor.RED.value
BORDER_COLOR_HSV = HSVColor.AZURE.with_sv(0.7, 0.6)
CITY_COLOR_HSV = HSVNeutral.WHITE.value
SHOT_COLOR_HSV = HSVColor.GREEN.value
AID_PACKGES_HSV = (200, 0.7, 0.6)

AID_EXTRA_SHOT_HSV = HSVColor.GREEN.value
AID_EXTRA_CANON_HSV = HSVColor.YELLOW.value
AID_SLAWER_METEORS_HSV = HSVColor.ROSE.value
AID_CITY_HP_HSV = HSVNeutral.WHITE.value
AID_SPLINTER_SHOT_HSV = HSVColor.AZURE.value
AID_DUBEL_SCORE_HSV = HSVColor.ORANGE.value

AID_COLOR_BY_TYPE = {
    'extra shot': AID_EXTRA_SHOT_HSV,
    'extra canon': AID_EXTRA_CANON_HSV,
    'slawer meteors': AID_SLAWER_METEORS_HSV,
    'city hp': AID_CITY_HP_HSV,
    'splinter shot': AID_SPLINTER_SHOT_HSV,
    'dubel score': AID_DUBEL_SCORE_HSV,
}




class Drawer:
    def __init__(self, matrix: Matrix, banner_matrix: Optional[Matrix] = None):
        self._matrix = matrix
        self._banner_matrix = banner_matrix

        board = Board()
        self._canvas_dimensions = matrix.dimensions  # (rows, cols)
        self._board_canvas = self._matrix.create_canvas(
            BOARD_POS_0, self._canvas_dimensions)

        self.board = board
        self._city_color = CITY_COLOR_HSV
        self._ship_colors = [SHIP_COLOR_HSV, SHIP2_COLOR_HSV]
        self._shot_color = SHOT_COLOR_HSV
        self._meteor_color = METEOR_COLOR_HSV
        self._aid_packges_color = AID_PACKGES_HSV

    def draw_board(self):
        self.draw_cities()
        self.draw_ships()
        self.draw_miteors()
        self.draw_shots()
        self.draw_aid_packges()
        self.show()

    def _is_inside_canvas(self, pos):
        rows, cols = self._canvas_dimensions
        return 0 <= pos[0] < rows and 0 <= pos[1] < cols

    def draw_object(self, game_object, color):
        """Paints every filled cell of one object. Cells outside the canvas
        are skipped instead of raising, so an object that reaches (or
        pokes past) an edge can never crash the drawer."""
        for pos in game_object.filled_cells():
            if self._is_inside_canvas(pos):
                self._board_canvas[pos] = color

    def draw_list(self, game_objects, color):
        """`color` is either one color for every object, or a function that
        picks the color of each object, e.g. `lambda pkg: COLORS[pkg.type]`."""
        for game_object in game_objects:
            self.draw_object(game_object, color(game_object) if callable(color) else color)

    def draw_ships(self):
        for ship, color in zip(self.board.ships, self._ship_colors):
            self.draw_object(ship, color)

    def draw_cities(self):
        self.draw_list(self.board.cities, self._city_color)

    def draw_miteors(self):
        self.draw_list(self.board.meteors, self._meteor_color)

    def draw_shots(self):
        self.draw_list(self.board.shots, self._shot_color)

    def draw_aid_packges(self):
        self.draw_list(self.board.aid_packges,
                       lambda aid_packge: AID_COLOR_BY_TYPE[aid_packge.type])

    def show(self):
        self._matrix.show()
        if self._banner_matrix:
            self._banner_matrix.show()

    def clear(self):
        self._matrix.clear()
        if self._banner_matrix:
            self._banner_matrix.clear()