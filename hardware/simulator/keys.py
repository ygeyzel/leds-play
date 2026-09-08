from hardware.interfaces import Key, KeyHandler
from hardware.simulator.window import get_window


_KEYSYM_TO_KEY = {
    "Up": Key.UP,
    "Down": Key.DOWN,
    "Left": Key.LEFT,
    "Right": Key.RIGHT,
    "w": Key.P2_UP, "W": Key.P2_UP,
    "s": Key.P2_DOWN, "S": Key.P2_DOWN,
    "a": Key.P2_LEFT, "A": Key.P2_LEFT,
    "d": Key.P2_RIGHT, "D": Key.P2_RIGHT,
    "Return": Key.ENTER,
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
}

BUTTON_SIZE = 20
BUTTON_GAP = 11
LABEL_FONT = ("TkDefaultFont", 8)
IDLE_COLOR = "#f00020"
PRESSED_COLOR = "#550000"
IDLE_TEXT_COLOR = "#ffffff"
PRESSED_TEXT_COLOR = "#ffffff"


class SimulatorKeyHandler(KeyHandler):
    """Keyboard keys standing in for the physical buttons - arrows for the
    1st D-pad, WASD for the 2nd, Enter for the menu select/back button -
    with on-screen buttons highlighting whichever key is currently
    pressed."""

    def __init__(self):
        self._window = get_window()
        self._last_key_pressed = Key.NO_KEY
        self._key_clicked = Key.NO_KEY

        self._buttons = {}
        self._labels = {}
        self._draw_buttons()

        root = self._window.root
        for name in _KEYSYM_TO_KEY:
            root.bind(f"<KeyPress-{name}>", self._on_press)
            root.bind(f"<KeyRelease-{name}>", self._on_release)

    def _draw_button(self, canvas, key: Key, x0: float, y0: float):
        self._buttons[key] = canvas.create_oval(
            x0 - BUTTON_SIZE, y0 - BUTTON_SIZE,
            x0 + BUTTON_SIZE, y0 + BUTTON_SIZE,
            fill=IDLE_COLOR, outline="", width=0)
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

        ox, oy = self._window.enter_button_origin
        self._draw_button(canvas, Key.ENTER, ox, oy)

    def _set_button_pressed(self, key: Key, pressed: bool):
        canvas = self._window.canvas
        canvas.itemconfig(self._buttons[key], fill=PRESSED_COLOR if pressed else IDLE_COLOR)
        canvas.itemconfig(self._labels[key], fill=PRESSED_TEXT_COLOR if pressed else IDLE_TEXT_COLOR)

    def _on_press(self, event):
        key = _KEYSYM_TO_KEY[event.keysym]
        self._set_button_pressed(key, True)
        self._last_key_pressed = key

    def _on_release(self, event):
        key = _KEYSYM_TO_KEY[event.keysym]
        self._set_button_pressed(key, False)
        if key == self._last_key_pressed:
            self._key_clicked = key
            self._last_key_pressed = Key.NO_KEY

    def get_key(self) -> Key:
        self.pump()
        key = self._key_clicked
        self.flush()
        return key

    def flush(self):
        self._last_key_pressed = Key.NO_KEY
        self._key_clicked = Key.NO_KEY

    def pump(self):
        self._window.pump()
