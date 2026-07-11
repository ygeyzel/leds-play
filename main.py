import argparse
from time import sleep, time

from game.drawer import Drawer
from game.game_board import Board
from hardware.factory import create_key_handler, create_score_display
from hardware.interfaces import Key, KeyHandler


def parse_args():
    parser = argparse.ArgumentParser(description="LEDs Play")
    parser.add_argument(
        "mode", nargs="?", choices=["rpi", "sim"], default="rpi",
        help="run against real hardware (rpi) or the graphical simulator (sim); default: rpi")
    return parser.parse_args()


def init_game(board: Board, key_handler: KeyHandler):
    board.start()
    key_handler.flush()


def game_over(drawer: Drawer, key_handler: KeyHandler):
    key_handler.flush()
    end_time = time()

    while key_handler.get_key() == Key.NO_KEY or time() - end_time < 2:
        drawer.blink_board()
        sleep(0.2)


PUMP_INTERVAL = 0.02


def _sleep(seconds: float, key_handler: KeyHandler):
    """Sleep in small slices, pumping the key handler between them so a
    backend that needs to service a GUI event loop (the simulator) stays
    responsive instead of freezing for the whole turn."""

    deadline = time() + seconds
    while (remaining := deadline - time()) > 0:
        key_handler.pump()
        sleep(min(PUMP_INTERVAL, remaining))


def game_loop(score_display, board: Board, drawer: Drawer, key_handler: KeyHandler):
    drawer.draw_board()

    while not board.is_game_over():
        dt = 1 / board.level
        _sleep(dt, key_handler)

        key = key_handler.get_key()
        board.advance_turn(key)

        drawer.clear()
        drawer.draw_board()
        score_display.send_score(board.score, board.best_score)

    game_over(drawer, key_handler)


def main():
    mode = parse_args().mode

    drawer = Drawer(mode)
    board = drawer.board
    board.burn_animation = drawer.burn_animation

    key_handler = create_key_handler(mode)

    with create_score_display(mode) as score_display:
        while True:
            init_game(board, key_handler)
            game_loop(score_display, board, drawer, key_handler)


if __name__ == "__main__":
    main()
