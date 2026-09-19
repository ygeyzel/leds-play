# Game Template Plan

This is the agreed design for what a "game" is in the multi-game platform:
the shared contract every game (Tetris, Snake, Pong, ...) implements, and
the files/assets each one ships alongside its code. It fleshes out
`STATUS.md` roadmap items 1 ("extract a game interface") and 2 ("move
Tetris into its own game module"), plus things not previously tracked
there: launcher/menu display metadata (name + logo) and audio.

The `Game` contract, Tetris's migration behind it, and the menu are done
(see "Done" below). Audio is still just a plan (see "Still open").

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
- **Matrix ownership**: `main.py` creates the one board `Matrix`/banner
  `Matrix` pair for the whole process and hands them to whichever `Game` is
  currently active (the menu, or a real game) - hardware only gets
  initialized once, not once per game. This is why every `Game` subclass's
  `__init__` takes `(matrix, banner_matrix=None, score_file=None)` rather
  than building its own matrices.

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
    logo.png             # ** not made yet ** - pixel art, any image editor
    assets/               # ** not made yet ** - see "Still open" below
      bgm.wav
      sfx/
        line_clear.wav
        game_over.wav
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

    def __init__(self, score_file: str | None = None):
        self._score_file = score_file or self._default_score_file()
        self.best_score = self._read_best_score()
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
    def on_round_end(self, key_handler): ...  # called once a round ends; default shows a blink-and-wait-for-keypress
                                               # screen. MenuGame overrides this to return instantly (no wait screen).
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
  gap.

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

No game has a real `logo.png` yet (`TetrisGame.LOGO_PATH` is still the
`Game` default of `None`), so the menu currently shows a placeholder empty
box for every game. Adding a `logo.png` under a game's own directory and
pointing `LOGO_PATH` at it is enough to replace the placeholder - no other
code changes needed.

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
