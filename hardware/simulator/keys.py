from hardware.interfaces import Key, KeyHandler
from hardware.simulator.window import get_window

_KEYSYM_TO_KEY = {
    "Up": Key.UP,
    "Down": Key.DOWN,
    "Left": Key.LEFT,
    "Right": Key.RIGHT,
    # WASD/P/M also list the keysyms an active non-Latin keyboard *group*
    # (e.g. a dual us/il layout switched to Hebrew) produces for the same
    # physical keys, so a press isn't silently dropped just because the
    # wrong group happens to be active - Right/Left/Return etc. don't need
    # this since arrow/control keysyms are the same in every group.
    "w": Key.P2_UP, "W": Key.P2_UP, "apostrophe": Key.P2_UP,
    "s": Key.P2_DOWN, "S": Key.P2_DOWN, "hebrew_dalet": Key.P2_DOWN,
    "a": Key.P2_LEFT, "A": Key.P2_LEFT, "hebrew_shin": Key.P2_LEFT,
    "d": Key.P2_RIGHT, "D": Key.P2_RIGHT, "hebrew_gimel": Key.P2_RIGHT,
    "Return": Key.ENTER,
    "p": Key.PAUSE, "P": Key.PAUSE, "hebrew_pe": Key.PAUSE,
    "m": Key.MUTE, "M": Key.MUTE, "hebrew_zade": Key.MUTE,
}

# (col, row) in a 3x3 D-pad grid
_PAD1_LAYOUT = {
    Key.UP: (1, 0),
    Key.LEFT: (0, 1),
    Key.RIGHT: (2, 1),
    Key.DOWN: (1, 2),
}

_PAD2_LAYOUT = {
    Key.P2_UP: (1, 0),
    Key.P2_LEFT: (0, 1),
    Key.P2_RIGHT: (2, 1),
    Key.P2_DOWN: (1, 2),
}

_KEY_LABEL = {
    Key.UP: "^",
    Key.DOWN: "v",
    Key.LEFT: "<",
    Key.RIGHT: ">",
    Key.P2_UP: "W",
    Key.P2_DOWN: "S",
    Key.P2_LEFT: "A",
    Key.P2_RIGHT: "D",
    Key.ENTER: "entr",
    Key.PAUSE: "P",
    Key.MUTE: "M",
}

# Toggle buttons (Key.PAUSE, Key.MUTE): a completed click flips a
# persistent on/off state instead of reporting a one-shot command.
_TOGGLE_KEYS = (Key.PAUSE, Key.MUTE)

BUTTON_SIZE = 20
BUTTON_GAP = 11
LABEL_FONT = ("TkDefaultFont", 8)
IDLE_COLOR = "#f00020"        # a D-pad/Enter button the active game actually reads
INACTIVE_COLOR = "#3a3a3a"    # ...and one it doesn't - dimmed gray instead of red
PRESSED_COLOR = "#550000"
IDLE_TEXT_COLOR = "#ffffff"
PRESSED_TEXT_COLOR = "#ffffff"

# Pause/mute are neutral-colored (not red, like the momentary buttons) so
# they read as a different kind of control, and lit only while toggled on.
TOGGLE_IDLE_COLOR = "#33475b"
TOGGLE_ON_COLOR = "#39b6ff"
TOGGLE_GAP = 30  # gap from Enter to the first toggle button


class SimulatorKeyHandler(KeyHandler):
    """Keyboard keys standing in for the physical buttons - arrows for the
    1st D-pad, WASD for the 2nd, Enter for the menu select/back button,
    P/M as pause/mute toggles - with on-screen buttons highlighting
    whichever key is currently pressed, dimmed gray instead of red for
    whichever ones the active game doesn't actually use, and a lit fill on
    the toggle buttons while they're on."""

    def __init__(self):
        self._window = get_window()
        self._last_key_pressed = Key.NO_KEY
        self._key_clicked = Key.NO_KEY
        self._held_keys = set()
        self._toggled = dict.fromkeys(_TOGGLE_KEYS, False)
        self._active_keys = frozenset()
        self._pending_release = {}

        self._buttons = {}
        self._labels = {}
        self._draw_buttons()

        root = self._window.root
        for name in _KEYSYM_TO_KEY:
            root.bind(f"<KeyPress-{name}>", self._on_press)
            root.bind(f"<KeyRelease-{name}>", self._on_release)

    def _idle_color(self, key: Key) -> str:
        return IDLE_COLOR if key in self._active_keys else INACTIVE_COLOR

    def _draw_button(self, canvas, key: Key, x0: float, y0: float):
        self._buttons[key] = canvas.create_oval(
            x0 - BUTTON_SIZE, y0 - BUTTON_SIZE,
            x0 + BUTTON_SIZE, y0 + BUTTON_SIZE,
            fill=self._idle_color(key), outline="", width=0)
        self._labels[key] = canvas.create_text(
            x0, y0, text=_KEY_LABEL[key],
            fill=IDLE_TEXT_COLOR, anchor="center", font=LABEL_FONT)

    def _draw_toggle_button(self, canvas, key: Key, x0: float, y0: float):
        self._buttons[key] = canvas.create_oval(
            x0 - BUTTON_SIZE, y0 - BUTTON_SIZE,
            x0 + BUTTON_SIZE, y0 + BUTTON_SIZE,
            fill=TOGGLE_IDLE_COLOR, outline="", width=0)
        self._labels[key] = canvas.create_text(
            x0, y0, text=_KEY_LABEL[key],
            fill=IDLE_TEXT_COLOR, anchor="center", font=LABEL_FONT)

    def _draw_dpad(self, canvas, layout, origin):
        ox, oy = origin
        for key, (col, row) in layout.items():
            x0 = ox + col * (BUTTON_SIZE + BUTTON_GAP)
            y0 = oy + row * (BUTTON_SIZE + BUTTON_GAP)
            self._draw_button(canvas, key, x0, y0)

    def _draw_buttons(self):
        canvas = self._window.canvas
        self._draw_dpad(canvas, _PAD2_LAYOUT, self._window.buttons_origin)
        self._draw_dpad(canvas, _PAD1_LAYOUT, self._window.buttons2_origin)

        ex, ey = self._window.enter_button_origin
        self._draw_button(canvas, Key.ENTER, ex, ey)

        px = ex + BUTTON_SIZE * 2 + TOGGLE_GAP
        self._draw_toggle_button(canvas, Key.PAUSE, px, ey)
        mx = px + BUTTON_SIZE * 2 + BUTTON_GAP
        self._draw_toggle_button(canvas, Key.MUTE, mx, ey)

    def _set_button_pressed(self, key: Key, pressed: bool):
        canvas = self._window.canvas
        canvas.itemconfig(self._labels[key], fill=PRESSED_TEXT_COLOR if pressed else IDLE_TEXT_COLOR)
        if key in _TOGGLE_KEYS:
            return  # toggle buttons' fill reflects on/off state, not momentary press
        canvas.itemconfig(self._buttons[key], fill=PRESSED_COLOR if pressed else self._idle_color(key))

    def _update_toggle_visual(self, key: Key):
        color = TOGGLE_ON_COLOR if self._toggled[key] else TOGGLE_IDLE_COLOR
        self._window.canvas.itemconfig(self._buttons[key], fill=color)

    def _on_press(self, event):
        key = _KEYSYM_TO_KEY[event.keysym]
        pending = self._pending_release.pop(key, None)
        if pending is not None:
            # X auto-repeat delivers release+press pairs for as long as a
            # key is held - this press immediately follows one of those,
            # not a fresh physical press, so cancel the deferred release
            # below and treat the hold as uninterrupted.
            self._window.root.after_cancel(pending)
            return
        self._set_button_pressed(key, True)
        self._last_key_pressed = key
        self._held_keys.add(key)

    def _on_release(self, event):
        key = _KEYSYM_TO_KEY[event.keysym]
        # Deferred by one tick: if this is an auto-repeat release, the
        # matching auto-repeat press (see _on_press) arrives before this
        # callback runs and cancels it, so a held key never gets treated
        # as clicked (and a toggle key never double-flips) mid-hold.
        self._pending_release[key] = self._window.root.after(0, self._finish_release, key)

    def _finish_release(self, key: Key):
        self._pending_release.pop(key, None)
        self._set_button_pressed(key, False)
        self._held_keys.discard(key)
        if key == self._last_key_pressed:
            self._key_clicked = key
            self._last_key_pressed = Key.NO_KEY
            if key in self._toggled:
                self._toggled[key] = not self._toggled[key]
                self._update_toggle_visual(key)

    def get_key(self) -> Key:
        # Only clears the one-shot _key_clicked, not _last_key_pressed: a
        # press already seen but not yet released must survive across
        # get_key() calls, or a fast poller (the menu) can wipe it before
        # the matching release ever arrives, silently dropping the click.
        self.pump()
        key = self._key_clicked
        self._key_clicked = Key.NO_KEY
        return key

    def flush(self):
        self._last_key_pressed = Key.NO_KEY
        self._key_clicked = Key.NO_KEY

    def pump(self):
        self._window.pump()

    def is_pressed(self, key: Key) -> bool:
        return key in self._held_keys

    def is_toggled(self, key: Key) -> bool:
        return self._toggled.get(key, False)

    def set_active_keys(self, keys):
        self._active_keys = frozenset(keys)
        canvas = self._window.canvas
        for key in self._buttons:
            if key not in _TOGGLE_KEYS:
                canvas.itemconfig(self._buttons[key], fill=self._idle_color(key))
