from time import sleep
from hardware.rpi.keys import RpiKeyHandler


def test_get_key():
    key_handler = RpiKeyHandler()
    print("Press keys")
    while True:
        key = key_handler.get_key()
        print(f"\t{key.name}")
        sleep(1)


if __name__ == "__main__":
    test_get_key()
