# CLAUDE.md

Guidance for Claude Code when working in this repository.

## Project

`LEDs Play` — a multi-game platform for an LED-matrix display with physical
button controls. It's the successor to a single-game project called
`TetLED`, which only implemented Tetris. Read `STATUS.md` first for the
current state of the migration and what's planned next; it's kept up to date
across sessions and is more current than this file's "target architecture"
description below.

## Target architecture (in progress, not fully built yet)

- Two run modes, selected at launch:
  - **`rpi` mode** — runs on a Raspberry Pi against real hardware: a WS281x
    LED matrix and physical GPIO buttons.
  - **`simulator` mode** — runs on a regular PC with a graphical stand-in for
    the matrix and keyboard-based stand-in for the buttons, for development
    without hardware.
- A hardware abstraction layer so game code never talks to `RPi.GPIO` or
  `rpi_ws281x` directly — it talks to an interface that has an `rpi`
  implementation and a `simulator` implementation.
- A game abstraction so `main.py` can run any game (Tetris, Snake, Pong, ...)
  through a common contract, rather than being hardwired to Tetris like it
  is today.
- Hardware is meant to grow over time (more LEDs/pixels, more buttons), so
  layout/pin/key-count details should live in config, not scattered literal
  constants.

## Current code (inherited from TetLED, pre-refactor)

- `main.py` — game loop, currently hardwired to the Tetris `Board`/`Drawer`.
- `game/game_board.py` — Tetris rules/state (`Board`, `Block`).
- `game/drawer.py` — draws the Tetris board onto the LED matrix; Tetris- and
  hardware-specific layout constants live here (`BOARD_POS_0`, `MATRIX_DPIN`,
  etc.).
- `hardware/leds.py` — `DualMatrix`/`Canvas`: driver for two 8x32 WS281x
  panels wired together as one matrix, plus HSV->RGB conversion. Imports
  `rpi_ws281x` at module scope (RPi-only).
- `hardware/keys.py` — `KeyHandler`: 4 fixed GPIO buttons (up/down/left/right)
  via edge-detect callbacks. Imports `RPi.GPIO` at module scope (RPi-only).
- `hardware/score.py` — optional serial link to an external ESP32 score
  display (`/dev/ttyUSB0`).
- `common/common.py` — shared `Position`/`HsvColor`/`RgbColor` types and
  `BOARD_DIMS`.
- `tests/` — **not automated pytest**. These are manual/interactive checks
  meant to be run on the Pi with real hardware attached: they light up the
  matrix or wait on real key presses and pause on `input()`. Don't treat a
  clean run of these as CI-style verification, and don't try to run them
  without a Pi.

When touching this inherited code, keep in mind it will be refactored behind
the abstractions above — don't deepen the RPi/Tetris coupling unless that's
specifically the task at hand (e.g. "port Tetris to the new game interface").

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
