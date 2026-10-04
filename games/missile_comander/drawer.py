from typing import Optional

from common.common import add_positions
from games.missile_comander.board import Board, BORDER_COLOR_HSV, AID_PACKGES_HSV, CITY_COLOR_HSV, SHIP_COLOR_HSV, SHOT_COLOR_HSV, METEOR_COLOR_HSV
from platforms.interfaces import Matrix


BOARD_POS_0 = (0, 0)


class Drawer:
    def __init__(self, matrix: Matrix, banner_matrix: Optional[Matrix] = None):
        self._matrix = matrix
        self._banner_matrix = banner_matrix

        board = Board()
        self._board_canvas = self._matrix.create_canvas(
            BOARD_POS_0, matrix.dimensions)

        self.board = board
        self._city_color = CITY_COLOR_HSV
        self._ship_color = SHIP_COLOR_HSV
        self._shot_color = SHOT_COLOR_HSV
        self._meteor_color = METEOR_COLOR_HSV
        self._aid_packges_color = AID_PACKGES_HSV

    def draw_board(self):
        self._board_canvas.draw_borders(BORDER_COLOR_HSV)
        self.draw_cities()
        self.draw_ship()
        self.draw_miteors()
        self.draw_shots()
        self.draw_aid_packges()
        self.show()

    @staticmethod
    def get_metrix_pos(game_object):
        all_object_pos = []
        for i, row in enumerate(game_object.matrix):
            for j, col in enumerate(row):
                if col:
                    x = game_object.pos[0] + i
                    y = game_object.pos[1] + j
                    all_object_pos.append((x, y))

        return all_object_pos

    def draw_list(self, game_objects, color):
        for game_object in game_objects:
            all_object_pos = self.get_metrix_pos(game_object)
            for pos in all_object_pos:
                self._board_canvas[pos] = color

    def draw_ship(self):
        ship = self.board.ship
        all_ship_pos = self.get_metrix_pos(ship)
        for pos in all_ship_pos:
            self._board_canvas[pos] = self._ship_color

    def draw_cities(self):
        self.draw_list(self.board.cities, self._city_color)

    def draw_miteors(self):
        self.draw_list(self.board.meteors, self._meteor_color)

    def draw_shots(self):
        self.draw_list(self.board.shots, self._shot_color)

    def draw_aid_packges(self):
        self.draw_list(self.board.aid_packges, self._shot_color)

    def show(self):
        self._matrix.show()
        if self._banner_matrix:
            self._banner_matrix.show()

    def clear(self):
        self._matrix.clear()
        if self._banner_matrix:
            self._banner_matrix.clear()