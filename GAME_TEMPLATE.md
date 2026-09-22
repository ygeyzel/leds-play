# Game Template Plan

This is the agreed design for what a "game" is in the multi-game platform:
the shared contract every game (Tetris, Snake, Pong, Flappy Bird, ...)
implements, and the files/assets each one ships alongside its code.

The `Game` contract, Tetris's migration behind it, the menu, Snake (the
second game), Pong (the third, and first 2-player game), Flappy Bird (the
fourth) and audio (see "Audio" below, Tetris is the first game to use it)
are all done.

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
- **Matrix/input/audio ownership**: `main.py` creates the one board
  `Matrix`, banner `Matrix`, `KeyHandler` and `AudioPlayer` for the whole
  process and hands them to whichever `Game` is currently active (the
  menu, or a real game) - hardware only gets initialized once, not once
  per game. This is why every `Game` subclass's `__init__` takes `(matrix,
  banner_matrix=None, key_handler=None, audio_player=None,
  score_file=None)` rather than building its own.

## Layout

```
games/
  base.py            # Game ABC + shared best-score file logic
  registry.py         # explicit list of playable games for the menu
  logo.py              # the one place that imports Pillow (PNG -> pixel grid)
  menu/
    __init__.py        # MenuGame(Game) - the game-selection screen
    font.py             # tiny 5x8 bitmap font for the scrolling banner text
    .current_game       # gitignored, created on first run
  tetris/
    __init__.py        # TetrisGame(Game) - reference migration of the original game/
    board.py            # Tetris rules/state (Board, Block)
    drawer.py            # renders the board onto a given Matrix
    logo.png             # pixel art, 12x12, four colored blocks
    bg_music.mp3         # looped background music - see "Audio" below
    game-over.wav         # played once on game over
    1-line-clear.wav      # played for a 1-3 line clear
    4-lines-clear.wav     # played for a 4-line clear
    .best_score          # gitignored, created on first run
  snake/
    __init__.py        # SnakeGame(Game) - the second game
    board.py            # snake/apple grid logic
    drawer.py            # white border box, green snake, red apple
    logo.png             # pixel art, 12x12, a blocky green "S"
    .best_score          # gitignored, created on first run
  pong/
    __init__.py        # PongGame(Game) - the third game, 2-player
    board.py            # paddle/ball court logic
    drawer.py            # white border box, two cyan paddles, a white ball
    logo.png             # pixel art, 12x12, two paddles and a ball
    # no .best_score - see "Pong" below, nothing is ever saved to disk
  flappy/
    __init__.py        # FlappyGame(Game) - the fourth game
    board.py            # bird physics/pipe scroll-and-collision logic
    drawer.py            # white border box, green pipes, a yellow bird
    logo.png             # pixel art, 12x12, a yellow bird
    .best_score          # gitignored, created on first run
tools/
  logo_editor.py       # standalone tkinter logo.png/logo_small.png painter
  font_editor.py        # standalone tkinter games/menu/font.py glyph painter
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
        key_handler: KeyHandler | None = None, audio_player: AudioPlayer | None = None,
        score_file: str | None = None,
    ):
        ...  # build whatever canvases this game needs from matrix/banner_matrix;
             # store key_handler only if turn_interval needs is_pressed() (see below);
             # store audio_player only if this game defines BGM_PATH/SFX_PATHS
        super().__init__(score_file)
    # Game.__init__ itself only takes score_file - it doesn't touch
    # matrix/banner_matrix/key_handler/audio_player, those are purely a
    # subclass constructor convention.
    # _read_best_score/_update_best_score: generalized from the original
    # Tetris-only game/game_board.py (lines 223-236).

    @abstractmethod
    def start(self): ...
    def stop(self): ...   # optional; called once when leaving this game for something else
                           # (the menu, or a different game) - not on a same-instance restart.
                           # default: no-op. a game with background music stops it here.
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
  centered at `LOGO_SIZE` (12x12), flanked by a left/right triangle
  (`ARROW_SIZE`) indicating the D-pad changes the selection. Above each
  arrow sits a row of `PREVIEW_COUNT` small logos (`SMALL_LOGO_SIZE`,
  6x6) - previous games above the left arrow, next games above the right
  one, the one nearest the big logo flush with its arrow's *outer* edge
  (mirrored between the two sides - `SMALL_LOGO_SIZE` is now wider than
  `ARROW_SIZE`, so anchoring both sides the same naive way would overhang
  past the matrix edge on one of them) and the rest extending outward from
  there. The whole strip updates as LEFT/RIGHT cycle the selection. It's
  the same `logo.png`, just decoded
  at a smaller size via `load_logo`'s `size` argument (no separate asset
  needed, though a hand-authored `logo_small.png` can exist alongside it
  for a game that wants one - see `tools/logo_editor.py` below).
  `MenuGame._load_cached_logo(game_cls, size)` caches by `(game_cls,
  size)` since the big and small logos are separate decodes of the same
  file. Clicking LEFT/RIGHT also blinks that side's arrow once (see
  `ARROW_BLINK_TICKS`), same as before. On the banner, the selected
  game's `NAME` scrolls left-to-right in the `games/menu/font.py` bitmap
  font, with a small copy of its own logo as the separator between
  repeats instead of a blank gap (`BANNER_LOGO_PADDING`). The score
  display (from `main.py`'s existing per-tick
  `score_display.send_score(game.score, game.best_score)` call) shows the
  selected game's best score: `MenuGame.best_score` is a property that
  reads it via `games.base.default_score_file`/`read_best_score` (module
  functions, so no game instance is needed) instead of the plain instance
  attribute `Game.__init__` assigns for every other game.

## Logo editor (`tools/logo_editor.py`)

A standalone tkinter tool (`python3 tools/logo_editor.py`, no new
dependency - Pillow's already required) for authoring `logo.png` by hand
instead of a script: paint the big grid (`LOGO_SIZE`) and, separately, the
small one (`SMALL_LOGO_SIZE`), pick colors from a preset palette or
`tkinter.colorchooser`, and save. "Auto-generate from big logo" (on by
default) keeps the small grid a nearest-neighbor downsample of the big one
- the same thing `load_logo` does at runtime from `logo.png` alone, so
this is what most games should ship. Painting the small canvas directly
turns that off and saves the result as a separate `logo_small.png`
alongside `logo.png` - `MenuGame._load_logo_for_size` prefers that file
over an auto-shrunk `logo.png` when it exists, for a game that wants a
hand-tuned small logo instead. Save targets: an existing
`games.registry.GAMES` entry,
a typed new game name (creates `games/<name>/` even though it isn't a
real registered game yet), or a plain file-save dialog.

## Font editor (`tools/font_editor.py`)

A standalone tkinter tool (`python3 tools/font_editor.py`) for
`games/menu/font.py`'s bitmap font: shows every glyph at once, sim-style
(lit/unlit cells), click one to edit it pixel-by-pixel in a bigger view.
Shows the full expected character set (A-Z, a-z, 0-9, space) even though
`_GLYPHS` normally only has uppercase/digits/space - the app always
`.upper()`s text before rendering, so lowercase has never been needed, but
the editor still offers blank, editable slots for it in case that changes.
"Save to font.py" rewrites just the `_GLYPHS = {...}` block in place via a
regex match on that one block (leaving `FONT_HEIGHT`/`FONT_WIDTH`/
`glyph_shape`/`text_shape` untouched) - and only writes a *blank* glyph if
it was already in the file or genuinely edited this session, so opening
the tool and saving without touching lowercase doesn't flood the file with
36 empty entries.

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
(`platforms/simulator/keys.py`, `platforms/rpi/keys.py`), independent of the
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

## Pong (`games/pong/`)

The third game, and the first with two players sharing one round instead
of a single-player high score:

- **Board**: a 24x34 court, left paddle on `Key.P2_UP`/`Key.P2_DOWN`
  ("W"/"S" in `sim`), right paddle on `Key.UP`/`Key.DOWN` (arrow keys).
  Both paddles are read every turn via `is_pressed` (see above) rather
  than `get_key()`, so `advance_turn`'s `key` argument goes unused and
  both players can move within the same turn. The ball moves diagonally
  one cell a turn, bounces off the top/bottom walls and off a paddle it
  reaches while that paddle's 5-cell span covers its row; reaching either
  edge without a paddle there scores the other side a point and re-serves
  the ball from the center in a random diagonal direction. First to
  `POINTS_TO_WIN` (7) ends the round.
- **Drawing**: the same full white border box as Snake, two cyan paddles
  flush against the inside of the left/right border, a white ball. On game
  over both paddles blink (flip 180 degrees around the hue wheel), same
  idea as Tetris/Snake's board blink.
- **No persisted best score**: a 2-player live match has no single-player
  high score to save, so `PongGame` overrides `best_score` as a read-only
  property returning the right paddle's live score instead of the usual
  file-backed value (same no-op-setter trick `MenuGame.best_score` uses) -
  `_update_best_score()` is simply never called, so no `.best_score` file
  is ever written. `main.py`'s existing `send_score(game.score,
  game.best_score)` call then shows the left paddle's score on the bottom
  7-segment row and the right paddle's on the top row, live, with no
  changes needed to `main.py` or the `Game` base class.

## Flappy Bird (`games/flappy/`)

The fourth game, and the first single-key one - `USED_KEYS = {Key.UP}`:

- **Board**: a 20x34 court. `Key.UP` sets the bird's vertical velocity
  upward instantly (not additive - a responsive, classic-feel flap, same
  idea as the original), and gravity accelerates it back down every turn
  otherwise, capped at a max fall speed. Pipes (a `deque` of fixed-width
  columns with a randomly-positioned gap) scroll one cell left per turn;
  the oldest is dropped once fully off-screen and a new one spawns at a
  fixed spacing. Touching a pipe (bird's row outside that column's gap),
  the ceiling, or the ground ends the round; passing a pipe's trailing
  edge scores a point.
- **Drawing**: the same full white border box as Snake/Pong, green pipe
  columns (skipping their gap rows), a yellow bird. On game over the bird
  blinks (flips 180 degrees around the hue wheel), same idea as the other
  games' board blink.
- **Best score**: unlike Pong, this is an ordinary single-player game, so
  it uses `Game`'s default file-backed `best_score`/`_update_best_score()`
  behavior unchanged - no override needed.

## Audio (`platforms/interfaces.py`'s `AudioPlayer`)

```python
class AudioPlayer(ABC):
    def play_bgm(self, path: str, loop: bool = True): ...
    def stop_bgm(self): ...
    def play_sfx(self, path: str): ...
    def set_muted(self, muted: bool): ...
```

- `platforms/simulator/audio.py` - `SimulatorAudioPlayer`, backed by
  `pygame.mixer` (cross-platform, handles looped bgm plus overlapping sfx
  on separate channels so one never interrupts the other; `winsound` was
  the only stdlib alternative and isn't cross-platform). `pygame` is a
  base dependency now (sim-side only, same as Pillow). Muting stops the
  bgm outright and remembers the last `play_bgm()` call to resume from the
  start on unmute; sfx just skip playing while muted.
- `platforms/rpi/audio.py` - `RpiAudioPlayer`, a no-op stub, same pattern
  `create_matrix`/`create_banner_matrix` already use for the rpi/sim
  capability gap. Left for a future session to fill in with real Pi audio
  wiring (speaker/DAC choice, GPIO/I2S specifics - all TBD, out of scope
  here).
- `platforms/factory.py`'s `create_audio_player(mode)` picks between them.
- `Game` (`games/base.py`) gained a `stop()` hook (default no-op), called
  once when a game is left for something else (the menu, or a different
  game) - not on a same-instance restart, where `start()` runs again
  instead. A game with background music stops it here.
- `main.py` creates the one `AudioPlayer` for the whole process (alongside
  the matrix/key handler/score display) and threads it into every game's
  constructor as `audio_player=`, following the existing shared-resource
  convention (unused by a game with no sound assets, accepted for the
  convention same as an unused `key_handler`). `_sleep` syncs `Key.MUTE`'s
  toggle state to `audio_player.set_muted()` on every pump, same cadence
  as the existing `Key.PAUSE` check.
- **Tetris** (`games/tetris/`) is the first game to use it:
  `BGM_PATH`/`SFX_PATHS` point at `bg_music.mp3`/`game-over.wav`/
  `1-line-clear.wav`/`4-lines-clear.wav`. `start()` starts the bgm loop,
  the new `stop()` override stops it. `Board` gained an `on_lines_cleared`
  callback (same pattern as its existing `burn_animation` hook), fired
  once per turn (after the row-clearing loop, not once per row) with the
  total line count - `TetrisGame` plays the 4-line sfx for a 4-line clear
  or the 1-line sfx for 1-3, exactly once either way (the 1-line sound
  never repeats for a 4-line clear). `on_round_end` (game over) stops the
  bgm, plays the game-over sfx, then immediately restarts the bgm loop so
  it resumes under the game-over blink screen. Snake/Pong/Flappy Bird
  don't define `BGM_PATH`/`SFX_PATHS` yet.

## Best-score files

Per-game `.best_score`, next to each game's own code, default path
`<game module dir>/.best_score`. `.gitignore` has `**/.best_score` (and,
for the menu's own state, `**/.current_game`) rather than an exact
top-level name, since these files now live inside each game's/the menu's
own directory instead of at the repo root.
