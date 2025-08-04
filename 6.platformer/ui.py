import pygame
from assets import heart_full, heart_empty, HEART_SIZE
from settings import SCREEN_WIDTH, WHITE

def draw_hearts(screen, player_health, max_health):
    for i in range(max_health):  # Draw up to currently unlocked max
        x = 10 + i * (HEART_SIZE + 10)
        y = 10
        heart = heart_full if i < player_health else heart_empty
        screen.blit(heart, (x, y))

def draw_prompt(screen, font, text, world_x, world_y, camera_x, camera_y):
    label = font.render(text, True, (255, 255, 255))
    x = world_x - camera_x + 40 - label.get_width() // 2
    y = world_y - camera_y - 20
    screen.blit(label, (x, y))

def draw_game_outcome(screen, font_big, font_small, player_won):
    overlay_band = pygame.Surface((SCREEN_WIDTH, 100))
    overlay_band.set_alpha(200)
    overlay_band.fill((0, 0, 0))

    band_rect = overlay_band.get_rect(center=(SCREEN_WIDTH // 2, 120))
    screen.blit(overlay_band, band_rect)

    message = "GREAT ENEMY FELLED" if player_won else "YOU DIED"
    text = font_big.render(message, True, (255, 0, 0))
    text_rect = text.get_rect(center=band_rect.center)

    for dx, dy in [(-2, 0), (2, 0), (0, -2), (0, 2)]:
        shadow = font_big.render(message, True, (0, 0, 0))
        screen.blit(shadow, text_rect.move(dx, dy))

    screen.blit(text, text_rect)