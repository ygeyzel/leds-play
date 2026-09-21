import argparse
from time import sleep, time

from games.base import Game
from games.menu import MenuGame
from games.registry import GAMES
from hardware.factory import create_banner_matrix, create_key_handler, create_matrix, create_score_display
from hardware.interfaces import Key, KeyHandler


# Physical rig layout: shared by the menu and every game, so it's owned
# here rather than by any one game (see games/tetris/drawer.py, which used
# to build these itself back when it was the only thing running).
SINGLE_MATRIX_WIDTH = 8
MATRIX_HEIGHT = 32
MATRIX_DPIN = 18
NUM_OF_MATRICES = 5

BANNER_PANEL_WIDTH = 32
BANNER_PANEL_HEIGHT = 8
BANNER_DPIN = 13  # placeholder; unused until rpi banner support lands
SIZE_OF_BANNER = 2


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
    parser.add_argument(
        "--start-game", metavar="NAME", choices=[game_cls.NAME for game_cls in GAMES],
        default=None,
        help="skip the menu and go straight into this game (by name); "
             "default: start at the menu")
    return parser.parse_args()


def create_matrices(mode: str, num_of_matrices: int, banner_size: int):
    """The one board `Matrix`/banner `Matrix` pair for the whole process,
    shared by the menu and whichever game is currently active - hardware
    only gets initialized once, not once per game."""

    banner_dims = (BANNER_PANEL_HEIGHT, BANNER_PANEL_WIDTH * banner_size)
    matrix = create_matrix(
        mode, MATRIX_DPIN, SINGLE_MATRIX_WIDTH, MATRIX_HEIGHT, num_of_matrices,
        banner_dims=banner_dims)
    banner_matrix = create_banner_matrix(
        mode, BANNER_DPIN, BANNER_PANEL_WIDTH, BANNER_PANEL_HEIGHT, banner_size)
    return matrix, banner_matrix


def init_game(game: Game, key_handler: KeyHandler):
    game.start()
    key_handler.flush()
    # ENTER always does something (exit to menu, or - for the menu itself -
    # launch), even for a game that doesn't list it in its own USED_KEYS.
    key_handler.set_active_keys(game.USED_KEYS | {Key.ENTER})


PUMP_INTERVAL = 0.02


def _sleep(seconds: float, key_handler: KeyHandler):
    """Sleep in small slices, pumping the key handler between them so a
    backend that needs to service a GUI event loop (the simulator) stays
    responsive instead of freezing for the whole turn. While Key.PAUSE is
    toggled on, the deadline is pushed forward instead of counting down -
    the turn clock halts, but keys (including PAUSE itself, to unpause)
    keep being read every pump."""

    deadline = time() + seconds
    while (remaining := deadline - time()) > 0:
        key_handler.pump()
        if key_handler.is_toggled(Key.PAUSE):
            deadline += PUMP_INTERVAL
            sleep(PUMP_INTERVAL)
        else:
            sleep(min(PUMP_INTERVAL, remaining))


def game_loop(score_display, game: Game, key_handler: KeyHandler) -> bool:
    """Runs one round of `game`. Returns True if the player asked to
    restart the same game from its game-over screen (an arrow key), False
    if control should go back to the menu instead."""

    game.render()
    score_display.send_score(game.score, game.best_score)

    while not game.is_game_over():
        _sleep(game.turn_interval, key_handler)

        key = key_handler.get_key()
        if key == Key.ENTER and Key.ENTER not in game.USED_KEYS:
            return False  # a game that doesn't use ENTER itself exits to the menu

        game.advance_turn(key)
        game.render()
        score_display.send_score(game.score, game.best_score)

    return game.on_round_end(key_handler)


def main():
    args = parse_args()
    mode = args.mode

    matrix, banner_matrix = create_matrices(mode, args.num_of_matrices, args.size_of_banner)
    key_handler = create_key_handler(mode)
    menu = MenuGame(matrix, banner_matrix, key_handler)

    active = menu
    if args.start_game:
        game_cls = next(g for g in GAMES if g.NAME == args.start_game)
        active = game_cls(matrix, banner_matrix, key_handler)

    with create_score_display(mode) as score_display:
        while True:
            init_game(active, key_handler)
            restart = game_loop(score_display, active, key_handler)

            if active is menu:
                active = menu.selected_game_cls(matrix, banner_matrix, key_handler)
            elif not restart:
                active = menu
            # else: an arrow key on the game-over screen - keep playing
            # the same game, init_game() will start() it fresh next loop.


if __name__ == "__main__":
    main()
