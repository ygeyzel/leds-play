# CLAUDE.md

Guidance for Claude Code when working in this repository.

## Project

`LEDs Play` — a multi-game platform for an LED-matrix display with physical
button controls. It's the successor to a single-game project called
`TetLED`, which only implemented Tetris. Read `STATUS.md` first for the
current state of the migration and what's planned next; it's kept up to date
across sessions and is more current than this file's "target architecture"
description below.

## Target architecture

- Two run modes, selected via a CLI arg to `main.py` (`rpi` default, `sim`):
  **done**.
  - **`rpi` mode** — runs on a Raspberry Pi against real hardware: a WS281x
    LED matrix and physical GPIO buttons.
  - **`sim` mode** — runs on a regular PC with a tkinter window standing in
    for the matrix (pixel-for-pixel) and keyboard arrow keys standing in for
    the buttons, for development without hardware.
- A hardware abstraction layer so game code never talks to `RPi.GPIO` or
  `rpi_ws281x` directly: **done**, see `hardware/interfaces.py` (the
  `Matrix`/`KeyHandler`/`ScoreDisplay` contracts) with an `hardware/rpi/`
  implementation and an `hardware/simulator/` implementation, picked by
  `hardware/factory.py`.
- A game abstraction so `main.py` can run any game (Tetris, Snake, Pong, ...)
  through a common contract, rather than being hardwired to Tetris like it
  is today: **partially done** — see `STATUS.md` and `GAME_TEMPLATE.md`; the
  `Game` contract exists and Tetris runs behind it, but there's still no
  game-selection launcher (`main.py` just runs the first registered game).
- Hardware is meant to grow over time (more LEDs/pixels, more buttons), so
  layout/pin/key-count details should live in config, not scattered literal
  constants: **partially done** — the matrix/pin layout constants still live
  in `games/tetris/drawer.py` and haven't been made configurable yet.

## Current code

- `main.py` — game loop; runs the first game in `games/registry.py`'s
  `GAMES` list (just Tetris so far), parameterized by an `rpi`/`sim` mode
  arg. No game-selection launcher yet.
- `games/base.py` — the `Game` ABC every game implements
  (`start`/`advance_turn`/`is_game_over`/`render`/`score`/`turn_interval`),
  plus shared per-game best-score file handling. See `GAME_TEMPLATE.md` for
  the full per-game template (name/logo/assets/audio) this is part of.
- `games/registry.py` — explicit `GAMES` list of playable games.
- `games/tetris/board.py` — Tetris rules/state (`Board`, `Block`); imports
  the shared `Key` enum from `hardware/interfaces.py`.
- `games/tetris/drawer.py` — draws the Tetris board onto a `Matrix`; Tetris-
  and hardware-specific layout constants live here (`BOARD_POS_0`,
  `MATRIX_DPIN`, etc.). Builds its matrix via
  `hardware.factory.create_matrix(mode, ...)`.
- `games/tetris/__init__.py` — `TetrisGame(Game)`, gluing `board.py` and
  `drawer.py` together behind the `Game` contract.
- `hardware/interfaces.py` — hardware-agnostic contracts: `Matrix`,
  `KeyHandler`, `ScoreDisplay` (ABCs) and the shared `Key` enum.
- `hardware/canvas.py` — `Canvas`: hardware-agnostic drawing surface used by
  `games/tetris/drawer.py`, works against any `Matrix` implementation.
- `hardware/factory.py` — `create_matrix`/`create_key_handler`/
  `create_score_display`: pick the `rpi` or `simulator` backend for a given
  mode string, lazily importing rpi-only modules only when needed.
- `hardware/rpi/` — real-hardware backend:
  - `leds.py` — `DualMatrix`: driver for two 8x32 WS281x panels wired
    together as one matrix. Imports `rpi_ws281x` at module scope (RPi-only).
  - `keys.py` — `RpiKeyHandler`: 4 fixed GPIO buttons (up/down/left/right)
    via edge-detect callbacks. Imports `RPi.GPIO` at module scope (RPi-only).
  - `score.py` — `SerialScoreDisplay`: optional serial link to an external
    ESP32 score display (`/dev/ttyUSB0`). Imports `pyserial`.
- `hardware/simulator/` — tkinter-based backend, no extra deps beyond the
  standard library:
  - `window.py` — `SimulatorWindow`/`get_window()`: the single shared `Tk`
    root/canvas the matrix, keys and score backends below draw into.
  - `leds.py` — `SimulatorMatrix`: pixel-for-pixel stand-in for `DualMatrix`.
  - `keys.py` — `SimulatorKeyHandler`: arrow keys -> `Key`, plus an on-screen
    D-pad that highlights the currently-pressed key.
  - `score.py` + `seven_segment.py` — `SimulatorScoreDisplay`: score/high
    score as 7-segment-style digits to the right of the matrix.
- `common/common.py` — shared `Position`/`HsvColor`/`RgbColor` types,
  `BOARD_DIMS`, `hsv_to_rgb`, `is_position_out_of_range`.
- `tests/` — **not automated pytest**. These are manual/interactive checks
  meant to be run on the Pi with real hardware attached: they light up the
  matrix or wait on real key presses and pause on `input()`. Don't treat a
  clean run of these as CI-style verification, and don't try to run them
  without a Pi.

The game-selection launcher (multi-game `main.py`) hasn't been built yet —
don't deepen the single-game (`GAMES[0]`) coupling in `main.py` unless
that's specifically the task at hand.

## Conventions

- Positions are `(row, col)`-style tuples via the `Position` type in
  `common/common.py`; colors are HSV tuples (`HsvColor`) at the game/drawer
  level and converted to RGB only at the LED driver boundary.
- Keep hardware-specific imports (`RPi.GPIO`, `rpi_ws281x`) confined to the
  `rpi` hardware backend so `simulator` mode and tests can run on a plain PC
  without them installed.

## Workflow notes

- Update `STATUS.md` when completing or starting a phase of the migration
  described there, so the next session picks up context correctly.
