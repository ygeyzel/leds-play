from games.snake import SnakeGame
from games.tetris import TetrisGame

# Explicit, no filesystem auto-discovery. This is the order the menu
# cycles through with LEFT/RIGHT.
GAMES = [TetrisGame, SnakeGame]
