# Game Template Plan

This is the agreed design for what a "game" is in the multi-game platform:
the shared contract every game (Tetris, Snake, Pong, ...) implements, and
the files/assets each one ships alongside its code.

The `Game` contract, Tetris's migration behind it, the menu, and Snake (the
second game) are all done. Audio is still just a plan (see "Still open").

## Decisions already made

- **Scope for now**: everything below targets `sim` mode (PC) only. Real
  Pi wiring for audio (and any other new hardware this implies) is
  deliberately deferred to a later session/contributor, the same way the
  rpi backend is already behind the sim backend for the banner and 2nd
  D-pad (see `STATUS.md`).
- **Logo format**: a PNG file, decoded and downsampled at load time (not a
  hand-written pixel grid literal).
- **Best-score storage**: one file per game, next to that game's own code
  (not a shared root-level file).
- **Matrix/input ownership**: `main.py` creates the one board `Matrix`,
  banner `Matrix` and `KeyHandler` for the whole process and hands them to
  whichever `Game` is currently active (the menu, or a real game) -
  hardware only gets initialized once, not once per game. This is why
  every `Game` subclass's `__init__` takes `(matrix, banner_matrix=None,
  key_handler=None, score_file=None)` rather than building its own.

## Layout

```
games/
  base.py            # Game ABC + shared best-score file logic
  registry.py         # explicit list of playable games for the menu
  logo.py              # the one place that imports Pillow (PNG -> pixel grid)
  menu/
    __init__.py        # MenuGame(Game) - the game-selection screen
    font.py             # tiny 3x5 bitmap font for the scrolling banner text
    .current_game       # gitignored, created on first run
  tetris/
    __init__.py        # TetrisGame(Game) - reference migration of the original game/
    board.py            # Tetris rules/state (Board, Block)
    drawer.py            # renders the board onto a given Matrix
    logo.png             # pixel art, 10x10, cyan T-tetromino
    assets/               # ** not made yet ** - see "Still open" below
      bgm.wav
      sfx/
        line_clear.wav
        game_over.wav
    .best_score          # gitignored, created on first run
  snake/
    __init__.py        # SnakeGame(Game) - the second game
    board.py            # snake/apple grid logic
    drawer.py            # white border box, green snake, red apple
    logo.png             # pixel art, 10x10, coiled snake + apple
    .best_score          # gitignored, created on first run
```

## `Game` contract (`games/base.py`)

```python
class Game(ABC):
    NAME: str                          # shown in the menu
    LOGO_PATH: str = None              # path to this game's logo.png (None = no logo yet)
    USED_KEYS: frozenset[Key]          # subset of Key this game reads - the menu
                                        # uses this to know ENTER is "exit to menu"
                                        # rather than something the game itself wants
    BGM_PATH: str | None = None
    SFX_PATHS: dict[str, str] = {}     # name -> path, e.g. {"line_clear": ...}

    def __init__(
        self, matrix: Matrix, banner_matrix: Matrix | None = None,
        key_handler: KeyHandler | None = None, score_file: str | None = None,
    ):
        ...  # build whatever canvases this game needs from matrix/banner_matrix;
             # store key_handler only if turn_interval needs is_pressed() (see below)
        super().__init__(score_file)
    # Game.__init__ itself only takes score_file - it doesn't touch
    # matrix/banner_matrix/key_handler, those are purely a subclass
    # constructor convention.
    # _read_best_score/_update_best_score: generalized from the original
    # Tetris-only game/game_board.py (lines 223-236).

    @abstractmethod
    def start(self): ...
    @property
    @abstractmethod
    def score(self) -> int: ...
    @property
    @abstractmethod
    def turn_interval(self) -> float: ...   # seconds between turns; may vary (e.g. Tetris speeding up)
    @abstractmethod
    def advance_turn(self, key: Key): ...
    @abstractmethod
    def is_game_over(self) -> bool: ...
    @abstractmethod
    def render(self): ...                    # draws to canvases the game made from its own matrix/banner_matrix

    def on_game_over_tick(self): ...          # optional animation while waiting after game over; default re-renders
    def on_round_end(self, key_handler) -> bool:  # called once a round ends; default shows a blink-and-wait-for-
        ...                                       # keypress screen, returning True if an arrow key ended it (main.py
                                                   # then restarts this same game) or False for anything else, e.g.
                                                   # ENTER (back to the menu). MenuGame overrides this to return
                                                   # instantly - its return value is never consulted.
```

`games/registry.py` holds an explicit `GAMES: list[type[Game]]` - no
filesystem auto-discovery magic.

## The menu (`games/menu/`)

`MenuGame` is itself a `Game`, so it runs through the exact same
`main.py` loop as anything it lets you pick:

- **Selection**: LEFT/RIGHT cycle `GAMES` cyclically; the choice is written
  to `games/menu/.current_game` (by game `NAME`, not index, so it survives
  `GAMES` being reordered) every time it changes, and read back on startup
  so the menu reopens on whatever was last selected.
- **Launch**: ENTER sets `is_game_over()` true, ending the menu's "round";
  `main.py` then reads `menu.selected_game_cls` and switches to a fresh
  instance of it, built with the same shared `matrix`/`banner_matrix`.
  `MenuGame.on_round_end` is overridden to do nothing, so this transition
  is instant (no blink-and-wait screen the way a real game-over gets one).
- **Exiting a game back to the menu**: `main.py`'s `game_loop` treats ENTER
  as a universal "exit to menu" key for any game that doesn't itself claim
  it via `USED_KEYS` (`if key == Key.ENTER and Key.ENTER not in
  game.USED_KEYS: return`). Tetris doesn't use ENTER, so pressing it
  mid-game drops straight back to the menu.
- **Display**: on the board matrix, the selected game's logo (via
  `games/logo.py`, or a placeholder empty box if it has none yet) is drawn
  centered, flanked by a left/right triangle indicating the D-pad changes
  the selection. On the banner, the selected game's `NAME` scrolls
  left-to-right in the `games/menu/font.py` bitmap font, looping with a
  gap. The score display (from `main.py`'s existing per-tick
  `score_display.send_score(game.score, game.best_score)` call) shows the
  selected game's best score: `MenuGame.best_score` is a property that
  reads it via `games.base.default_score_file`/`read_best_score` (module
  functions, so no game instance is needed) instead of the plain instance
  attribute `Game.__init__` assigns for every other game.

## Restarting after game over

`Game.on_round_end` (see the contract above) returns whether an arrow key
ended its wait screen. `main.py`'s `game_loop` propagates that bool, and
`main()` uses it: True keeps `active` as the same game instance for
another `init_game()`/`start()` (fresh score, `best_score` untouched since
it lives on the instance, not reset by `start()`); False (e.g. ENTER, or
the "any other key" case) switches `active` back to the menu, same as
before. This is generic on the base class, so both Tetris and Snake get
"arrow key on the game-over screen replays instantly" for free, with no
per-game code.

## Starting directly into a game

`main.py --start-game NAME` (e.g. `--start-game Snake`) skips the menu
entirely: `main()` constructs that game directly as the initial `active`
instead of `menu`. `NAME` must exactly match a `Game.NAME` in
`games.registry.GAMES` - argparse's `choices` handles validation/the error
message. Once that first game's round ends and you don't restart it
(anything but an arrow key), control falls through to the menu as usual.

## Logo

`games/logo.py` owns the only `Pillow` import in the codebase, mirroring
the existing convention of confining hardware/format-specific imports
(`RPi.GPIO`, `rpi_ws281x`) to one place. `load_logo(path, size)` decodes a
PNG, nearest-neighbor resizes it to the target display area's pixel
dimensions, and returns an `HsvColor` grid (or `None` if `path` is unset or
missing) - the same shape `Canvas.draw_color_map` already expects, so no
PNG-awareness leaks into drawing code. `Pillow` is in the base
`requirements.txt`/`pyproject.toml` (cross-platform, sim-side only for
now).

Tetris and Snake both have a real `logo.png` (`games/tetris/logo.png`,
`games/snake/logo.png`), pointed at by `TetrisGame.LOGO_PATH`/
`SnakeGame.LOGO_PATH`. A future game without one falls back to the `Game`
default of `LOGO_PATH = None`, which shows the menu's placeholder empty
box. Adding a `logo.png` under that game's own directory and pointing
`LOGO_PATH` at it is enough to replace the placeholder - no other code
changes needed.

## Continuous key-hold state (`KeyHandler.is_pressed`)

`KeyHandler.get_key()` only reports discrete one-shot clicks (a full
press+release since the last call), which is right for movement/menu
commands but wrong for a continuous modifier like Snake's run boost: a
game needs to know a key is down *right now*, for as long as it's held,
not wait for it to be released.

`KeyHandler.is_pressed(key) -> bool` (default `False`) answers that,
backed by a `_held_keys` set both backends update on every press/release
(`hardware/simulator/keys.py`, `hardware/rpi/keys.py`), independent of the
`_last_key_pressed`/`_key_clicked` one-shot click machinery `get_key()`
uses. Since `Game.turn_interval` is a property (no way to pass it the
key_handler per call), a game that needs `is_pressed` stores the
`key_handler` given to its constructor and queries it from there - see
`SnakeGame.turn_interval` for the reference usage.

## Snake (`games/snake/`)

The second game, and the first to actually exercise `key_handler` and
`is_pressed`:

- **Board**: 16x16 grid, arrow keys steer (a 180-degree reversal into your
  own neck is ignored; moving into the cell the tail is vacating this turn
  is legal, same as classic Snake). Eating the apple scores 5 points and
  grows the snake by one cell; hitting a wall or your own body ends the
  round.
- **Drawing**: a full white box (`Canvas.draw_borders()`'s default,
  all-four-sides, unlike Tetris's partial `"ulb"`) around the play area,
  a green snake, a red apple. On game over the snake blinks (flips 180
  degrees around the hue wheel and back, same idea as Tetris's board
  blink) via `Drawer.blink_board()`/`SnakeGame.on_game_over_tick()`.
- **Run boost**: holding `Key.P2_UP` ("W" in `sim`) switches
  `turn_interval` from `NORMAL_TURN_INTERVAL` to the shorter
  `RUN_TURN_INTERVAL` for as long as it's held, via `is_pressed` (see
  above) - not a `USED_KEYS`/`get_key()` command.

## Still open: Audio

New contract in `hardware/interfaces.py`:

```python
class AudioPlayer(ABC):
    def play_bgm(self, path: str, loop: bool = True): ...
    def stop_bgm(self): ...
    def play_sfx(self, path: str): ...
```

- `hardware/simulator/audio.py` - real implementation using `pygame.mixer`
  (cross-platform, handles looped bgm plus overlapping sfx; `winsound` was
  the only stdlib alternative and isn't cross-platform). Would need adding
  to base `requirements.txt`.
- `hardware/rpi/audio.py` - stub that no-ops for now, same pattern
  `create_matrix`/`create_banner_matrix` already use for the rpi/sim
  capability gap. Left for a future session to fill in with real Pi audio
  wiring (speaker/DAC choice, GPIO/I2S specifics - all TBD, out of scope
  here).
- `hardware/factory.py` would get a new `create_audio_player(mode)`.

Not started - no game defines `BGM_PATH`/`SFX_PATHS` yet either.

## Best-score files

Per-game `.best_score`, next to each game's own code, default path
`<game module dir>/.best_score`. `.gitignore` has `**/.best_score` (and,
for the menu's own state, `**/.current_game`) rather than an exact
top-level name, since these files now live inside each game's/the menu's
own directory instead of at the repo root.
