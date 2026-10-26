# Stickman bitmaps for the maze's NPC. '#' = body, '*' = muzzle flash.
# The board is too coarse to shrink the 14-row stickman further away, so
# each pose also has hand-drawn 9-row and 5-row versions (like mipmaps).

_STICK_TOP = [
    "..###..",
    ".#...#.",
    ".#...#.",
    "..###..",
    "...#...",
]
_ARMS_DOWN = [
    ".#####.",
    "#..#..#",
    "#..#..#",
]
_ARMS_AIM = [
    "#######",
    "...#...",
    "...#...",
]
_ARMS_FIRE = [
    "*#####*",
    "...#...",
    "...#...",
]
_TORSO = [
    "...#...",
    "...#...",
]
_LEGS_APART = [
    "..#.#..",
    "..#.#..",
    ".#...#.",
    ".#...#.",
]
_LEGS_TOGETHER = [
    "...#...",
    "..#.#..",
    "..#.#..",
    "..#.#..",
]

_SMALL_TOP = [
    ".###.",
    ".#.#.",
    ".###.",
    "..#..",
]
_SMALL_ARMS_DOWN = [".###.", "#.#.#"]
_SMALL_ARMS_AIM = ["#####", "..#.."]
_SMALL_ARMS_FIRE = ["*###*", "..#.."]
_SMALL_LEGS_APART = ["..#..", ".#.#.", "#...#"]
_SMALL_LEGS_TOGETHER = ["..#..", ".#.#.", ".#.#."]

_TINY_WALK = [".#.", "###", ".#.", ".#.", "#.#"]
_TINY_FIRE = [".#.", "*#*", ".#.", ".#.", "#.#"]

STICK_HEIGHT = 0.8  # standing height as a fraction of wall height
DEAD_HEIGHT = STICK_HEIGHT * 4 / 14
STICK_HALF_WIDTH = 0.1  # half the hittable body width, as a fraction of wall height

# Each pose is a list of (bitmap, height as a fraction of wall height),
# largest first.
POSES = {
    "walk0": [
        (_STICK_TOP + _ARMS_DOWN + _TORSO + _LEGS_APART, STICK_HEIGHT),
        (_SMALL_TOP + _SMALL_ARMS_DOWN + _SMALL_LEGS_APART, STICK_HEIGHT),
        (_TINY_WALK, STICK_HEIGHT),
    ],
    "walk1": [
        (_STICK_TOP + _ARMS_DOWN + _TORSO + _LEGS_TOGETHER, STICK_HEIGHT),
        (_SMALL_TOP + _SMALL_ARMS_DOWN + _SMALL_LEGS_TOGETHER, STICK_HEIGHT),
        (_TINY_WALK, STICK_HEIGHT),
    ],
    "aim": [
        (_STICK_TOP + _ARMS_AIM + _TORSO + _LEGS_APART, STICK_HEIGHT),
        (_SMALL_TOP + _SMALL_ARMS_AIM + _SMALL_LEGS_APART, STICK_HEIGHT),
        (_TINY_WALK, STICK_HEIGHT),
    ],
    "fire": [
        (_STICK_TOP + _ARMS_FIRE + _TORSO + _LEGS_APART, STICK_HEIGHT),
        (_SMALL_TOP + _SMALL_ARMS_FIRE + _SMALL_LEGS_APART, STICK_HEIGHT),
        (_TINY_FIRE, STICK_HEIGHT),
    ],
    "dead": [
        ([".##...........",
          "#..#..#....#..",
          "#..##########.",
          ".##...#....#.."], DEAD_HEIGHT),
        (["##.....",
          "#######"], DEAD_HEIGHT),
    ],
}
