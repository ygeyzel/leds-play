from games.tetris import TetrisGame

# Explicit, no filesystem auto-discovery. Order will matter once a
# game-selection launcher exists (STATUS.md); for now `main.py` just runs
# GAMES[0].
GAMES = [TetrisGame]
