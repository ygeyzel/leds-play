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
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        if self.serial and self.serial.is_open:
            self.serial.close()

    def send_score(self, score, highest):
        if self.serial is None:
            return
        try:
            message = f"{score} {highest}\r\n"
            self.serial.write(message.encode())
            # Wait for data to be written
            self.serial.flush()
        except serial.SerialException:
            pass
