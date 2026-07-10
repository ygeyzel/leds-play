import serial
import time
from functools import wraps


class ScoreDisplay:
    def __init__(self, port="/dev/ttyUSB0", baudrate=115200, timeout=1):
        self.port = port
        self.baudrate = baudrate
        self.timeout = timeout
        self.serial = None
    
    def __enter__(self):
        self.serial = serial.Serial(
            port=self.port,
            baudrate=self.baudrate,
            timeout=self.timeout
        )
        # Allow ESP32 to initialize
        time.sleep(2)
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        if self.serial and self.serial.is_open:
            self.serial.close()
    
    def send_score(self, score, highest):
        try:
            message = f"{score} {highest}\r\n"
            self.serial.write(message.encode())
            # Wait for data to be written
            self.serial.flush()
        except serial.SerialException:
            pass


def with_score_display(func):
    @wraps(func)
    def wrapper(*args, **kwargs):
        with ScoreDisplay() as score_display:
            return func(score_display, *args, **kwargs)
    return wrapper
