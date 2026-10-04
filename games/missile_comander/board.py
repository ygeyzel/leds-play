from random import randrange, choice
from copy import deepcopy
from collections import deque

from games.missile_comander.colors import HSVColor, HSVNeutral

from platforms.interfaces import Key, KeyHandler


TURN_INTERVAL = 0.08



SHIP_COLOR_HSV = HSVColor.BLUE.value
METEOR_COLOR_HSV = HSVColor.RED.value
BORDER_COLOR_HSV = HSVColor.AZURE.with_sv(0.7, 0.6)
CITY_COLOR_HSV = HSVNeutral.WHITE.value
SHOT_COLOR_HSV = HSVColor.GREEN.value


AID_PACKGES_HSV = (200, 0.7, 0.6)

START_MAX_SHOT = 3
BASE_SHOT_MATRIX = [[1]]

base_city_matrix = [[0, 0, 1, 0, 0],
                    [0, 1, 1, 1, 0],
                    [1, 1, 1, 1, 1]]

SHIP_MATRIX = [[0, 1, 0],
               [1, 1, 1]]

SHIP_MATRIX2 = [[1, 0, 1],
                [1, 1, 1]]

SHIP_MATRIX3 = [[1, 0, 1, 0, 1],
                [1, 1, 1, 1, 1]]

SHIP_MATRIX_LIST = [SHIP_MATRIX, SHIP_MATRIX2, SHIP_MATRIX3]

SHOOTS_BY_LVL = {1: [1],
                 2: [0, 2],
                 3: [0, 2, 4]}

SPLINTER_SHOT_DIRECTIONS = {
    0: [(-1, 0)],                     # normal: straight up
    1: [(-1, -1), (-1, 1)],           # first take: two diagonals
    2: [(-1, -1), (-1, 1), (-1, 0)],  # second take: two diagonals + straight
}
SMALL_METEOR_MATRIX = [[1]]

BIG_METEOR_MATRIX = [[1, 1],
                     [1, 1]]

BOARD_HEIGHT = 31
BOARD_WIDTH = 40


# Both paddles move continuously while held (KeyHandler.is_pressed(), like
# Snake's run boost) rather than one-shot per get_key() click, so both
# players can move in the same turn.
_LEFT_KEYS = {Key.P2_UP: -1, Key.P2_DOWN: 1}
_RIGHT_KEYS = {Key.UP: -1, Key.DOWN: 1}


# ---------------------------------------------------------------------------
# Game objects
#
# Every object on the board (city, ship, shot, meteor, aid package) is a
# rigid shape: a `matrix` (2D grid of 0/1 cells) anchored at a board `pos`
# (top-left corner, [row, col]). GameObject holds all the geometry that's
# shared by every object type; each subclass only adds the extra state that
# is specific to it (ship level, meteor zig-zag/side/score, aid package
# type).
# ---------------------------------------------------------------------------

class GameObject:
    def __init__(self, pos, matrix):
        self.pos = list(pos)
        self.matrix = matrix

    @property
    def height(self):
        return len(self.matrix)

    @property
    def width(self):
        return len(self.matrix[0])

    def filled_offsets(self):
        """Returns the (i, j) matrix indices of every filled cell in this
        shape, relative to its own top-left corner — independent of its
        board position."""
        return [
            (i, j)
            for i, row in enumerate(self.matrix)
            for j, val in enumerate(row)
            if val
        ]

    def filled_cell_map(self, pos=None):
        """Maps board (x, y) position -> matrix (i, j) index, for filled
        cells only. Pass `pos` to check a hypothetical position instead of
        the object's current one (used for look-ahead bounds checks)."""
        pos_x, pos_y = pos if pos is not None else self.pos
        return {
            (pos_x + i, pos_y + j): (i, j)
            for i, j in self.filled_offsets()
        }

    def filled_cells(self, pos=None):
        """Returns the set of (x, y) board coordinates this shape occupies."""
        return set(self.filled_cell_map(pos).keys())

    def is_on_edge(self, pos=None):
        """True if the whole shape (not just its anchor) sits inside the
        board. Pass `pos` to test a hypothetical position instead of the
        object's current one."""
        pos = pos if pos is not None else self.pos
        if (0 < pos[0] and pos[0] + self.height <= BOARD_HEIGHT and
                0 < pos[1] and pos[1] + self.width <= BOARD_WIDTH):
            return True

    def is_empty(self):
        """True once every cell of this shape has been destroyed."""
        for row in self.matrix:
            if 1 in row:
                return
        return True


class City(GameObject):
    pass

class Ship(GameObject):
    def __init__(self, pos, matrix, level=1, splinter_level=0):
        super().__init__(pos, matrix)
        self.level = level
        self.splinter_level = splinter_level

class Shot(GameObject):
    def __init__(self, pos, matrix, direction=(-1, 0)):
        super().__init__(pos, matrix)
        self.direction = direction  # (d_row, d_col); default is straight up

class Meteor(GameObject):
    def __init__(self, pos, matrix, is_zig_zag=False, side=1, score=0):
        super().__init__(pos, matrix)
        self.is_zig_zag = is_zig_zag
        self.side = side
        self.score = score


class AidPackage(GameObject):
    def __init__(self, pos, matrix, aid_type):
        super().__init__(pos, matrix)
        self.type = aid_type


# ---------------------------------------------------------------------------
# Geometry helpers
#
# Pure functions used for continuous (swept) collision detection, so a
# fast-moving shot and meteor can't tunnel past each other between two
# ticks. They work on plain (row, col) points, not on GameObjects, so they
# have no dependency on the object model above.
# ---------------------------------------------------------------------------

def _turn_direction(start, mid, end):
    """Direction you turn going start -> mid -> end.
    Returns 0 if the three points are collinear, 1 for clockwise, 2 for
    counter-clockwise."""
    cross_product = ((mid[1] - start[1]) * (end[0] - mid[0]) -
                      (mid[0] - start[0]) * (end[1] - mid[1]))
    if cross_product == 0:
        return 0
    return 1 if cross_product > 0 else 2


def _point_is_between(segment_start, point, segment_end):
    """True if `point` lies within the bounding box of segment_start and
    segment_end, given the three points are already known to be
    collinear."""
    return (min(segment_start[0], segment_end[0]) <= point[0] <= max(segment_start[0], segment_end[0]) and
            min(segment_start[1], segment_end[1]) <= point[1] <= max(segment_start[1], segment_end[1]))


def _segments_intersect(seg_a_start, seg_a_end, seg_b_start, seg_b_end):
    """True if line segment A (seg_a_start -> seg_a_end) crosses or touches
    line segment B (seg_b_start -> seg_b_end)."""
    dir_a_to_b_start = _turn_direction(seg_a_start, seg_a_end, seg_b_start)
    dir_a_to_b_end = _turn_direction(seg_a_start, seg_a_end, seg_b_end)
    dir_b_to_a_start = _turn_direction(seg_b_start, seg_b_end, seg_a_start)
    dir_b_to_a_end = _turn_direction(seg_b_start, seg_b_end, seg_a_end)

    # general case: the segments straddle each other
    if dir_a_to_b_start != dir_a_to_b_end and dir_b_to_a_start != dir_b_to_a_end:
        return True

    # collinear edge cases: one segment's endpoint sits exactly on the other segment
    if dir_a_to_b_start == 0 and _point_is_between(seg_a_start, seg_b_start, seg_a_end):
        return True
    if dir_a_to_b_end == 0 and _point_is_between(seg_a_start, seg_b_end, seg_a_end):
        return True
    if dir_b_to_a_start == 0 and _point_is_between(seg_b_start, seg_a_start, seg_b_end):
        return True
    if dir_b_to_a_end == 0 and _point_is_between(seg_b_start, seg_a_end, seg_b_end):
        return True

    return False


def _cell_paths(obj, prev_pos):
    """For each filled cell in the shape, returns (where_it_was,
    where_it_is_now) on the board, assuming the shape only slid
    (translated), didn't rotate."""
    cur_pos = obj.pos
    paths = []
    for i, j in obj.filled_offsets():
        prev_cell = (prev_pos[0] + i, prev_pos[1] + j)
        cur_cell = (cur_pos[0] + i, cur_pos[1] + j)
        paths.append((prev_cell, cur_cell))
    return paths


def _swept_collide(obj_a, prev_pos_a, obj_b, prev_pos_b):
    """True if any filled cell of obj_a's swept path crossed or overlapped
    any filled cell of obj_b's swept path this turn. Works for shapes of
    any size, as long as they only translate (no rotation) between turns."""
    paths_a = _cell_paths(obj_a, prev_pos_a)
    paths_b = _cell_paths(obj_b, prev_pos_b)

    for prev_cell_a, cur_cell_a in paths_a:
        for prev_cell_b, cur_cell_b in paths_b:
            if _segments_intersect(prev_cell_a, cur_cell_a, prev_cell_b, cur_cell_b):
                return True

    return False


def _is_matrix_collide(obj_a_filled, obj_b_filled):
    return bool(obj_a_filled & obj_b_filled)


def resolve_bomb_collision(obj_a, obj_b):
    """Zeroes out every cell where obj_a and obj_b's filled cells overlap
    at their CURRENT positions (used for things that don't both move fast
    enough to tunnel, e.g. meteor vs. stationary city)."""
    a_cells = obj_a.filled_cell_map()
    b_cells = obj_b.filled_cell_map()

    collisions = list(a_cells.keys() & b_cells.keys())

    for board_pos in collisions:
        ai, aj = a_cells[board_pos]
        bi, bj = b_cells[board_pos]
        obj_a.matrix[ai][aj] = 0
        obj_b.matrix[bi][bj] = 0

    return collisions


class Board:

    """Missile Command is a classic arcade game
       target and shoot down incoming ballistic missiles before they destroy their six cities. 
       The game features an intensifying, endless onslaught that inevitably ends in total destruction, 
       serving as a bleak reflection of Cold War anxieties."""

    def __init__(self):
        self.score = 0
        self.high_score = 0
        self.cities = []
        self.ship = None
        self.shots = []
        self.meteors = []
        self.aid_packges = []
        self.game_over = False
        self.METEORS_CUONTER = 5
        self.max_shot = START_MAX_SHOT
        self.rel_max_shot = START_MAX_SHOT
        self.meteors_turn_frame = deque([True, False, False, False, False, False])

    def start(self):
        self.create_cities()
        self.create_ship()
        self.game_over = False

    def create_cities(self):
        for i in range(6):
            mod = 0
            if i > 2:
                mod += 3
            matrix = deepcopy(base_city_matrix)
            self.cities.append(City(pos=(25, 1 + (6 * i) + mod), matrix=matrix))

    def create_ship(self):
        self.ship = Ship(pos=[29, 18], matrix=deepcopy(SHIP_MATRIX), level=1)

    def _add_shot(self):
        if len(self.shots) < self.rel_max_shot:
            self.shots += self._create_shot()

    def _create_shot(self):
        shots = []
        ship_pos_x, ship_pos_y = self.ship.pos
        directions = SPLINTER_SHOT_DIRECTIONS[self.ship.splinter_level]

        for rel_pos in SHOOTS_BY_LVL[self.ship.level]:
            shot_origin = [ship_pos_x, ship_pos_y + rel_pos]
            for direction in directions:
                shots.append(Shot(pos=shot_origin.copy(),
                                   matrix=deepcopy(BASE_SHOT_MATRIX),
                                   direction=direction))

        return shots

    def _create_aid_packge(self, value):
        aid_types = ['extra shot', 'extra canon', 'slawer meteors',
                     'city hp', 'splinter shot', 'dubel score']
        # exta cannon need to be orenge!!!
        self.aid_packges.append(
            AidPackage(pos=[1, randrange(1, 40)], matrix=[[1]], aid_type='splinter shot')
        )
        self.aid_packges.append(
            AidPackage(pos=[1, randrange(1, 40)], matrix=[[1]], aid_type='extra canon')
        )
        

    def is_game_over(self) -> bool:
        return self.game_over

    def advance_turn(self, key_handler: KeyHandler):
        self.advence_player_input(key_handler)
        self._generate_meteors()

        prev_shot_pos = {id(s): tuple(s.pos) for s in self.shots}
        self._advence_shots()
        self._advence_aid_packges()

        prev_meteor_pos = {id(m): tuple(m.pos) for m in self.meteors}
        if self.meteors_turn_frame[0]:
            self._advence_meteors()

        self._meteors_shot_colide(prev_meteor_pos, prev_shot_pos)
        self._meteors_city_colide()
        self._aid_packges_ship_colide()
        self.remove_dead_object()

        self.meteors_turn_frame.rotate(-1)
        if len(self.cities) == 0:
            self.game_over = True

    def _generate_meteors(self):
        if randrange(0, self.METEORS_CUONTER) > 2:
            self.meteors.append(self._create_meteore())

    def _create_meteore(self, zig_zag=False):
        big_presentage = self.score % 10
        zig_zag_presentage = self.score % 15

        if randrange(101) < big_presentage:
            meteore_matrix = BIG_METEOR_MATRIX
        else:
            meteore_matrix = SMALL_METEOR_MATRIX

        if randrange(101) < zig_zag_presentage:
            zig_zag = True

        side = choice([1, -1])

        meteor_score = 5 + (zig_zag * 5) + (len(meteore_matrix) * 5)
        starter_pos = [1, randrange(1, 39)]

        return Meteor(pos=starter_pos, matrix=deepcopy(meteore_matrix),
                      is_zig_zag=zig_zag, side=side, score=meteor_score)

    def advence_player_input(self, key_handler):
        if key_handler.is_pressed(Key.LEFT):
            prospective_pos = [self.ship.pos[0], self.ship.pos[1] - 1]
            print(prospective_pos)
            if self.ship.is_on_edge(prospective_pos):
                self.ship.pos[1] -= 1

        if key_handler.is_pressed(Key.RIGHT):
            prospective_pos = [self.ship.pos[0], self.ship.pos[1] + 1]
            print(prospective_pos)
            if self.ship.is_on_edge(prospective_pos):
                self.ship.pos[1] += 1

        if key_handler.is_pressed(Key.UP):
            self._add_shot()

    def _advence_shots(self):
        for shot in self.shots:
            d_row, d_col = shot.direction
            shot.pos[0] += d_row
            shot.pos[1] += d_col

        self.shots = [s for s in self.shots if s.is_on_edge()]

    def _advence_meteors(self):
        for meteor in self.meteors:
            if meteor.is_zig_zag:
                prospective_pos = [meteor.pos[0], meteor.pos[1] + meteor.side]
                if not meteor.is_on_edge(prospective_pos):
                    meteor.side *= -1
                meteor.pos[1] += meteor.side
            meteor.pos[0] += 1

        self.meteors = [m for m in self.meteors if m.is_on_edge()]


    def _advence_aid_packges(self):
        for aid_packge in self.aid_packges:
            aid_packge.pos[0] += 1

        self.aid_packges = [ap for ap in self.aid_packges if ap.is_on_edge()]

    def _meteors_shot_colide(self, prev_meteor_pos, prev_shot_pos):
        for meteor in self.meteors.copy():
            for shot in self.shots.copy():
                if _swept_collide(meteor, prev_meteor_pos[id(meteor)],
                                   shot, prev_shot_pos[id(shot)]):
                    resolve_bomb_collision(meteor, shot)
                    if meteor.is_empty():
                        self._reword(meteor)

    def _meteors_city_colide(self):
        for meteor in self.meteors:
            for city in self.cities:
                if _is_matrix_collide(meteor.filled_cells(), city.filled_cells()):
                    resolve_bomb_collision(meteor, city)

    def _aid_packges_ship_colide(self):
        aid_packge_collide = []
        for aid_packge in self.aid_packges:
            if _is_matrix_collide(aid_packge.filled_cells(), self.ship.filled_cells()):
                if self.is_aid_collide(aid_packge, self.ship):
                    aid_packge_collide.append(aid_packge)

        for aid_packge in aid_packge_collide:
            self.aid_packge_proses(aid_packge.type)
            aid_packge.matrix = [[0]]

    @staticmethod
    def is_aid_collide(aid_packge, ship):
        aid_packge_filled = aid_packge.filled_cell_map()
        ship_filled = ship.filled_cell_map()
        collisions = list(aid_packge_filled.keys() & ship_filled.keys())
        return bool(collisions)

    def aid_packge_proses(self, aid_type):
        match aid_type:
            case 'extra shot':
                self.max_shot += 1
                self.rel_max_shot += 1 * self.ship.level

            case 'slawer meteors':
                self.meteors_turn_frame += [False]

            case 'city hp':
                random_city = randrange(6)
                self.cities[random_city].matrix = deepcopy(base_city_matrix)

            case 'extra canon':
                if self.ship.level < 3:
                    self.ship.level += 1
                    self.rel_max_shot += (self.max_shot * self.ship.splinter_level)

                self.ship.matrix = deepcopy(SHIP_MATRIX_LIST[self.ship.level - 1])

            case 'splinter shot':
                if self.ship.splinter_level < 2:
                    self.ship.splinter_level += 1
                    self.rel_max_shot += (self.max_shot * self.ship.level)

            case 'dubel score':
                self.score *= 2

    def remove_dead_object(self):
        self.shots = [shot for shot in self.shots if not shot.is_empty()]
        self.meteors = [meteor for meteor in self.meteors if not meteor.is_empty()]
        self.aid_packges = [ap for ap in self.aid_packges if not ap.is_empty()]

    def _reword(self, meteor):
        self.score += meteor.score
        packge_value = randrange(meteor.score)
        packge_value = 10
        if packge_value > 5:
            self._create_aid_packge(packge_value)