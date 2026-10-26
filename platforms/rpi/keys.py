from RPi import GPIO

from platforms.interfaces import Key, KeyHandler
from platforms.rpi.mapping import load_mapping

GPIO.setmode(GPIO.BCM)

# Buttons pull their input pin high when pressed, so inputs use the internal
# pull-down and read high while held.
BOUNCE_MS = 20


class RpiKeyHandler(KeyHandler):
    """Buttons wired straight to GPIOs, each with its own LED, per
    platforms/rpi/mapping.json's `keys`. A button's LED is lit while its key
    is active (see set_active_keys())."""

    def __init__(self):
        self._last_key_pressed = Key.NO_KEY
        self._key_clicked = Key.NO_KEY
        self._held_keys = set()
        self._pin_to_key = {}
        self._led_pins = {}

        for name, (pin, led_pin) in load_mapping()["keys"].items():
            key = Key[name]
            self._pin_to_key[pin] = key
            self._led_pins[key] = led_pin
            GPIO.setup(led_pin, GPIO.OUT, initial=GPIO.LOW)
            GPIO.setup(pin, GPIO.IN, pull_up_down=GPIO.PUD_DOWN)
            GPIO.add_event_detect(
                pin, GPIO.BOTH, callback=self._handle_key_pressed, bouncetime=BOUNCE_MS)

    def _handle_key_pressed(self, channel):
        key = self._pin_to_key[channel]

        if not GPIO.input(channel):
            self._held_keys.discard(key)
            if key == self._last_key_pressed:
                self._key_clicked = key
                self._last_key_pressed = Key.NO_KEY
        else:
            self._last_key_pressed = key
            self._held_keys.add(key)

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

    def is_pressed(self, key: Key) -> bool:
        return key in self._held_keys

    def set_active_keys(self, keys):
        for key, led_pin in self._led_pins.items():
            GPIO.output(led_pin, GPIO.HIGH if key in keys else GPIO.LOW)
