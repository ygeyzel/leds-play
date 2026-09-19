# Game Template Plan

This is the agreed design for what a "game" is in the multi-game platform:
the shared contract every game (Tetris, Snake, Pong, ...) implements, and
the files/assets each one ships alongside its code. It fleshes out
`STATUS.md` roadmap items 1 ("extract a game interface") and 2 ("move
Tetris into its own game module"), plus two things not previously tracked
there: launcher display metadata (name + logo) and audio.

Not started yet — this is the plan to build against, not current state.

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

## Layout

```
games/
  base.py            # new: Game ABC + shared best-score file logic
  registry.py         # new: explicit list of playable games for the launcher
  logo.py              # new: the one place that imports Pillow (PNG -> pixel grid)
  tetris/
    __init__.py        # TetrisGame(Game) - reference migration of today's game/
    board.py            # today's game/game_board.py, moved as-is
    drawer.py            # today's game/drawer.py, moved as-is
    logo.png             # pixel art, authored in any image editor
    assets/
      bgm.wav
      sfx/
        line_clear.wav
        game_over.wav
    .best_score          # gitignored, created on first run
```

## `Game` contract (`games/base.py`)

```python
class Game(ABC):
    NAME: str                          # shown in the launcher
    LOGO_PATH: str                     # path to this game's logo.png
    USED_KEYS: frozenset[Key]          # subset of Key this game reads - lets
                                        # the launcher/menu know what's live
    BGM_PATH: str | None = None
    SFX_PATHS: dict[str, str] = {}     # name -> path, e.g. {"line_clear": ...}

    def __init__(self, score_file: str | None = None):
        self.best_score = self._read_best_score(score_file or self._default_score_file())
    # _read_best_score/_update_best_score lifted from today's
    # game/game_board.py (lines 223-236), generalized instead of Tetris-only.

    @abstractmethod
    def start(self): ...
    @abstractmethod
    def advance_turn(self, key: Key): ...
    @abstractmethod
    def is_game_over(self) -> bool: ...
    @abstractmethod
    def render(self, canvas: Canvas, banner_canvas: Canvas | None): ...
    @property
    @abstractmethod
    def score(self) -> int: ...
```

`games/registry.py` holds an explicit `GAMES: list[type[Game]]` - no
filesystem auto-discovery magic. The launcher/menu itself (how `GAMES` gets
turned into a picker on screen) is a separate piece of design, still open.

## Logo

`games/logo.py` owns the only `Pillow` import in the codebase, mirroring
the existing convention of confining hardware/format-specific imports
(`RPi.GPIO`, `rpi_ws281x`) to one place. It decodes each game's `logo.png`,
nearest-neighbor resizes it to the target display area's pixel dimensions,
and returns an `HsvColor` grid - the same shape `Canvas` already expects, so
no PNG-awareness leaks into drawing code. Requires adding `Pillow` to the
base `requirements.txt`/`pyproject.toml` (cross-platform, sim-side only for
now).

## Audio

New contract in `hardware/interfaces.py`:

```python
class AudioPlayer(ABC):
    def play_bgm(self, path: str, loop: bool = True): ...
    def stop_bgm(self): ...
    def play_sfx(self, path: str): ...
```

- `hardware/simulator/audio.py` - real implementation using `pygame.mixer`
  (cross-platform, handles looped bgm plus overlapping sfx; `winsound` was
  the only stdlib alternative and isn't cross-platform). Added to base
  `requirements.txt`.
- `hardware/rpi/audio.py` - stub that no-ops for now, same pattern
  `create_matrix`/`create_banner_matrix` already use for the rpi/sim
  capability gap. Left for a future session to fill in with real Pi audio
  wiring (speaker/DAC choice, GPIO/I2S specifics - all TBD, out of scope
  here).
- `hardware/factory.py` gets a new `create_audio_player(mode)`.

## Best-score files

Per-game `.best_score`, next to each game's own code, default path
`<game module dir>/.best_score`. Note: today's root-level `.best_score` is
gitignored by exact name (`.best_score` in `.gitignore`); moving to
per-game files needs that changed to a pattern (e.g. `**/.best_score`) -
call this out explicitly so it isn't missed during the migration.

## Suggested build order

1. `Game` base class (`games/base.py`) + `games/registry.py`.
2. Migrate Tetris into `games/tetris/` behind `Game`, as the reference
   implementation - proves the contract actually fits before Snake/Pong are
   attempted.
3. Audio contract + `hardware/simulator/audio.py` backend + rpi stub.
4. Logo loader (`games/logo.py`) + `Pillow` dependency.

Steps 3 and 4 don't depend on each other and could be done in either order,
or in parallel with step 2 once the `Game` shape from step 1 is settled.
