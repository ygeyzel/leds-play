from hardware.leds import DualMatrix


def matrix_test(test):
    def _matrix_test(*args, **kwargs):
        print(test.__name__)
        matrix = kwargs.get('matrix') or DualMatrix(18, 8, 32)

        try:
            matrix.clear()
            matrix.show()
            test(matrix)
            input("Press Enter to continue\n")
        finally:
            print("clear canvas")
            matrix.clear()
            matrix.show()

    return _matrix_test

