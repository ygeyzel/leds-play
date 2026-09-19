# Project Status

## What this project is

`LEDs Play` is the successor to `TetLED` (a single-game Tetris-on-LED-matrix
project for Raspberry Pi). The goal is to generalize it into a multi-game
platform (Tetris, Snake, Pong, ...) that can run either on real hardware
(`rpi` mode) or on a PC with a graphical simulator (`simulator` mode), and to
support a bigger/more flexible hardware setup (more pixels, more buttons).

See `CLAUDE.md` for architecture/contributor notes, `README.md` for
user-facing setup instructions, and `GAME_TEMPLATE.md` for the agreed
design of the per-game contract/template (`Game` ABC, Tetris's migration
behind it, the menu, and PNG logo loading are all done; audio is still
just a plan).

## Completed

- Imported the working `TetLED` codebase as the starting point:
  - `game/game_board.py` — Tetris board/piece logic (later moved to
    `games/tetris/board.py`, see below).
  - `game/drawer.py` — renders the Tetris board to the LED matrix (later
    moved to `games/tetris/drawer.py`, see below).
  - `common/common.py` — shared position/color types, `BOARD_DIMS`.
  - `main.py` — Tetris game loop wiring the pieces above together.
  - Manual/interactive hardware tests in `tests/` (`test_canvas.py`,
    `test_drawer.py`, `test_keys.py`) — these run against real hardware and
    require a human at the keyboard, they are not automated `pytest`.
- Repo renamed/repurposed to `leds-play`; git repo initialized.
- Project direction agreed with the user: multi-game, dual-mode
  (rpi/simulator), expandable hardware.
- **Hardware abstraction boundary defined**: `hardware/interfaces.py` holds
  the `Matrix` / `KeyHandler` / `ScoreDisplay` ABCs and the shared `Key`
  enum; `hardware/canvas.py` holds the hardware-agnostic `Canvas` drawing
  surface (moved out of the old `hardware/leds.py`, unchanged otherwise).
  Game code (now `games/tetris/`, see below) only imports from
  `hardware.interfaces`/`hardware.factory`, never `RPi.GPIO`/`rpi_ws281x`
  directly.
- **`rpi` backend** (`hardware/rpi/`): `leds.py` (`DualMatrix`), `keys.py`
  (`RpiKeyHandler`), `score.py` (`SerialScoreDisplay`) — adapted from the
  original inherited modules (which are now removed from `hardware/`'s top
  level) to implement the new interfaces; behavior unchanged.
- **`simulator` backend** (`hardware/simulator/`), built with tkinter:
  - `leds.py` (`SimulatorMatrix`) — pixel-for-pixel stand-in for the real
    16x32 dual matrix, same `dimensions`/`__setitem__` contract as the rpi
    `DualMatrix`.
  - `keys.py` (`SimulatorKeyHandler`) — keyboard arrow keys mapped to
    up/down/left/right, with an on-screen D-pad that highlights whichever
    key is currently pressed.
  - `score.py` (`SimulatorScoreDisplay`) + `seven_segment.py` — score
    (bottom) and high score (top) drawn as 7-segment-style digits to the
    right of the matrix, no text.
  - `window.py` — the single shared `Tk` window/canvas the three backends
    above draw into.
- **Mode switch**: `python main.py [rpi|sim]` (defaults to `rpi`), wired via
  `hardware/factory.py` (`create_matrix`/`create_key_handler`/
  `create_score_display`) which lazily imports the rpi-only modules only
  when `mode == "rpi"`, so `sim` mode and `tests/` never touch
  `RPi.GPIO`/`rpi_ws281x`/`pyserial`.
- Split `requirements.txt` (base/cross-platform — currently just stdlib
  tkinter, nothing to install) from `requirements-rpi.txt` (`rpi-ws281x`,
  `lgpio`, `pyserial`).
- Verified manually: ran `python main.py sim` end-to-end (matrix rendering,
  score digits updating, board logic) and a focused key-press test
  confirming the D-pad highlight and `get_key()` both react correctly to a
  simulated arrow-key press/release.
- Added `pyproject.toml`/`uv.lock` for `uv` support (`uv sync` /
  `uv sync --extra rpi` / `uv run`), alongside the existing pip
  `requirements*.txt` files.
- **`sim`-mode hardware expansion** (roadmap item 3 below, sim side only):
  - Board matrix panel count is now a CLI flag, `--num-of-matrices`
    (default 5, was hardcoded to 2) — `hardware/factory.py`'s
    `create_matrix`/`hardware/simulator/leds.py`'s `SimulatorMatrix` take
    `num_of_matrices` instead of assuming 2.
  - New banner area: a second, independent matrix drawn above the board
    matrix in the simulator window, sized via `--size-of-banner` (default
    2, panels are 8 rows x 32 cols each). `hardware/factory.py`'s new
    `create_banner_matrix()`; `Drawer` now holds `self._banner_matrix`
    alongside `self._matrix`, but nothing draws game content into it yet.
  - New buttons: a 2nd D-pad (`Key.P2_UP/DOWN/LEFT/RIGHT`, `WASD` in sim)
    and a `Key.ENTER` button (`Return` in sim), for a future 2nd
    player/game and menu navigation respectively. Tetris doesn't use them
    (`Board.advance_turn` now ignores keys it doesn't recognize instead of
    raising `KeyError`, so pressing them during a game is a harmless no-op).
  - `hardware/rpi/*` deliberately untouched (still hardcoded to 2 panels,
    4 buttons, no banner) — the rpi backend is now out of sync with the
    sim backend's capabilities; `create_matrix`/`create_banner_matrix`
    print a warning and fall back to the old rpi behavior (or `None` for
    the banner) if run with non-default flags in `rpi` mode, rather than
    crashing.
- **Game interface extracted + Tetris migrated behind it** (roadmap items 1
  and 2 below, design in `GAME_TEMPLATE.md`):
  - `games/base.py` — the `Game` ABC (`start`/`advance_turn`/
    `is_game_over`/`render`/`score`/`turn_interval`, plus a default
    `on_game_over_tick` and shared per-game best-score file read/write).
  - `games/tetris/` — Tetris moved out of the old `game/` package:
    `board.py` (was `game/game_board.py`, best-score logic removed — now
    handled generically by `Game`), `drawer.py` (was `game/drawer.py`,
    unchanged otherwise), `__init__.py` (`TetrisGame(Game)`, gluing board +
    drawer together and implementing the contract). Best score now persists
    to `games/tetris/.best_score` instead of a root-level file;
    `.gitignore`'s `.best_score` entry became `**/.best_score` accordingly.
  - `games/registry.py` — explicit `GAMES` list (just `TetrisGame` so far);
    `main.py` runs `GAMES[0]` directly since the actual game-selection
    launcher (menu/CLI picker) is still future work, see item 1 below.
  - Not part of this migration: the logo/audio pieces of `GAME_TEMPLATE.md`
    (`LOGO_PATH` is `None` on every game for now) and the launcher UI
    itself — both done in the next entry below.
- **Game-selection menu built** (`games/menu/`, design in
  `GAME_TEMPLATE.md`): `MenuGame` is itself a `Game`, so `main.py`'s loop
  alternates between it and whichever real game is selected, transitioning
  on `is_game_over()` either way:
  - LEFT/RIGHT cycle `games.registry.GAMES` cyclically; the selection is
    persisted (by game `NAME`) to `games/menu/.current_game` and restored
    on startup.
  - ENTER launches the selected game. `main.py`'s `game_loop` also treats
    ENTER as a universal "exit to menu" key for any game that doesn't claim
    it itself via `USED_KEYS` - Tetris doesn't, so ENTER mid-game drops
    straight back to the menu (no game-over screen; see `Game.on_round_end`,
    which the menu overrides to skip its own wait screen when launching).
  - Matrix creation moved out of each game and into `main.py`
    (`create_matrices()`, using the hardware-wiring constants formerly in
    `games/tetris/drawer.py`) so the one real `Matrix`/banner `Matrix` pair
    is shared between the menu and every game instead of being rebuilt
    (and, on real hardware, re-initialized) each time. Every `Game`
    subclass's `__init__` now takes `(matrix, banner_matrix=None,
    score_file=None)` by convention.
  - `games/logo.py` added: decodes a game's `logo.png` (Pillow, now a base
    dependency) into the pixel grid the menu draws centered on the board
    matrix, flanked by left/right arrows; falls back to a placeholder empty
    box when a game has no logo yet (true for every game today).
  - `games/menu/font.py` added: a small 3x5 bitmap font, used to scroll the
    selected game's name across the banner.
  - Verified manually in `sim` mode: menu renders (scrolling name + logo
    placeholder + arrows), ENTER launches Tetris on the shared matrix,
    ENTER mid-game returns to the menu instantly.
- **Fixed a dropped-keypress race in both `KeyHandler` backends**: `get_key()`
  called `flush()`, which reset `_last_key_pressed` (not just the one-shot
  `_key_clicked`) on every call. A press seen but not yet released could
  get wiped by an intervening `get_key()` before its release ever arrived,
  silently dropping the click. Latent before (Tetris's slowest poll rate,
  1s at level 1, easily outlasted a real button press) but broke reliably
  once the menu started polling every 0.07s for smooth scrolling - found
  via a real "ENTER doesn't start the game" report, reproduced with
  synthetic X key events. `get_key()` now only clears `_key_clicked`;
  `flush()` (called at round boundaries) still resets both.

## In progress

Nothing active right now — see "Not started yet" for what's next.

## Not started yet (planned)

Roughly in the order they'll likely need to happen:

1. **Audio**: the `AudioPlayer` contract, `pygame.mixer`-based sim backend,
   and rpi no-op stub from `GAME_TEMPLATE.md` haven't been built, and no
   game defines `BGM_PATH`/`SFX_PATHS` yet.
2. **Real logo art**: every game still shows the menu's placeholder box;
   authoring an actual `logo.png` per game (starting with Tetris) is just
   content, no code changes needed once one exists (see `GAME_TEMPLATE.md`).
3. **Expand the hardware config**: **partially done, sim side only** (see
   "Completed" above) — `--num-of-matrices`/`--size-of-banner` CLI flags
   and the 2nd D-pad + `Key.ENTER` are live in `sim` mode. Still needed:
   - `hardware/rpi/*` doesn't support any of this yet (still fixed at 2
     panels / 4 buttons / no banner) — needs real panel-count wiring math
     generalized in `DualMatrix`, GPIO pins picked for the 5 new buttons
     and a banner strip, and a rpi banner-matrix implementation.
   - `BOARD_POS_0` etc. in `games/tetris/drawer.py` are still hardcoded
     Tetris layout constants (unaffected by the bigger matrix — Tetris just
     gets extra unused columns to the right for now).
   - Tetris itself still doesn't render anything into the banner (the menu
     does; Tetris just leaves it blank while playing) or react to the 2nd
     D-pad.
4. **Implement Snake** as the second game, to validate the `Game`
   abstraction actually generalizes.
5. **Implement More Games** ...

## Open questions for the user

- Real GPIO pin numbers for the 5 new buttons and the banner strip, and
  whatever panel-count/wiring specifics the rpi backend needs once it's
  brought up to parity with the sim backend (see roadmap item 3).
