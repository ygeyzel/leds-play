from time import sleep, time
from game.drawer import Drawer
from game.game_board import Board
from hardware.keys import Key, KeyHandler
from hardware.score import ScoreDisplay, with_score_display


key_handler = KeyHandler()


def init_game(board: Board):
    board.start()
    key_handler.flush()


def game_over(drawer: Drawer):
    key_handler.flush()
    end_time = time()
    
    while key_handler.get_key() == Key.NO_KEY or time() - end_time < 2:
        drawer.blink_board()
        sleep(0.2)


def game_loop(score_display: ScoreDisplay, board: Board, drawer: Drawer):
    drawer.draw_board()

    while not board.is_game_over():
        dt = 1 / board.level
        sleep(dt)

        key = key_handler.get_key()
        board.advance_turn(key)

        drawer.clear()
        drawer.draw_board()
        score_display.send_score(board.score, board.best_score)

    game_over(drawer)


@with_score_display
def main(score_display: ScoreDisplay):
    drawer = Drawer()
    board = drawer.board
    board.burn_animation = drawer.burn_animation

    while True:
        init_game(board)
        game_loop(score_display, board, drawer)


if __name__ == "__main__":
    main()
