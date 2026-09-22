from games.flappy import FlappyGame
from games.pong import PongGame
from games.snake import SnakeGame
from games.tetris import TetrisGame

# Explicit, no filesystem auto-discovery. This is the order the menu
# cycles through with LEFT/RIGHT.
GAMES = [TetrisGame, SnakeGame, PongGame, FlappyGame]
