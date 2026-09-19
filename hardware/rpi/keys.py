from RPi import GPIO

from hardware.interfaces import Key, KeyHandler


GPIO.setmode(GPIO.BCM)

_KEY_PINS = {
    Key.UP: 26,
    Key.DOWN: 23,
    Key.LEFT: 4,
    Key.RIGHT: 12,
}


class RpiKeyHandler(KeyHandler):
    def __init__(self):
        self._last_key_pressed = Key.NO_KEY
        self._key_clicked = Key.NO_KEY
        self._pin_to_key = {pin: key for key, pin in _KEY_PINS.items()}

        for key, pin in _KEY_PINS.items():
            GPIO.setup(pin, GPIO.IN, GPIO.PUD_UP)
            GPIO.add_event_detect(pin, GPIO.BOTH, callback=self._handle_key_pressed)

    def _handle_key_pressed(self, channel):
        key = self._pin_to_key[channel]

        if GPIO.input(channel):
            if key == self._last_key_pressed:
                self._key_clicked = key
                self._last_key_pressed = Key.NO_KEY
        else:
            self._last_key_pressed = key

    def get_key(self) -> Key:
        # Only clears the one-shot _key_clicked, not _last_key_pressed: a
        # press already seen but not yet released must survive across
        # get_key() calls, or a fast poller (the menu) can wipe it before
        # the matching release ever arrives, silently dropping the click.
        key = self._key_clicked
        self._key_clicked = Key.NO_KEY
        return key

    def flush(self):
        self._last_key_pressed = Key.NO_KEY
        self._key_clicked = Key.NO_KEY
