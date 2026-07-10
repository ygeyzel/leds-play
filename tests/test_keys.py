from time import sleep
from hardware.keys import get_key


def test_get_key():
    print("Press keys")
    while True:
        key = get_key()
        print(f"\t{key.name}")
        sleep(1)


if __name__ == "__main__":
    test_get_key()
