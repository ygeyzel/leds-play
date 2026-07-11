from hardware.interfaces import Key, KeyHandler
from hardware.simulator.window import get_window


_ARROW_TO_KEY = {
    "Up": Key.UP,
    "Down": Key.DOWN,
    "Left": Key.LEFT,
    "Right": Key.RIGHT,
}

# (col, row) in a 3x3 D-pad grid
_BUTTON_LAYOUT = {
    Key.UP: (1, 0),
    Key.LEFT: (0, 1),
    Key.RIGHT: (2, 1),
    Key.DOWN: (1, 2),
}

BUTTON_SIZE = 20
BUTTON_GAP = 11
IDLE_COLOR = "#f00020"
PRESSED_COLOR = "#550000"
IDLE_TEXT_COLOR = "#888888"
PRESSED_TEXT_COLOR = "#1a1a1a"


class SimulatorKeyHandler(KeyHandler):
    """Keyboard arrow keys standing in for the physical buttons; the D-pad
    on screen highlights whichever key is currently pressed."""

    def __init__(self):
        self._window = get_window()
        self._last_key_pressed = Key.NO_KEY
        self._key_clicked = Key.NO_KEY

        self._buttons = {}
        self._draw_buttons()

        root = self._window.root
        for name in _ARROW_TO_KEY:
            root.bind(f"<KeyPress-{name}>", self._on_press)
            root.bind(f"<KeyRelease-{name}>", self._on_release)

    def _draw_buttons(self):
        canvas = self._window.canvas
        ox, oy = self._window.buttons_origin

        for key, (col, row) in _BUTTON_LAYOUT.items():
            x0 = ox + col * (BUTTON_SIZE + BUTTON_GAP)
            y0 = oy + row * (BUTTON_SIZE + BUTTON_GAP)

            circle = canvas.create_oval(
                x0 - BUTTON_SIZE, y0 - BUTTON_SIZE,
                x0 + BUTTON_SIZE, y0 + BUTTON_SIZE,
                fill=IDLE_COLOR, outline="", width=0)
                
            self._buttons[key] = circle

    def _set_button_pressed(self, key: Key, pressed: bool):
        circle = self._buttons[key]
        canvas = self._window.canvas
        canvas.itemconfig(circle, fill=PRESSED_COLOR if pressed else IDLE_COLOR)

    def _on_press(self, event):
        key = _ARROW_TO_KEY[event.keysym]
        self._set_button_pressed(key, True)
        self._last_key_pressed = key

    def _on_release(self, event):
        key = _ARROW_TO_KEY[event.keysym]
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
