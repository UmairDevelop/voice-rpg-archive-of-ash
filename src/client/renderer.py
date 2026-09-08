import math
import pygame
from typing import Tuple
from .world import TileMap
from .entities import Player, ArchivistDrone


class RetroRenderer:
    """
    Crisp HD Vector-Pixel Renderer.
    Renders high-contrast tiles, sharp outlines, detailed entities, and clean HUD.
    """
    # High-Contrast Crisp Palette
    COLOR_BG = (12, 14, 20)
    COLOR_WALL = (45, 52, 68)
    COLOR_WALL_OUTLINE = (70, 80, 105)
    COLOR_FLOOR = (28, 33, 44)
    COLOR_FLOOR_GRID = (38, 44, 58)
    COLOR_PLAYER = (50, 220, 130)
    COLOR_PLAYER_OUTLINE = (20, 100, 50)
    COLOR_DRONE = (255, 190, 40)
    COLOR_DRONE_OUTLINE = (160, 110, 10)
    COLOR_VAULT_SEALED = (230, 50, 50)
    COLOR_VAULT_CRACKED = (255, 170, 30)
    COLOR_VAULT_OPEN = (50, 230, 110)
    COLOR_TERMINAL = (30, 160, 240)
    COLOR_CONSOLE = (240, 130, 30)
    COLOR_AMBER = (255, 180, 0)
    COLOR_WHITE = (255, 255, 255)

    def __init__(self, resolution: Tuple[int, int] = (768, 416)):
        self.width, self.height = resolution
        self.surface = pygame.Surface(resolution)
        self.enable_crt_scanlines = False  # Disabled by default for maximum graphic clarity!

        # Optional clean scanline surface
        self.scanline_surface = pygame.Surface(resolution, pygame.SRCALPHA)
        for y in range(0, self.height, 4):
            pygame.draw.line(self.scanline_surface, (0, 0, 0, 20), (0, y), (self.width, y))

    def render_scene(
        self,
        tilemap: TileMap,
        player: Player,
        drone: ArchivistDrone,
        vault_state: str,
        trust_level: float,
        status_label: str = "IDLE",
        idle_hint_target: Tuple[float, float] = None
    ) -> pygame.Surface:
        self.surface.fill(self.COLOR_BG)

        # 1. Render High-Definition Crisp TileMap
        for r in range(tilemap.rows):
            for c in range(tilemap.cols):
                tile = tilemap.get_tile(c, r)
                rect = (c * tilemap.TILE_SIZE, r * tilemap.TILE_SIZE, tilemap.TILE_SIZE, tilemap.TILE_SIZE)
                
                if tile == 1:  # Wall
                    pygame.draw.rect(self.surface, self.COLOR_WALL, rect)
                    pygame.draw.rect(self.surface, self.COLOR_WALL_OUTLINE, rect, 2)
                    # Metallic texture accent
                    pygame.draw.line(self.surface, (85, 95, 120), (rect[0]+4, rect[1]+4), (rect[0]+28, rect[1]+4), 2)
                
                elif tile == 0:  # Floor
                    pygame.draw.rect(self.surface, self.COLOR_FLOOR, rect)
                    pygame.draw.rect(self.surface, self.COLOR_FLOOR_GRID, rect, 1)
                
                elif tile == 4:  # Terminal
                    pygame.draw.rect(self.surface, self.COLOR_FLOOR, rect)
                    pygame.draw.rect(self.surface, self.COLOR_TERMINAL, (rect[0]+4, rect[1]+4, 24, 24))
                    pygame.draw.rect(self.surface, (255, 255, 255), (rect[0]+4, rect[1]+4, 24, 24), 2)
                    # Terminal screen glow
                    pygame.draw.rect(self.surface, (150, 230, 255), (rect[0]+8, rect[1]+8, 16, 12))
                
                elif tile == 3:  # Power Console
                    pygame.draw.rect(self.surface, self.COLOR_FLOOR, rect)
                    pygame.draw.rect(self.surface, self.COLOR_CONSOLE, (rect[0]+4, rect[1]+4, 24, 24))
                    pygame.draw.rect(self.surface, (255, 255, 255), (rect[0]+4, rect[1]+4, 24, 24), 2)
                    # Gauges
                    pygame.draw.rect(self.surface, (255, 200, 50), (rect[0]+8, rect[1]+8, 16, 6))

                elif tile == 2:  # Vault Door
                    door_color = self.COLOR_VAULT_SEALED
                    if vault_state == "CRACKED":
                        door_color = self.COLOR_VAULT_CRACKED
                    elif vault_state == "OPEN":
                        door_color = self.COLOR_VAULT_OPEN
                    
                    pygame.draw.rect(self.surface, door_color, rect)
                    pygame.draw.rect(self.surface, (255, 255, 255), rect, 3)
                    # Door bolts
                    pygame.draw.circle(self.surface, (255, 255, 255), (rect[0]+8, rect[1]+16), 4)
                    pygame.draw.circle(self.surface, (255, 255, 255), (rect[0]+24, rect[1]+16), 4)

        # 2. Render Navigation Arrow when idle > 3s
        if player.idle_timer > 3.0 and idle_hint_target:
            tx, ty = idle_hint_target
            px, py = player.x + 12, player.y + 14
            angle = math.atan2(ty - py, tx - px)
            ix = px + math.cos(angle) * 32
            iy = py + math.sin(angle) * 32
            pygame.draw.circle(self.surface, self.COLOR_AMBER, (int(ix), int(iy)), 6)
            pygame.draw.circle(self.surface, (255, 255, 255), (int(ix), int(iy)), 7, 2)

        # 3. Render Player Sprite (Crisp HD Box Avatar)
        player_rect = (int(player.x), int(player.y), player.width, player.height)
        pygame.draw.rect(self.surface, self.COLOR_PLAYER, player_rect)
        pygame.draw.rect(self.surface, self.COLOR_PLAYER_OUTLINE, player_rect, 2)
        # Visor
        pygame.draw.rect(self.surface, (255, 255, 255), (int(player.x)+4, int(player.y)+4, 16, 6))

        # 4. Render Archivist Drone
        drone_y = int(drone.y + drone.hover_offset)
        drone_pos = (int(drone.x), drone_y)
        pygame.draw.circle(self.surface, self.COLOR_DRONE, drone_pos, 14)
        pygame.draw.circle(self.surface, self.COLOR_DRONE_OUTLINE, drone_pos, 15, 3)
        # Eye sensor
        eye_x = int(drone.x + math.cos(drone.facing_angle) * 8)
        eye_y = int(drone_y + math.sin(drone.facing_angle) * 8)
        pygame.draw.circle(self.surface, (255, 40, 40), (eye_x, eye_y), 4)
        pygame.draw.circle(self.surface, (255, 255, 255), (eye_x, eye_y), 5, 1)

        # Status mode indicator above drone
        if status_label in ["THINKING", "MODEL_GENERATING"]:
            pygame.draw.circle(self.surface, (100, 200, 255), (int(drone.x), drone_y - 24), 6)
            pygame.draw.circle(self.surface, (255, 255, 255), (int(drone.x), drone_y - 24), 7, 1)
        elif status_label in ["SPEAKING"]:
            pygame.draw.circle(self.surface, (80, 240, 120), (int(drone.x), drone_y - 24), 6)
            pygame.draw.circle(self.surface, (255, 255, 255), (int(drone.x), drone_y - 24), 7, 1)
        elif status_label in ["LISTENING", "RECORDING"]:
            pygame.draw.circle(self.surface, (255, 80, 80), (int(drone.x), drone_y - 24), 6)
            pygame.draw.circle(self.surface, (255, 255, 255), (int(drone.x), drone_y - 24), 7, 1)

        # 5. Optional CRT scanlines (Only if enabled)
        if self.enable_crt_scanlines:
            self.surface.blit(self.scanline_surface, (0, 0))

        return self.surface
