import math
import pygame
from typing import Tuple, Optional
from .world import TileMap


class Player:
    """
    Player Avatar with crisp vector rendering and collision detection.
    """
    def __init__(self, x: float = 128.0, y: float = 128.0):
        self.x = x
        self.y = y
        self.width = 24
        self.height = 28
        self.speed = 3.2
        self.facing = "down"
        self.is_moving = False
        self.anim_frame = 0
        self.anim_timer = 0.0
        self.idle_timer = 0.0

    def update(self, keys, tilemap: TileMap, dt: float):
        dx, dy = 0.0, 0.0
        if keys[pygame.K_w] or keys[pygame.K_UP]:
            dy -= self.speed
            self.facing = "up"
        if keys[pygame.K_s] or keys[pygame.K_DOWN]:
            dy += self.speed
            self.facing = "down"
        if keys[pygame.K_a] or keys[pygame.K_LEFT]:
            dx -= self.speed
            self.facing = "left"
        if keys[pygame.K_d] or keys[pygame.K_RIGHT]:
            dx += self.speed
            self.facing = "right"

        self.is_moving = (dx != 0 or dy != 0)

        if self.is_moving:
            self.idle_timer = 0.0
            self.anim_timer += dt
            if self.anim_timer > 0.15:
                self.anim_frame = (self.anim_frame + 1) % 4
                self.anim_timer = 0.0

            # Collision check on X axis
            new_x = self.x + dx
            if not tilemap.is_solid(new_x, self.y) and not tilemap.is_solid(new_x + self.width, self.y + self.height):
                self.x = new_x

            # Collision check on Y axis
            new_y = self.y + dy
            if not tilemap.is_solid(self.x, new_y) and not tilemap.is_solid(self.x + self.width, new_y + self.height):
                self.y = new_y
        else:
            self.idle_timer += dt
            self.anim_frame = 0


class ArchivistDrone:
    """
    Archivist Mechanical Drone Entity.
    Crisp HD position tracking and smooth hover animation.
    """
    def __init__(self, x: float = 320.0, y: float = 160.0):
        self.x = x
        self.y = y
        self.target_x = x
        self.target_y = y
        self.hover_offset = 0.0
        self.time_counter = 0.0
        self.state_label = "MONITORING"
        self.facing_angle = 0.0

    def update(self, player: Player, trust_level: float, puzzle_active: bool, dt: float):
        self.time_counter += dt
        self.hover_offset = math.sin(self.time_counter * 3.0) * 5.0

        if puzzle_active:
            self.target_x = 19 * 32 - 32
            self.target_y = 2 * 32 + 16
            self.state_label = "GUARDING_GRID"
        elif trust_level < 40.0:
            self.target_x = 10.5 * 32
            self.target_y = 4.5 * 32
            self.state_label = "DEFENSIVE_LOCK"
        else:
            dist_to_player = math.hypot(player.x - self.x, player.y - self.y)
            if dist_to_player > 70.0:
                self.target_x = player.x + (70.0 if player.x < self.x else -70.0)
                self.target_y = player.y - 20.0
            self.state_label = "COMMUNICATION"

        self.x += (self.target_x - self.x) * 0.05
        self.y += (self.target_y - self.y) * 0.05
        self.facing_angle = math.atan2(player.y - self.y, player.x - self.x)
