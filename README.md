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
> Right now the code still only runs Tetris, directly on Raspberry Pi
> hardware — simulator mode and other games are not implemented yet.

## Modes

- **`rpi` mode** — runs on a Raspberry Pi driving a real WS281x LED matrix
  and physical GPIO buttons. This is the original, currently the only
  working mode.
- **`simulator` mode** *(planned)* — runs on a regular PC with a graphical
  window standing in for the LED matrix and the keyboard standing in for the
  buttons, so games can be developed and tested without any hardware.

## Hardware (current)

- Two 8x32 WS281x LED panels wired together as one 16x32 matrix.
- 4 buttons (up, down, left, right) wired to GPIO pins.
- Optional: an external serial (ESP32) score display.

This is expected to grow (more LEDs, more buttons) as new games need more
display area or more input actions than Tetris did.

## Requirements

- Raspberry Pi (for `rpi` mode).
- Python 3, see `requirements.txt`.

```bash
pip install -r requirements.txt
```

## Running

```bash
python main.py
```

Controls: the buttons currently map to left / right / rotate (up) / drop
(down).

## Development

The `tests/` directory contains manual, interactive hardware checks (they
light up the LED matrix and wait on real button presses) — they're meant to
be run on a Pi with the hardware attached, not as an automated test suite.

## Project layout

```
common/    shared types and helpers
game/      game logic and rendering (currently Tetris only)
hardware/  LED matrix and button drivers
tests/     manual hardware checks
main.py    entry point / game loop
```

See [`CLAUDE.md`](CLAUDE.md) for more detail on the current architecture and
where it's headed.
