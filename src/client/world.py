import pygame
from typing import List, Tuple, Dict, Any, Optional


class TileMap:
    """
    2D Crisp HD Tilemap representation for the 2-room Archive of Ash chamber:
    Room 1: Entrance Airlock & Terminal
    Room 2: Core Vault Chamber, Power Console, Vault Door
    """
    TILE_SIZE = 32

    # 0 = Floor, 1 = Wall, 2 = Vault Door, 3 = Power Console, 4 = Terminal
    MAP_DATA = [
        [1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1],
        [1, 0, 0, 0, 0, 1, 1, 0, 0, 0, 0, 0, 0, 0, 0, 0, 1, 1, 0, 0, 0, 0, 0, 1],
        [1, 0, 4, 0, 0, 1, 1, 0, 0, 0, 0, 0, 0, 0, 0, 0, 1, 1, 0, 3, 0, 0, 0, 1],
        [1, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 1],
        [1, 0, 0, 0, 0, 1, 1, 0, 0, 0, 0, 0, 0, 0, 0, 0, 1, 1, 0, 0, 0, 0, 0, 1],
        [1, 1, 1, 0, 1, 1, 1, 1, 1, 1, 2, 2, 1, 1, 1, 1, 1, 1, 1, 1, 0, 1, 1, 1],
        [1, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 1],
        [1, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 1],
        [1, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 1],
        [1, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 1],
        [1, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 1],
        [1, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 1],
        [1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1],
    ]

    def __init__(self):
        self.cols = len(self.MAP_DATA[0])
        self.rows = len(self.MAP_DATA)
        self.width = self.cols * self.TILE_SIZE
        self.height = self.rows * self.TILE_SIZE

    def get_tile(self, col: int, row: int) -> int:
        if 0 <= row < self.rows and 0 <= col < self.cols:
            return self.MAP_DATA[row][col]
        return 1

    def is_solid(self, x: float, y: float) -> bool:
        col = int(x // self.TILE_SIZE)
        row = int(y // self.TILE_SIZE)
        tile = self.get_tile(col, row)
        return tile == 1 or tile == 2

    def get_interactable(self, x: float, y: float, radius: float = 48.0) -> Optional[str]:
        # Terminal (col 2, row 2)
        if abs(x - (2 * 32 + 16)) < radius and abs(y - (2 * 32 + 16)) < radius:
            return "terminal"
        # Power Console (col 19, row 2)
        if abs(x - (19 * 32 + 16)) < radius and abs(y - (2 * 32 + 16)) < radius:
            return "power_console"
        # Vault Door (col 10-11, row 5)
        if abs(x - (10.5 * 32)) < radius and abs(y - (5 * 32)) < radius:
            return "vault_door"
        return None
