# Project Status

## What this project is

`LEDs Play` is the successor to `TetLED` (a single-game Tetris-on-LED-matrix
project for Raspberry Pi). The goal is to generalize it into a multi-game
platform (Tetris, Snake, Pong, ...) that can run either on real hardware
(`rpi` mode) or on a PC with a graphical simulator (`simulator` mode), and to
support a bigger/more flexible hardware setup (more pixels, more buttons).

See `CLAUDE.md` for architecture/contributor notes and `README.md` for
user-facing setup instructions.

## Completed

- Imported the working `TetLED` codebase as the starting point:
  - `game/game_board.py` — Tetris board/piece logic.
  - `game/drawer.py` — renders the Tetris board to the LED matrix.
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
  Game code (`game/drawer.py`, `game/game_board.py`) only imports from
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

## In progress

Nothing active right now — see "Not started yet" for what's next.

## Not started yet (planned)

Roughly in the order they'll likely need to happen:

1. **Extract a game interface.** `game/game_board.py` and `game/drawer.py`
   are Tetris-specific and drawing is coupled directly to the board model.
   Need a common `Game` contract (start/advance_turn/is_game_over/render or
   similar) so `main.py` can run any registered game, plus a game-selection
   entry point (menu, or CLI arg).
2. **Move Tetris into its own game module** (e.g. `games/tetris/`) behind
   that new interface, as the reference implementation.
3. **Expand the hardware config**: **partially done, sim side only** (see
   "Completed" above) — `--num-of-matrices`/`--size-of-banner` CLI flags
   and the 2nd D-pad + `Key.ENTER` are live in `sim` mode. Still needed:
   - `hardware/rpi/*` doesn't support any of this yet (still fixed at 2
     panels / 4 buttons / no banner) — needs real panel-count wiring math
     generalized in `DualMatrix`, GPIO pins picked for the 5 new buttons
     and a banner strip, and a rpi banner-matrix implementation.
   - `BOARD_POS_0` etc. in `game/drawer.py` are still hardcoded Tetris
     layout constants (unaffected by the bigger matrix — Tetris just gets
     extra unused columns to the right for now).
   - Nothing renders into the banner yet — that's step 4 below (games
     need to be updated to actually use the bigger board/banner/buttons).
4. **Update the games to use the expanded hardware** — Tetris doesn't
   render into the banner or react to the 2nd D-pad/`Key.ENTER` yet.
5. **Implement Snake** as the second game, to validate the abstraction
   actually generalizes.
6. **Implement More Games** ...

## Open questions for the user

- Real GPIO pin numbers for the 5 new buttons and the banner strip, and
  whatever panel-count/wiring specifics the rpi backend needs once it's
  brought up to parity with the sim backend (see roadmap item 3).
