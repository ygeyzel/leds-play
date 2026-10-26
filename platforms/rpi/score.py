import time

import serial

from platforms.interfaces import ScoreDisplay


class SerialScoreDisplay(ScoreDisplay):
    def __init__(self, port="/dev/ttyUSB0", baudrate=115200, timeout=1):
        self.port = port
        self.baudrate = baudrate
        self.timeout = timeout
        self.serial = None

    def __enter__(self):
        # The display is optional: without it, scores just aren't shown.
        try:
            self.serial = serial.Serial(
                port=self.port,
                baudrate=self.baudrate,
                timeout=self.timeout
            )
        except serial.SerialException as e:
            print(f"warning: no score display, running without one ({e})")
            return self
        # Allow ESP32 to initialize
        time.sleep(2)
        # End any partial line left in the ESP32's buffer (e.g. a glitch
        # byte from opening the port), so the first score isn't garbled.
        self.serial.write(b"\n")
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        if self.serial and self.serial.is_open:
            self.serial.close()

    def send_score(self, score, highest):
        """leds-play-score-board protocol: "left,right" + newline puts each
        part on one of its two 8x32 boards (all-digit parts are zero-padded
        to 8 digits). It answers every line with "OK" or an error, which
        nothing here needs - drop them so they don't pile up unread."""

        if self.serial is None:
            return
        try:
            self.serial.reset_input_buffer()
            message = f"{score},{highest}\n"
            self.serial.write(message.encode())
            # Wait for data to be written
            self.serial.flush()
        except serial.SerialException:
            pass
