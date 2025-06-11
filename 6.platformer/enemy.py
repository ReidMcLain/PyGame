# enemy.py
import pygame
from settings import *
from assets import enemy_image, ENEMY_WIDTH, ENEMY_HEIGHT

class Enemy:
    def __init__(self, x, y):
        self.x = x
        self.y = y - ENEMY_HEIGHT
        self.vx = 2
        self.min_x = x - 100
        self.max_x = x + 100
        self.rect = pygame.Rect(self.x, self.y, ENEMY_WIDTH, ENEMY_HEIGHT)
        self.facing_right = True  # Initially facing right

    def update(self):
        self.x += self.vx
        self.rect.x = int(self.x)
        if self.x < self.min_x or self.x > self.max_x:
            self.vx *= -1
        # Always flip to face away from center:
        if self.vx > 0:
            self.facing_right = False  # Moving right, face left
        else:
            self.facing_right = True   # Moving left, face right

    def draw(self, screen, camera_x, camera_y):
        if self.facing_right:
            screen.blit(enemy_image, (round(self.x - camera_x), round(self.y - camera_y)))
        else:
            flipped_image = pygame.transform.flip(enemy_image, True, False)
            screen.blit(flipped_image, (round(self.x - camera_x), round(self.y - camera_y)))