# LEDs Play

A small game platform for an LED-matrix display with physical button
controls, built to run on a Raspberry Pi — with a PC-based simulator mode
for developing and testing games without the hardware.

This project is the successor to [`TetLED`](https://github.com/ygeyzel/tetled), a Tetris-only version of the
same idea. `LEDs Play` generalizes it to support multiple games (Tetris,
Snake, Pong, ...) and is moving towards a bigger/more flexible hardware setup
(more pixels, more buttons).

> **Status:** actively being migrated from the original single-game TetLED
> codebase. See [`STATUS.md`](STATUS.md) for what's done and what's planned.
> The game itself is still Tetris-only (the multi-game abstraction hasn't
> landed yet), but it now runs in both `rpi` and `sim` mode.

## Modes

Selected with a CLI arg to `main.py` (`rpi` is the default):

- **`rpi` mode** — runs on a Raspberry Pi driving a real WS281x LED matrix
  and physical GPIO buttons.
- **`sim` mode** — runs on a regular PC with a tkinter window standing in
  for the LED matrix (pixel-for-pixel) and the keyboard arrow keys standing
  in for the buttons, so games can be developed and tested without any
  hardware. It also shows score/high score as 7-segment-style digits and
  highlights button presses on screen.

```bash
python main.py sim
```

## Hardware (current)

- Two 8x32 WS281x LED panels wired together as one 16x32 matrix.
- 4 buttons (up, down, left, right) wired to GPIO pins.
- Optional: an external serial (ESP32) score display.

This is expected to grow (more LEDs, more buttons) as new games need more
display area or more input actions than Tetris did.

## Requirements

- Python 3.
- `sim` mode only needs the standard library (tkinter).
- `rpi` mode additionally needs `requirements-rpi.txt` (Raspberry Pi only).

```bash
pip install -r requirements.txt
# on the Pi, also:
pip install -r requirements-rpi.txt
```

## Running

```bash
python main.py          # rpi mode (default)
python main.py sim       # simulator mode, on a regular PC
```

Controls: the buttons currently map to left / right / rotate (up) / drop
(down). In `sim` mode these are the keyboard arrow keys.

## Development

The `tests/` directory contains manual, interactive hardware checks (they
light up the LED matrix and wait on real button presses) — they're meant to
be run on a Pi with the hardware attached, not as an automated test suite.

## Project layout

```
common/              shared types and helpers
game/                game logic and rendering (currently Tetris only)
hardware/
  interfaces.py       Matrix / KeyHandler / ScoreDisplay contracts, shared Key enum
  canvas.py            hardware-agnostic drawing surface used by game/drawer.py
  factory.py           picks the rpi or simulator backend for a given mode
  rpi/                 real hardware: WS281x matrix, GPIO buttons, serial score
  simulator/           tkinter stand-ins: matrix, keyboard buttons, 7-seg score
tests/               manual hardware checks
main.py              entry point / game loop
```

See [`CLAUDE.md`](CLAUDE.md) for more detail on the current architecture and
where it's headed.
