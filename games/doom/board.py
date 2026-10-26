import math
import random

from games.doom.sprites import POSES, STICK_HALF_WIDTH

MAZE_CELLS = 7  # maze is MAZE_CELLS x MAZE_CELLS corridors

# Horizontal field of view on a square (rows == cols) view; a wider view
# widens it to match, so pixels keep the same aspect ratio.
SQUARE_FOV = math.radians(66)
MOVE_SPEED = 2.5  # cells per second
TURN_SPEED = math.radians(120)  # radians per second
PLAYER_RADIUS = 0.2
MAX_DEPTH = 20.0

PLAYER_HP = 100
FIRE_COOLDOWN = 0.3  # seconds between player shots
FIRING_TIME = 0.08  # how long the muzzle flash/recoil shows
HURT_TIME = 0.25  # how long the red damage tint shows
ESCAPED_TIME = 0.6  # how long the green "next maze" tint shows

NPC_HP = 3  # hits to kill the NPC
NPC_SPEED = 1.5  # cells per second
NPC_SIGHT = 8.0  # how far the NPC can see, in cells
NPC_REACTION = 0.7  # delay before the NPC fires after spotting you
NPC_FIRE_COOLDOWN = 1.2
NPC_DAMAGE = 15
NPC_RESPAWN = 3.0  # seconds a dead NPC stays down

KILL_POINTS = 10
ESCAPE_POINTS = 50

WALL = 1
EXIT = 2

# RGB, not HSV like the other games: the drawer blends these (distance
# shading, damage tint) per pixel and only converts to HSV on output.
EXIT_COLOR = (40, 230, 80)
NPC_COLOR = (245, 245, 245)
NPC_HURT_COLOR = (255, 40, 40)
NPC_DEAD_COLOR = (150, 30, 30)
WALL_PALETTE = [
    (220, 60, 60),  # red
    (60, 120, 230),  # blue
    (240, 200, 50),  # yellow
    (180, 80, 220),  # purple
    (50, 200, 210),  # cyan
    (240, 130, 40),  # orange
    (230, 90, 170),  # pink
]


# ---------------------------------------------------------------- maze


def generate_maze(cells_w, cells_h, rng=random):
    """Recursive-backtracker maze. Returns a grid of (2*cells+1) squares."""
    w, h = cells_w * 2 + 1, cells_h * 2 + 1
    grid = [[WALL] * w for _ in range(h)]
    stack = [(0, 0)]
    visited = {(0, 0)}
    grid[1][1] = 0
    while stack:
        cx, cy = stack[-1]
        neighbours = [
            (cx + dx, cy + dy)
            for dx, dy in ((1, 0), (-1, 0), (0, 1), (0, -1))
            if 0 <= cx + dx < cells_w and 0 <= cy + dy < cells_h
            and (cx + dx, cy + dy) not in visited
        ]
        if not neighbours:
            stack.pop()
            continue
        nx, ny = rng.choice(neighbours)
        grid[cy * 2 + 1 + (ny - cy)][cx * 2 + 1 + (nx - cx)] = 0
        grid[ny * 2 + 1][nx * 2 + 1] = 0
        visited.add((nx, ny))
        stack.append((nx, ny))
    # Exit door in the outer wall next to the far corner.
    grid[h - 2][w - 1] = EXIT
    return grid


def _wall_runs(grid):
    """Split the walls into straight sections.

    Returns (runs, h_run, v_run): the sections' cell lists, and dicts
    mapping a wall cell to the index of the horizontal / vertical section
    (2+ cells long) it belongs to.
    """
    h, w = len(grid), len(grid[0])
    runs = []
    h_run, v_run = {}, {}
    for horizontal in (True, False):
        outer, inner = (h, w) if horizontal else (w, h)
        target = h_run if horizontal else v_run
        for a in range(outer):
            b = 0
            while b < inner:
                cells = []
                while b < inner:
                    x, y = (b, a) if horizontal else (a, b)
                    if grid[y][x] != WALL:
                        break
                    cells.append((x, y))
                    b += 1
                if len(cells) >= 2:
                    for c in cells:
                        target[c] = len(runs)
                    runs.append(cells)
                b += 1
    # Lone wall cells (no straight neighbours) become their own section.
    for y in range(h):
        for x in range(w):
            if grid[y][x] == WALL and (x, y) not in h_run and (x, y) not in v_run:
                h_run[(x, y)] = len(runs)
                runs.append([(x, y)])
    return runs, h_run, v_run


def color_walls(grid, rng=random):
    """Give each straight wall section one solid colour.

    Returns a dict mapping a wall cell to (x-face colour, y-face colour):
    the face a ray hits decides which section's colour is shown, so the
    end post of a horizontal wall still looks like part of that wall.
    """
    runs, h_run, v_run = _wall_runs(grid)

    run_color = []
    for cells in runs:
        # Avoid colours of sections that touch or sit diagonally next to this one.
        nearby = set()
        for x, y in cells:
            for dx in (-1, 0, 1):
                for dy in (-1, 0, 1):
                    for lookup in (h_run, v_run):
                        r = lookup.get((x + dx, y + dy))
                        if r is not None and r < len(run_color):
                            nearby.add(run_color[r])
        choices = [c for c in WALL_PALETTE if c not in nearby] or WALL_PALETTE
        run_color.append(rng.choice(choices))

    colors = {}
    for y, row in enumerate(grid):
        for x, cell in enumerate(row):
            if cell == EXIT:
                colors[(x, y)] = (EXIT_COLOR, EXIT_COLOR)
            elif cell == WALL:
                hr, vr = h_run.get((x, y)), v_run.get((x, y))
                x_face = run_color[vr if vr is not None else hr]
                y_face = run_color[hr if hr is not None else vr]
                colors[(x, y)] = (x_face, y_face)
    return colors


def cell_at(grid, x, y):
    return grid[int(y)][int(x)]


def _blocked(grid, x, y):
    return cell_at(grid, x, y) == WALL


def cast_ray(grid, px, py, ray_dx, ray_dy):
    """DDA raycast. Returns (perpendicular distance, hit x, hit y, side)."""
    map_x, map_y = int(px), int(py)
    delta_x = abs(1 / ray_dx) if ray_dx else float("inf")
    delta_y = abs(1 / ray_dy) if ray_dy else float("inf")
    if ray_dx < 0:
        step_x, side_x = -1, (px - map_x) * delta_x
    else:
        step_x, side_x = 1, (map_x + 1 - px) * delta_x
    if ray_dy < 0:
        step_y, side_y = -1, (py - map_y) * delta_y
    else:
        step_y, side_y = 1, (map_y + 1 - py) * delta_y

    while True:
        if side_x < side_y:
            side_x += delta_x
            map_x += step_x
            side = 0
        else:
            side_y += delta_y
            map_y += step_y
            side = 1
        if not (0 <= map_y < len(grid) and 0 <= map_x < len(grid[0])):
            return MAX_DEPTH, map_x, map_y, side
        if grid[map_y][map_x]:
            dist = side_x - delta_x if side == 0 else side_y - delta_y
            return max(dist, 1e-6), map_x, map_y, side


def line_of_sight(grid, ax, ay, bx, by):
    """True if no wall lies on the straight line between two points."""
    dx, dy = bx - ax, by - ay
    if not (dx or dy):
        return True
    # With an unnormalised direction, cast_ray measures distance in units
    # of the whole a->b vector, so a wall before b means a result < 1.
    return cast_ray(grid, ax, ay, dx, dy)[0] >= 1


# -------------------------------------------------------------- player


class Player:
    def __init__(self, x, y, angle):
        self.x = x
        self.y = y
        self.angle = angle

    def turn(self, delta):
        self.angle = (self.angle + delta) % (2 * math.pi)

    def move(self, grid, forward, strafe=0.0):
        dx = math.cos(self.angle) * forward - math.sin(self.angle) * strafe
        dy = math.sin(self.angle) * forward + math.cos(self.angle) * strafe
        # Resolve each axis separately so the player slides along walls.
        if dx:
            nx = self.x + dx
            if not _blocked(grid, nx + math.copysign(PLAYER_RADIUS, dx), self.y):
                self.x = nx
        if dy:
            ny = self.y + dy
            if not _blocked(grid, self.x, ny + math.copysign(PLAYER_RADIUS, dy)):
                self.y = ny


class Camera:
    """The player's view onto a `dimensions` (rows, cols) screen."""

    def __init__(self, dimensions):
        self.height, self.width = dimensions
        self.plane_len = math.tan(SQUARE_FOV / 2) * self.width / self.height

    def vectors(self, player):
        """(dir_x, dir_y, plane_x, plane_y) for `player`'s facing."""
        dir_x, dir_y = math.cos(player.angle), math.sin(player.angle)
        return dir_x, dir_y, -dir_y * self.plane_len, dir_x * self.plane_len

    def project(self, player, x, y):
        """Project a world point to (screen x, depth). Depth <= 0 is behind us."""
        dir_x, dir_y, plane_x, plane_y = self.vectors(player)
        rx, ry = x - player.x, y - player.y
        inv = 1.0 / (plane_x * dir_y - dir_x * plane_y)
        lateral = inv * (dir_y * rx - dir_x * ry)
        depth = inv * (-plane_y * rx + plane_x * ry)
        if depth <= 0:
            return None, depth
        return self.width / 2 * (1 + lateral / depth), depth


# ----------------------------------------------------------------- NPC


class NPC:
    def __init__(self, x, y):
        self.x = x
        self.y = y
        self.angle = 0.0
        self.hp = NPC_HP
        self.alive = True
        self.target = (int(x), int(y))
        self.prev = self.target
        self.sees_player = False
        self.cooldown = 0.0
        self.hurt_time = 0.0
        self.flash_time = 0.0
        self.dead_time = 0.0
        self.walk_phase = 0.0

    def hit(self):
        """Take one bullet. Returns True if this killed the NPC."""
        self.hp -= 1
        self.hurt_time = 0.2
        if self.hp <= 0:
            self.alive = False
            self.dead_time = NPC_RESPAWN
            return True
        return False

    def update(self, dt, grid, player, rng=random):
        """Advance the NPC. Returns True if it shot and hit the player."""
        self.hurt_time = max(0.0, self.hurt_time - dt)
        self.flash_time = max(0.0, self.flash_time - dt)
        if not self.alive:
            self.dead_time -= dt
            return False

        dist = math.hypot(player.x - self.x, player.y - self.y)
        sees = dist < NPC_SIGHT and line_of_sight(
            grid, self.x, self.y, player.x, player.y)
        if sees and not self.sees_player:
            self.cooldown = max(self.cooldown, NPC_REACTION)
        self.sees_player = sees
        self.cooldown = max(0.0, self.cooldown - dt)

        if sees:
            # Stand still, face the player and shoot.
            self.angle = math.atan2(player.y - self.y, player.x - self.x)
            if self.cooldown <= 0:
                self.cooldown = NPC_FIRE_COOLDOWN
                self.flash_time = 0.12
                return rng.random() < max(0.2, 0.75 - dist * 0.05)
            return False

        self._wander(dt, grid, rng)
        return False

    def _wander(self, dt, grid, rng):
        tx, ty = self.target[0] + 0.5, self.target[1] + 0.5
        dx, dy = tx - self.x, ty - self.y
        dist = math.hypot(dx, dy)
        step = NPC_SPEED * dt
        self.walk_phase += step
        if dist > step:
            self.x += dx / dist * step
            self.y += dy / dist * step
            self.angle = math.atan2(dy, dx)
            return
        self.x, self.y = tx, ty
        cx, cy = self.target
        options = [
            (cx + ox, cy + oy)
            for ox, oy in ((1, 0), (-1, 0), (0, 1), (0, -1))
            if grid[cy + oy][cx + ox] == 0 and (cx + ox, cy + oy) != self.prev
        ]
        self.prev = self.target
        self.target = rng.choice(options) if options else self.prev

    def pose(self):
        if not self.alive:
            return POSES["dead"]
        if self.flash_time:
            return POSES["fire"]
        if self.sees_player:
            return POSES["aim"]
        return POSES["walk%d" % (int(self.walk_phase * 3) % 2)]

    def color(self):
        if not self.alive:
            return NPC_DEAD_COLOR
        return NPC_HURT_COLOR if self.hurt_time else NPC_COLOR


def spawn_point(grid, player, min_dist=6.0, rng=random):
    """A random corridor cell centre, preferably far from the player."""
    cells = [
        (x + 0.5, y + 0.5)
        for y in range(1, len(grid), 2)
        for x in range(1, len(grid[0]), 2)
    ]
    far = [c for c in cells
           if math.hypot(c[0] - player.x, c[1] - player.y) >= min_dist]
    return rng.choice(far or cells)


# --------------------------------------------------------------- board


class Board:
    """A first-person maze shooter: find the green exit door while an NPC
    stickman wanders the maze and shoots at you on sight. Unlike the other
    games, time advances by real seconds (`advance(dt, ...)`), not by
    whole turns, so movement stays smooth whatever the frame rate.

    Escaping a maze scores ESCAPE_POINTS and drops you into a fresh one
    with your remaining HP; killing the NPC scores KILL_POINTS. The round
    ends when your HP runs out."""

    def __init__(self, view_dims, rng=random):
        self.camera = Camera(view_dims)
        self._rng = rng
        self.score = 0
        self.hp = PLAYER_HP

    def start(self):
        self.score = 0
        self.hp = PLAYER_HP
        self.hurt = 0.0
        self.escaped = 0.0
        self._new_maze()

    def _new_maze(self):
        self.grid = generate_maze(MAZE_CELLS, MAZE_CELLS, self._rng)
        self.colors = color_walls(self.grid, self._rng)
        self.player = Player(1.5, 1.5, 0.0)
        self.npc = NPC(*spawn_point(self.grid, self.player, rng=self._rng))
        self.fire_cooldown = 0.0
        self.firing = 0.0

    def is_game_over(self) -> bool:
        return self.hp <= 0

    def advance(self, dt, forward=0, turn=0, strafe=0, fire=False):
        """Advance by `dt` seconds. forward/turn/strafe are -1, 0 or 1
        (back/left/left, none, forward/right/right)."""
        self.firing = max(0.0, self.firing - dt)
        self.hurt = max(0.0, self.hurt - dt)
        self.escaped = max(0.0, self.escaped - dt)
        if self.is_game_over():
            return

        self._update_player(dt, forward, turn, strafe, fire)
        self._update_npc(dt)

        p = self.player
        ahead = cell_at(self.grid, p.x + math.cos(p.angle) * 0.5,
                        p.y + math.sin(p.angle) * 0.5)
        if ahead == EXIT:
            self.score += ESCAPE_POINTS
            self.escaped = ESCAPED_TIME
            self._new_maze()

    def _update_player(self, dt, forward, turn, strafe, fire):
        if turn:
            self.player.turn(turn * TURN_SPEED * dt)
        if forward or strafe:
            step = MOVE_SPEED * dt
            self.player.move(self.grid, forward * step, strafe * step)

        self.fire_cooldown = max(0.0, self.fire_cooldown - dt)
        if fire and self.fire_cooldown <= 0:
            self.fire_cooldown = FIRE_COOLDOWN
            self.firing = FIRING_TIME
            npc = self.npc
            if npc.alive and self._shot_hits(npc.x, npc.y):
                if npc.hit():
                    self.score += KILL_POINTS

    def _update_npc(self, dt):
        npc = self.npc
        if npc.update(dt, self.grid, self.player, self._rng):
            self.hp = max(0, self.hp - NPC_DAMAGE)
            self.hurt = HURT_TIME
        if not npc.alive and npc.dead_time <= 0:
            self.npc = NPC(*spawn_point(self.grid, self.player, rng=self._rng))

    def _shot_hits(self, target_x, target_y):
        """True if a shot straight ahead would hit a stickman at the target."""
        p = self.player
        screen_x, depth = self.camera.project(p, target_x, target_y)
        if screen_x is None:
            return False
        if abs(screen_x - self.camera.width / 2) > (self.camera.height / depth) * STICK_HALF_WIDTH:
            return False
        wall = cast_ray(self.grid, p.x, p.y, math.cos(p.angle), math.sin(p.angle))[0]
        return depth < wall
