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
        self.facing_right = True
        self.max_health = 100
        self.current_health = 100
        self.is_alive = True

    def update(self):
        if not self.is_alive:
            return

        self.x += self.vx
        self.rect.x = int(self.x)
        if self.x < self.min_x or self.x > self.max_x:
            self.vx *= -1
        self.facing_right = self.vx < 0

    def take_damage(self, amount):
        self.current_health -= amount
        if self.current_health <= 0:
            self.is_alive = False

    def draw(self, screen, camera_x, camera_y):
        if not self.is_alive:
            return

        screen_x = round(self.x - camera_x)
        screen_y = round(self.y - camera_y)

        if self.facing_right:
            screen.blit(enemy_image, (screen_x, screen_y))
        else:
            flipped_image = pygame.transform.flip(enemy_image, True, False)
            screen.blit(flipped_image, (screen_x, screen_y))

        # Draw health bar
        bar_width = ENEMY_WIDTH
        bar_height = 6
        health_ratio = self.current_health / self.max_health
        health_bar_bg = pygame.Rect(screen_x, screen_y - 10, bar_width, bar_height)
        health_bar_fg = pygame.Rect(screen_x, screen_y - 10, int(bar_width * health_ratio), bar_height)

        pygame.draw.rect(screen, (60, 60, 60), health_bar_bg)
        pygame.draw.rect(screen, (255, 0, 0), health_bar_fg)