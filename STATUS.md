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
  - `hardware/leds.py` — `DualMatrix`/`Canvas` driver for two 8x32 WS281x
    panels wired as one 16x32 matrix (`rpi_ws281x`).
  - `hardware/keys.py` — 4-button GPIO input (`RPi.GPIO`), up/down/left/right.
  - `hardware/score.py` — optional serial link to an external ESP32 score
    display.
  - `common/common.py` — shared position/color types, `BOARD_DIMS`.
  - `main.py` — Tetris game loop wiring the pieces above together.
  - Manual/interactive hardware tests in `tests/` (`test_canvas.py`,
    `test_drawer.py`, `test_keys.py`) — these run against real hardware and
    require a human at the keyboard, they are not automated `pytest`.
- Repo renamed/repurposed to `leds-play`; git repo initialized.
- Project direction agreed with the user: multi-game, dual-mode
  (rpi/simulator), expandable hardware.

## In progress

- Bootstrapping project docs (`STATUS.md`, `CLAUDE.md`, `README.md`) — this
  step.

## Not started yet (planned)

Roughly in the order they'll likely need to happen:

1. **Define the hardware abstraction boundary.** Everything under
   `hardware/` (`leds.py`, `keys.py`) is currently RPi-only and imports
   `RPi.GPIO` / `rpi_ws281x` at module scope, which will crash off-hardware.
   Need an interface (e.g. `Matrix`/`InputDevice` protocol) with two
   implementations: `hardware/rpi/` (current code, adapted) and
   `hardware/simulator/` (new, PC-side graphical stand-in — likely
   `pygame`).
2. **Add a mode switch.** Some way to select `rpi` vs `simulator` at launch
   (CLI flag / env var / config file) that picks which hardware backend to
   construct.
3. **Implement a graphical simulator** for PC development, with a faithful
   representation of the LED matrix and keyboard-based input for buttons.
4. Update `requirements.txt` to separate rpi-only deps (`rpi-ws281x`,
   `lgpio`) from cross-platform deps (simulator, shared).
5. **Extract a game interface.** `game/game_board.py` and `game/drawer.py`
   are Tetris-specific and drawing is coupled directly to the board model.
   Need a common `Game` contract (start/advance_turn/is_game_over/render or
   similar) so `main.py` can run any registered game, plus a game-selection
   entry point (menu, or CLI arg).
6. **Move Tetris into its own game module** (e.g. `games/tetris/`) behind
   that new interface, as the reference implementation.
7. **Expand the hardware config**: more pixels (larger/different matrix
   layout than the fixed dual-8x32), more buttons (beyond the current 4),
   in a way that's driven by config rather than hardcoded constants
   (`BOARD_POS_0`, `MATRIX_DPIN`, etc. in `game/drawer.py` today).
8. **Implement Snake** as the second game, to validate the abstraction
   actually generalizes.
9. **Implement More Games** ...


## Open questions for the user

- Exact new button layout/count and what extra actions they should map to.
- Whether the simulator should be pixel-perfect (emulate individual LEDs) or
  just a faithful game-logic view.
