from enum import Enum
from RPi import GPIO


GPIO.setmode(GPIO.BCM)


class Key(Enum):
    NO_KEY = None
    UP = 26
    DOWN = 23
    LEFT = 4
    RIGHT = 12


class _KeysHandler:
    def __init__(self):
        self._last_key_pressed = Key.NO_KEY
        self._key_clicked = Key.NO_KEY

        for key in Key:
            if key_gpio := key.value:
                GPIO.setup(key_gpio, GPIO.IN, GPIO.PUD_UP)
                GPIO.add_event_detect(key_gpio, GPIO.BOTH, callback=self._handle_key_pressed)
    
    def _handle_key_pressed(self, channel):
        key = Key(channel)

        if GPIO.input(channel):
            if key == self._last_key_pressed:
                self._key_clicked = Key(channel)
                self._last_key_pressed = Key.NO_KEY
        else:
            self._last_key_pressed = key
            
    def get_key(self) -> Key:
        key = self._key_clicked
        self.flush()
        return key
    
    def flush(self):
        self._last_key_pressed = Key.NO_KEY
        self._key_clicked = Key.NO_KEY


_key_handler = _KeysHandler()


def KeyHandler() -> _KeysHandler:
    return _key_handler
