import argparse
from time import sleep, time

from games.base import Game
from games.registry import GAMES
from games.tetris.drawer import NUM_OF_MATRICES, SIZE_OF_BANNER
from hardware.factory import create_key_handler, create_score_display
from hardware.interfaces import Key, KeyHandler


def parse_args():
    parser = argparse.ArgumentParser(description="LEDs Play")
    parser.add_argument(
        "mode", nargs="?", choices=["rpi", "sim"], default="rpi",
        help="run against real hardware (rpi) or the graphical simulator (sim); default: rpi")
    parser.add_argument(
        "--num-of-matrices", type=int, default=NUM_OF_MATRICES,
        help="number of chained board LED panels (each 8x32); default: %(default)s. "
             "rpi mode doesn't support this yet and always uses 2.")
    parser.add_argument(
        "--size-of-banner", type=int, default=SIZE_OF_BANNER,
        help="number of chained banner LED panels (each 8 rows x 32 cols); "
             "default: %(default)s. rpi mode doesn't support a banner yet.")
    return parser.parse_args()


def init_game(game: Game, key_handler: KeyHandler):
    game.start()
    key_handler.flush()


def game_over(game: Game, key_handler: KeyHandler):
    key_handler.flush()
    end_time = time()

    while key_handler.get_key() == Key.NO_KEY or time() - end_time < 2:
        game.on_game_over_tick()
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


def game_loop(score_display, game: Game, key_handler: KeyHandler):
    game.render()

    while not game.is_game_over():
        _sleep(game.turn_interval, key_handler)

        key = key_handler.get_key()
        game.advance_turn(key)
        game.render()
        score_display.send_score(game.score, game.best_score)

    game_over(game, key_handler)


def main():
    args = parse_args()
    mode = args.mode

    # A real game-selection launcher (picking from GAMES) is future work,
    # see STATUS.md - for now the platform still only runs one game.
    game_cls = GAMES[0]
    game = game_cls(mode, args.num_of_matrices, args.size_of_banner)

    key_handler = create_key_handler(mode)

    with create_score_display(mode) as score_display:
        while True:
            init_game(game, key_handler)
            game_loop(score_display, game, key_handler)


if __name__ == "__main__":
    main()
