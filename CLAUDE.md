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
  is today: **done** — see `STATUS.md` and `GAME_TEMPLATE.md`; the `Game`
  contract exists, Tetris runs behind it, and `games/menu/` is a working
  game-selection menu (itself a `Game`) that `main.py` runs by default.
- Hardware is meant to grow over time (more LEDs/pixels, more buttons), so
  layout/pin/key-count details should live in config, not scattered literal
  constants: **partially done** — the matrix/pin layout constants now live
  in `main.py` (moved out of `games/tetris/drawer.py` since the matrix is
  shared across games) but still aren't configurable beyond the existing
  `--num-of-matrices`/`--size-of-banner` CLI flags.

## Current code

- `main.py` — owns the physical rig: creates the one board `Matrix`/banner
  `Matrix` pair for the whole process (`create_matrices()`) and the
  `rpi`/`sim` mode arg, then runs `games/menu/`'s `MenuGame`, switching to
  whichever game it selects and back again on that game's ENTER/game-over.
- `games/base.py` — the `Game` ABC every game (the menu included)
  implements (`start`/`advance_turn`/`is_game_over`/`render`/`score`/
  `turn_interval`/`on_round_end`), plus shared per-game best-score file
  handling. By convention every subclass's `__init__` takes `(matrix,
  banner_matrix=None, key_handler=None, score_file=None)`. See
  `GAME_TEMPLATE.md` for the full per-game template (name/logo/assets/
  audio) this is part of.
- `games/registry.py` — explicit `GAMES` list of games selectable from the
  menu (`TetrisGame`, `SnakeGame`).
- `games/menu/__init__.py` — `MenuGame(Game)`: the game-selection screen
  (LEFT/RIGHT cycles `GAMES`, ENTER launches); persists the selection to
  `games/menu/.current_game`.
- `games/menu/font.py` — a tiny 3x5 bitmap font used to scroll the selected
  game's name across the banner.
- `games/logo.py` — `load_logo()`: the only place that imports `Pillow`;
  decodes a game's `logo.png` into the pixel grid the menu draws.
- `games/tetris/board.py` — Tetris rules/state (`Board`, `Block`); imports
  the shared `Key` enum from `hardware/interfaces.py`.
- `games/tetris/drawer.py` — draws the Tetris board onto a `Matrix` given
  to it (doesn't create one itself); Tetris-specific layout constants live
  here (`BOARD_POS_0`, etc.).
- `games/tetris/__init__.py` — `TetrisGame(Game)`, gluing `board.py` and
  `drawer.py` together behind the `Game` contract.
- `games/snake/` — the second game, same three-file shape as `tetris/`
  (`board.py`/`drawer.py`/`__init__.py`). Its run boost (hold `Key.P2_UP`,
  "W" in `sim`) is the first thing to use `KeyHandler.is_pressed()` for
  continuous hold state rather than `get_key()`'s one-shot clicks.
- `hardware/interfaces.py` — hardware-agnostic contracts: `Matrix`,
  `KeyHandler` (`get_key`/`flush`/`pump`/`is_pressed`), `ScoreDisplay`
  (ABCs) and the shared `Key` enum.
- `hardware/canvas.py` — `Canvas`: hardware-agnostic drawing surface used by
  both `games/tetris/drawer.py` and `games/menu/`, works against any
  `Matrix` implementation.
- `hardware/factory.py` — `create_matrix`/`create_key_handler`/
  `create_score_display`: pick the `rpi` or `simulator` backend for a given
  mode string, lazily importing rpi-only modules only when needed.
- `hardware/rpi/` — real-hardware backend:
  - `leds.py` — `DualMatrix`: driver for two 8x32 WS281x panels wired
    together as one matrix. Imports `rpi_ws281x` at module scope (RPi-only).
  - `keys.py` — `RpiKeyHandler`: 4 fixed GPIO buttons (up/down/left/right)
    via edge-detect callbacks, tracking both one-shot clicks and a
    `_held_keys` set for `is_pressed()`. Imports `RPi.GPIO` at module scope
    (RPi-only).
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

Real Pi audio hardware and per-game audio assets haven't been built yet
(see `GAME_TEMPLATE.md`'s "Still open" section) — don't assume
`AudioPlayer` or `BGM_PATH`/`SFX_PATHS` do anything yet.

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
- Before committing any Python changes, run `ruff check` on them. If
  `ruff` isn't installed/on `PATH`, ask the user to install it rather than
  installing it yourself or skipping the check.
- Run Python in this repo through `uv run` (e.g. `uv run main.py --mode sim`,
  `uv run tools/logo_editor.py`) so it uses the project `.venv`, which has
  `Pillow`. The system `python3` doesn't.
- If `.venv` ever has to be rebuilt, pin it to a system interpreter:
  `uv sync --python ~/.pyenv/versions/3.13.5/bin/python3
  --python-preference only-system`. A plain `uv sync` pulls in uv's own
  CPython build, whose Tcl/Tk aborts on any tkinter window (`[xcb] Unknown
  sequence number ... Aborting`), which breaks `sim` mode and the logo editor.
