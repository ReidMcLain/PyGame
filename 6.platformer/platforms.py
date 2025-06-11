# platforms.py
import pygame
from settings import LEVEL_WIDTH, LEVEL_HEIGHT

platforms = [
    pygame.Rect(0, LEVEL_HEIGHT - 10, LEVEL_WIDTH, 10),
    pygame.Rect(100, 1100, 200, 10),
    pygame.Rect(400, 1000, 150, 10),
    pygame.Rect(700, 950, 200, 10),
    pygame.Rect(1000, 900, 150, 10),
    pygame.Rect(200, 800, 200, 10),
    pygame.Rect(600, 700, 200, 10),
    pygame.Rect(900, 600, 200, 10),
    pygame.Rect(1200, 500, 200, 10),
    pygame.Rect(300, 200, 1800, 10),
    pygame.Rect(2100, 200, 600, 10),
    pygame.Rect(-600, 200, 600, 10),
    pygame.Rect(200, 300, 100, 10),
    pygame.Rect(150, 400, 100, 10),
    pygame.Rect(100, 500, 100, 10),
    pygame.Rect(500, 600, 150, 10),
    pygame.Rect(0, 200, 10, LEVEL_HEIGHT - 210),
    pygame.Rect(LEVEL_WIDTH - 10, 210, 10, LEVEL_HEIGHT - 210)
]