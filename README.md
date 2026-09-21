# LEDs Play

A multi-game platform for an LED-matrix display with physical button
controls, built to run on a Raspberry Pi — with a PC-based simulator mode
for developing and testing games without the hardware.

This project is the successor to [`TetLED`](https://github.com/ygeyzel/tetled), a Tetris-only version of the
same idea. `LEDs Play` generalizes it into a real game platform: a
game-selection menu, Tetris and Snake to pick from, and room to add more.

> **Status:** the game abstraction has landed — there's a menu, and two
> games (Tetris, Snake) behind it. See [`STATUS.md`](STATUS.md) for the
> full history and what's planned next (audio, more games, bringing `rpi`
> mode up to parity with `sim`).

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

## Playing

Starting `main.py` opens a menu: the selected game's logo sits centered on
the board matrix with small previews of the neighboring games above the
left/right arrows, its name scrolls across the banner, and the score
display shows its best score. LEFT/RIGHT cycle through the games, ENTER
launches the highlighted one.

To skip the menu and go straight into a game:

```bash
python main.py sim --start-game Snake
```

**In any game**, ENTER returns to the menu (unless the game itself uses
ENTER for something — none currently do). When a round ends, pressing an
arrow key restarts that same game immediately with a fresh score; any
other key goes back to the menu.

**Tetris** — D-pad 1 (arrow keys in `sim`): left/right to move, up to
rotate, down to drop.

**Snake** — D-pad 1 (arrow keys in `sim`) to steer. Hold the run key
(`Key.P2_UP`, `W` in `sim`) to move a bit faster for as long as it's held.
Eating the apple scores points and grows the snake; hitting a wall or its
own body ends the round.

## Hardware (current)

- Two 8x32 WS281x LED panels wired together as one 16x32 matrix.
- 4 buttons (up, down, left, right) wired to GPIO pins.
- Optional: an external serial (ESP32) score display.

This is expected to grow (more LEDs, more buttons) as new games need more
display area or more input actions than Tetris did. `sim` mode already
supports the bigger setup described below; the `rpi` backend hasn't been
updated to match yet (still fixed at 2 panels / 4 buttons / no banner).

## Hardware (sim mode, configurable)

- **Board matrix**: `--num-of-matrices N` (default 5) chains N 8x32 panels
  side by side into an `8*N`-wide by 32-tall matrix.
- **Banner**: `--size-of-banner N` (default 2) chains N 8-row-by-32-col
  panels side by side above the board matrix, as its own independent
  matrix. The menu scrolls the selected game's name across it; games
  themselves don't render into it yet.
- **Buttons**: two D-pads (up/down/left/right each) plus an Enter button,
  9 inputs in total:
  - D-pad 1 (original 4): arrow keys in `sim`. Used by the menu and every
    game for movement/selection.
  - D-pad 2 (`Key.P2_*`): `W`/`A`/`S`/`D` in `sim`. `W` is Snake's run key;
    the rest are reserved for a future 2nd player/game.
  - Enter (`Key.ENTER`): `Enter`/`Return` in `sim`. Launches a game from
    the menu, or returns to the menu from within a game.

  `rpi` mode still only has the original 4 GPIO buttons.

## Requirements

- Python 3.
- `sim` mode needs [Pillow](https://pypi.org/project/Pillow/) (for
  decoding game logos) on top of the standard library (tkinter).
- `rpi` mode additionally needs the `rpi` dependency group (Raspberry Pi
  only).

Using [`uv`](https://docs.astral.sh/uv/) (recommended):

```bash
uv sync              # sim mode deps
uv sync --extra rpi  # on the Pi, also installs the rpi hardware deps
```

Or with plain `pip`:

```bash
pip install -r requirements.txt
# on the Pi, also:
pip install -r requirements-rpi.txt
```

## Running

```bash
uv run python main.py                              # rpi mode (default)
uv run python main.py sim                           # simulator mode, on a regular PC
uv run python main.py sim --start-game Tetris       # skip the menu, go straight into Tetris
uv run python main.py sim --num-of-matrices 8 --size-of-banner 3  # bigger sim setup
```

(or, without `uv`, `python main.py` / `python main.py sim` as usual once
dependencies are installed.)

## Development

- The `tests/` directory contains manual, interactive hardware checks
  (they light up the LED matrix and wait on real button presses) — they're
  meant to be run on a Pi with the hardware attached, not as an automated
  test suite.
- `tools/logo_editor.py` and `tools/font_editor.py` are standalone tkinter
  tools for hand-authoring a game's `logo.png` and for editing
  `games/menu/font.py`'s bitmap font, instead of scripting them.
- Run `ruff check` before committing any Python changes.

## Project layout

```
common/              shared types and helpers
games/
  base.py             Game contract every game (and the menu) implements
  registry.py          explicit list of games selectable from the menu
  logo.py              decodes a game's logo.png into a pixel grid
  menu/                the game-selection screen, itself a Game
  tetris/              Tetris: rules/state, rendering, logo
  snake/               Snake: rules/state, rendering, logo
hardware/
  interfaces.py       Matrix / KeyHandler / ScoreDisplay contracts, shared Key enum
  canvas.py            hardware-agnostic drawing surface used by game drawers
  factory.py           picks the rpi or simulator backend for a given mode
  rpi/                 real hardware: WS281x matrix, GPIO buttons, serial score
  simulator/           tkinter stand-ins: matrix, keyboard buttons, 7-seg score
tools/               standalone logo/font authoring tools (see Development)
tests/               manual hardware checks
main.py              entry point / menu + game loop
```

See [`CLAUDE.md`](CLAUDE.md) for more detail on the architecture,
[`GAME_TEMPLATE.md`](GAME_TEMPLATE.md) for the per-game contract new games
implement, and [`STATUS.md`](STATUS.md) for what's done and what's next.
