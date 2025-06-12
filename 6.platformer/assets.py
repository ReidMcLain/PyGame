import os
import sys
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

# ✅ Handle both PyInstaller and dev environments
BASE_DIR = getattr(sys, '_MEIPASS', os.path.abspath("."))

def load_image(path, scale=None, convert_alpha=True):
    full_path = os.path.join(BASE_DIR, path)
    image = pygame.image.load(full_path)
    image = image.convert_alpha() if convert_alpha else image.convert()
    return pygame.transform.scale(image, scale) if scale else image

# Player Images
player_image_original = load_image("assets/player.png", (PLAYER_WIDTH, PLAYER_HEIGHT))
player_image_flipped = pygame.transform.flip(player_image_original, True, False)

# Enemy Images
enemy_image = load_image("assets/patrol.png", (ENEMY_WIDTH, ENEMY_HEIGHT))

# Heart Images
heart_full = load_image("assets/heart.png", (HEART_SIZE, HEART_SIZE))
heart_empty = load_image("assets/heart_empty.png", (HEART_SIZE, HEART_SIZE))

# Background Image
background_image = load_image("assets/rpgbackground.png", (LEVEL_WIDTH, SCREEN_HEIGHT), convert_alpha=False)

# Sword Image
SWORD_SIZE = 40  # original size
sword_image = load_image("assets/rpgsword.png", (SWORD_SIZE * 2, SWORD_SIZE * 2))