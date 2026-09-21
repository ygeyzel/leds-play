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
- **Game interface extracted + Tetris migrated behind it** (design in
  `GAME_TEMPLATE.md`):
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
  - `games/registry.py` — explicit `GAMES` list (just `TetrisGame` at this
    point); `main.py` ran `GAMES[0]` directly since the actual
    game-selection launcher didn't exist yet - see the menu entry below.
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
    subclass's `__init__` took `(matrix, banner_matrix=None,
    score_file=None)` by convention at this point (a `key_handler` param
    was added later - see the Snake entry below).
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
- **Implemented Snake** (`games/snake/`) as the second game, validating
  that the `Game` abstraction actually generalizes beyond Tetris:
  - `board.py` — grid-based snake/apple logic: arrow keys steer (a
    180-degree reversal into your own neck is ignored), moving into the
    cell the tail is vacating is legal, eating the apple scores 5 points
    and grows the snake by one, hitting a wall or your own body ends the
    round.
  - `drawer.py` — white full box border (`Canvas.draw_borders`'s default
    all-four-sides mode, unlike Tetris's partial one), green snake, red
    apple.
  - Holding the run key (`Key.P2_UP`, "W" in `sim`) speeds up play a bit.
    This needed a new capability, since `get_key()` only reports discrete
    one-shot clicks: `KeyHandler.is_pressed(key)` (new, defaults to
    `False`, implemented in both backends via a `_held_keys` set updated
    on press/release) reports whether a key is down *right now*, checked
    every tick by `SnakeGame.turn_interval`. This is also why every
    `Game` subclass's constructor convention grew a third argument -
    `(matrix, banner_matrix=None, key_handler=None, score_file=None)` -
    `main.py` and `MenuGame` now pass the shared `KeyHandler` through the
    same way they already pass the shared matrices; Tetris/the menu
    accept and ignore it.
  - Registered in `games/registry.py` (`GAMES = [TetrisGame, SnakeGame]`)
    - reachable from the menu today.
  - Verified: an isolated logic script covering apple-eating/scoring,
    wall-collision death, self-collision death (and that reversing
    180 degrees is a no-op), and the run-speed switch; plus a real `sim`
    run confirming rendering, menu selection, and the wall-death ->
    game-over-screen -> menu flow end-to-end.
- **Real logo art for Tetris and Snake**: `games/tetris/logo.png` (a cyan
  T-tetromino framed by 2x2 corner squares in the other three piece
  colors) and `games/snake/logo.png` (a coiled green snake body around a
  red apple), both 10x10 pixel art with a transparent background,
  authored directly at the menu's `LOGO_SIZE`. `TetrisGame.LOGO_PATH`/
  `SnakeGame.LOGO_PATH` now point at them (`os.path.join(os.path.dirname
  (__file__), "logo.png")`), so the menu shows real art instead of the
  placeholder box for both games. Verified via `games.logo.load_logo`
  directly (correct 10x10 shape/transparency) and a `sim`-mode run.
- **Restart-on-death + Snake's death blink** (design in `GAME_TEMPLATE.md`):
  - `Game.on_round_end` now returns a bool: True if an arrow key ended the
    wait screen, False otherwise (e.g. ENTER). `main.py`'s `game_loop`/
    `main()` use it to either restart the same game instance (fresh score,
    `best_score` untouched) or fall back to the menu - generic on the base
    class, so Tetris gets this for free alongside Snake.
  - Snake now blinks on game over too: `Drawer.blink_board()` flips the
    snake's color 180 degrees around the hue wheel each
    `on_game_over_tick()` (green <-> magenta), same idea as Tetris's board
    blink; `SnakeGame.start()` resets it back to green via
    `Drawer.reset_colors()` so a restart isn't stuck mid-blink.
  - Apple is now worth 5 points (was 10).
  - Verified: an isolated script driving `on_round_end` with a
    `FakeKeyHandler` (arrow key restarts, ENTER doesn't; score resets to 0
    while `best_score` survives; the blink color toggles and resets) for
    both Snake and Tetris, plus a real `sim` run - wall death, the green/
    magenta blink, and a clean fresh-state restart on an arrow key.
- **`--start-game NAME` CLI flag**: skips the menu and goes straight into
  the named game (`main.py sim --start-game Snake`); `NAME` must match a
  `Game.NAME` in `games.registry.GAMES` exactly (argparse `choices`
  validates it). Falls back to the menu once that game's round ends
  without an arrow-key restart.
- **Menu shows the selected game's best score**: `games/base.py`'s
  per-game best-score file helpers (`default_score_file`/
  `read_best_score`) became module-level functions (previously private
  `Game` methods) so they work from a game *class* alone, no instance
  needed. `MenuGame.best_score` is now a property that looks up
  `selected_game_cls`'s best score this way (its setter is a no-op -
  `Game.__init__` still assigns `self.best_score` once, harmlessly);
  `main.py`'s existing `score_display.send_score(game.score,
  game.best_score)` call already runs every menu tick, so the display
  updates live as LEFT/RIGHT change the selection. Verified with an
  isolated script (switching `MenuGame._index` reads back the right
  game's score) and a real `sim` run.
- **Simpler logos + a small-logo preview strip in the menu** (design in
  `GAME_TEMPLATE.md`):
  - `games/tetris/logo.png` is now just four flat colored squares (cyan/
    yellow/purple/orange), and `games/snake/logo.png` a plain blocky green
    "S" - replacing the more detailed T-tetromino/coiled-snake art.
  - **Found and fixed a real bug while making the Tetris logo**:
    `common.common.hsv_to_rgb`'s hue-sector lookup was `rgb0_by_h0[int(h0)
    - 1]` instead of `int(h0) % 6` - at `h0` (`hue/60`) in `[0, 1)`, `int(h0)
    - 1` is `-1`, which Python happily reads as the *last* tuple element
    instead of raising, so every hue silently got the wrong RGB formula
    except ones sitting exactly on a 60-degree boundary (pure red, green,
    etc. - which is why nothing looked obviously broken before: every
    color already in use happened to be a boundary hue). Fixed and
    reverified all the primary/secondary hues come out correct now.
  - The menu shows a row of small logos above each arrow (previous games
    above the left one, next games above the right, closest one
    column-aligned with its arrow) - the same `logo.png`, just decoded
    smaller, updating as LEFT/RIGHT cycle the selection.
    `MenuGame._logo_cache` is keyed by `(game_cls, size)` since the big
    and small logos are separate decodes of the same file. Went through a
    couple of layout iterations before landing here (beside the big logo,
    then above it) - above the arrows is what stuck.
  - The banner's scrolling name now uses a small copy of the selected
    game's logo as the separator between repeats, instead of a blank gap.
  - `tools/logo_editor.py` - a standalone tkinter tool for painting
    `logo.png` (and, if hand-tuned separately from the big one, a
    `logo_small.png`) instead of scripting it: preset palette + full color
    picker, save to an existing game, a typed new game name, or any path.
  - Verified in `sim` mode across the iterations, plus a manual pass on
    the logo editor's paint/preview/save.
- **Bigger menu art + a real 8-row banner font + a font editor**:
  - `games/menu/font.py`'s bitmap font grew from 3x5 to 5x8 - genuinely
    redesigned per-glyph (not just a blank row tacked onto the old 7-row
    shapes, which was tried first and correctly called out as pointless
    padding for a single scrolling line).
  - `LOGO_SIZE` 10x10 -> 12x12, `SMALL_LOGO_SIZE` 4x4 -> 6x6. Since
    `SMALL_LOGO_SIZE` is now wider than `ARROW_SIZE`, the preview-strip
    placement in `MenuGame._create_matrix_canvases` needed a real fix, not
    just bigger numbers: anchoring the innermost small logo's *left* edge
    to the arrow's position on both sides (the old formula) overhangs
    rightward on both sides, which starves the right side's outer margin;
    the right side now anchors to the arrow's *right* edge instead, a true
    mirror of the left side.
  - `tools/font_editor.py` added: shows every glyph at once (sim-style lit/
    unlit cells), click to edit pixel-by-pixel, "Save to font.py" rewrites
    just the `_GLYPHS` dict via a regex match on that block. Also shows
    blank a-z slots alongside the real A-Z/0-9/space entries (the app
    itself only ever looks up uppercase) in case lowercase is wanted later;
    saving only keeps a blank glyph if it was already in the file or
    genuinely edited this session, so browsing the tool and saving doesn't
    flood the file with 26 empty lowercase entries.
  - Verified: a `sim` run (banner text fills the full 8-row height, no
    logo/arrow overlap at default matrix width) and a manual pass on the
    font editor (lowercase slots appear, editing/saving round-trips
    correctly, blank untouched slots aren't written).

- **Pause/mute toggle buttons + active-button dimming in `sim`**:
  - `hardware/interfaces.py`'s `Key` enum gained `PAUSE` and `MUTE`;
    `KeyHandler` gained `is_toggled(key)` (a persistent on/off state
    flipped by each completed click, independent of `get_key()`'s one-shot
    reporting and `is_pressed()`'s momentary hold) and `set_active_keys(keys)`
    (tells the backend which keys the current game/menu actually reads).
    Both default to no-op/never-toggled for a backend that doesn't support
    them yet (`hardware/rpi/keys.py` is unaffected).
  - `hardware/simulator/keys.py`: P/M on-screen buttons next to Enter, in a
    neutral blue-gray instead of the D-pad's red, lit brighter while
    toggled on. Every D-pad/Enter button the active game doesn't list in
    its `USED_KEYS` now dims to gray instead of red (an idea that started
    as a lit ring around active buttons, then was simplified to this
    gray-vs-red fill). `main.py::init_game` always includes `Key.ENTER` in
    the active set even for a game whose own `USED_KEYS` doesn't list it,
    since ENTER always does something (exit to menu).
  - `main.py::_sleep` (used for every turn's wait, and reused as-is for the
    pause case) pushes its deadline forward instead of counting down while
    `Key.PAUSE` is toggled on - the turn clock halts, but keys (PAUSE
    itself included, to unpause) keep being read every pump.
  - Found and fixed a real bug along the way: a held key delivers
    release+press pairs from X11 auto-repeat, and the original toggle
    logic treated every release as a completed click, so one physical
    press of P/M could flip the toggle 0 or 2 times instead of once (only
    visible on a toggle - a duplicate one-shot click is harmless, which is
    why the same binding pattern never caused trouble for the D-pad).
    Fixed with the standard Tk idiom: defer a release by one tick and
    cancel it if a matching press arrives immediately after.
  - Verified in `sim` mode via screenshots: single click reliably toggles
    P on then off (no double-fire), the board visibly freezes while paused
    and resumes exactly where it left off on unpause, and Enter/D-pad
    dim to gray correctly per-game.
  - Also generated `games/tetris/logo_small.png` and
    `games/snake/logo_small.png` (hand-tunable small-logo overrides that
    `tools/logo_editor.py` already knew how to read/write; the app falls
    back to decoding `logo.png` smaller when this file doesn't exist).
- **Lowercase glyphs added to the banner font**: `games/menu/font.py`'s
  `_GLYPHS` now has real a-z shapes (previously only `tools/font_editor.py`
  showed blank editable slots for them) - baseline at row 5, ascenders
  (b/d/f/h/k/l/t) reaching up to row 0 like the capitals, descenders
  (g/j/p/q/y) reaching down to row 7. Not wired up to anything yet: every
  caller (`games/menu/__init__.py`'s banner text) still uppercases its
  string before rendering, so this is font *data* only, available for
  `tools/font_editor.py` and for whenever mixed-case rendering is wanted.
  Verified via the font editor: all 26 slots render distinct non-blank
  shapes.
- **Wired up hand-tuned `logo_small.png`**: `tools/logo_editor.py` could
  already save one (painting the small canvas directly turns off
  "auto-generate from big logo" and saves the result alongside `logo.png`),
  but `MenuGame` never looked for it - it always resized `logo.png` down,
  silently ignoring any `logo_small.png` on disk. `MenuGame.
  _load_logo_for_size` now prefers `logo_small.png` next to `LOGO_PATH`
  when requesting `SMALL_LOGO_SIZE`, falling back to the resize when that
  file doesn't exist. Verified in `sim`: saved a deliberately distinct test
  `logo_small.png` for Tetris and confirmed the menu's preview strip shows
  it (not an auto-shrunk `logo.png`) while Snake is selected.
- **Layout-independent WASD/Pause/Mute keysyms in `sim`**: this dev
  machine's dual `us,il` keyboard layout means the physical P/M/W/A/S/D
  keys produce different X keysyms (`hebrew_pe`, `hebrew_zade`,
  `apostrophe`, `hebrew_shin`, `hebrew_dalet`, `hebrew_gimel`) when the
  Hebrew group is active, which `hardware/simulator/keys.py`'s
  `_KEYSYM_TO_KEY` didn't recognize - a press while that group happened to
  be active was silently dropped (not bound to anything), which could look
  like Pause working unreliably. Traced this down while investigating a
  "pause doesn't fully stop the banner, just slows it" report - the pause
  mechanism itself was verified correct (a clean toggle freezes the
  banner's scroll position bit-for-bit, confirmed via screenshots 2s
  apart); `_KEYSYM_TO_KEY` now also maps each of those alternate-group
  keysyms to the same `Key`, so the toggle can't be silently missed
  depending on which keyboard group happens to be active.

## In progress

Nothing active right now — see "Not started yet" for what's next.

## Not started yet (planned)

Roughly in the order they'll likely need to happen:

1. **Audio**: the `AudioPlayer` contract, `pygame.mixer`-based sim backend,
   and rpi no-op stub from `GAME_TEMPLATE.md` haven't been built, and no
   game defines `BGM_PATH`/`SFX_PATHS` yet.
2. **Simulator pause/mute keys**: add `P` (pause the game loop) and `M`
   (mute/unmute music) to `hardware/simulator/keys.py`, sim mode only.
   Global controls, not a per-game command, so probably handled directly
   in `main.py`'s `game_loop` (like the existing `Key.ENTER`-to-menu
   handling) rather than via a game's `USED_KEYS`/`advance_turn`. Mute is
   a no-op until item 1 (audio) exists.
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
   - Neither Tetris nor Snake render anything into the banner (the menu
     does; both just leave it blank while playing) or react to the 2nd
     D-pad beyond Snake's `Key.P2_UP` run boost.
4. **Implement More Games** ...

## Open questions for the user

- Real GPIO pin numbers for the 5 new buttons and the banner strip, and
  whatever panel-count/wiring specifics the rpi backend needs once it's
  brought up to parity with the sim backend (see roadmap item 3).
