from itertools import product

from tests.shared import matrix_test


OO = None
C0 = (120, 0.2, 0.1)
C1 = (120, 0.7, 0.1)
C2 = (120, 1, 0.1)

color_map = [
    [C0, C1, OO],
    [OO, C1, C2]
]
    
@matrix_test
def test_canvas(matrix):
    canvas = matrix.create_canvas((1, 3), (10, 6))
    x, y = canvas.dimensions

    print("drawing template on canvas")
    for i,j in product(range(x), range(y)):
        h = 360 * i / x                    
        s = 0.5 + 0.5 * j / (y - 1)
        canvas[i, j] = (h, s, 0.1)
    
    matrix.show()


@matrix_test
def test_draw_color_map(matrix):
    canvas = matrix.create_canvas((1, 1), (10, 10))
    c0, c1, c2, c3 = None, (40, 1, 0.1), (0, 0, 0.1), (120, 1, 0.1)

    color_map = [
        [c1, c2, c0],
        [c0, c2, c0],
        [c0, c2, c3]
    ]

    canvas.draw_color_map(color_map)
    canvas.draw_color_map(color_map, (4, 1))

    matrix.show()


@matrix_test
def test_draw_shape(matrix):
    canvas = matrix.create_canvas((1, 1), (10, 10))
    c0, c1 = (40, 1, 0.1), (120, 1, 0.1)

    shape = [
        [1, 1, 0],
        [0, 1, 0],
        [0, 1, 1]
    ]

    canvas.draw_shape(shape, c0)
    canvas.draw_shape(shape, c1, (4, 1))

    matrix.show()


@matrix_test
def test_draw_borders(matrix):
    canvas = matrix.create_canvas((1, 3), (10, 8))
    
    canvas.draw_borders((40, 1, 0.1), "ur")
    canvas.draw_borders((120, 1, 0.1), "lb")

    matrix.show()


if __name__ == "__main__":
    test_canvas()
    test_draw_color_map()
    test_draw_shape()
    test_draw_borders()
