# assets.py
import pygame
from settings import (
    PLAYER_WIDTH,
    PLAYER_HEIGHT,
    ENEMY_WIDTH,
    ENEMY_HEIGHT,
    HEART_SIZE,
    SCREEN_WIDTH,
    SCREEN_HEIGHT,
    LEVEL_WIDTH
)

# Player Images
player_image_original = pygame.image.load("assets/player.png").convert_alpha()
player_image_original = pygame.transform.scale(player_image_original, (PLAYER_WIDTH, PLAYER_HEIGHT))
player_image_flipped = pygame.transform.flip(player_image_original, True, False)

# Enemy Images
enemy_image = pygame.image.load("assets/patrol.png").convert_alpha()
enemy_image = pygame.transform.scale(enemy_image, (ENEMY_WIDTH, ENEMY_HEIGHT))

# Heart Images
heart_full = pygame.image.load("assets/heart.png").convert_alpha()
heart_full = pygame.transform.scale(heart_full, (HEART_SIZE, HEART_SIZE))
heart_empty = pygame.image.load("assets/heart_empty.png").convert_alpha()
heart_empty = pygame.transform.scale(heart_empty, (HEART_SIZE, HEART_SIZE))

# Background Image
background_image = pygame.image.load("assets/rpgbackground.png").convert()
background_image = pygame.transform.scale(background_image, (LEVEL_WIDTH, SCREEN_HEIGHT))

# Sword Image
sword_image = pygame.image.load("assets/rpgsword.png").convert_alpha()
SWORD_SIZE = 40  # original size
sword_image = pygame.transform.scale(sword_image, (SWORD_SIZE * 2, SWORD_SIZE * 2))  # double the size