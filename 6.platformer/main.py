import pygame
import sys

# ✅ Initialize display FIRST to avoid convert_alpha() crash
pygame.init()
screen = pygame.display.set_mode((600, 400))
pygame.display.set_caption("Scrolling Platformer")

# ✅ Now it's safe to import assets
from assets import (
    heart_full,
    heart_empty,
    HEART_SIZE,
    background_image,
    sword_image,
    SWORD_SIZE
)
from platforms import platforms
from enemy import Enemy
from player import Player
from settings import *

def main():
    clock = pygame.time.Clock()
    font_big = pygame.font.SysFont("monospace", 48)
    font_small = pygame.font.SysFont("monospace", 24)
    font_prompt = pygame.font.SysFont("monospace", 18, bold=True)

    player = Player()
    enemy = Enemy(1000, 200)

    # Sword position — left side of top horizontal bar (platforms[9])
    sword_platform_index = 9
    sword_world_x = platforms[sword_platform_index].left - 900
    sword_world_y = platforms[sword_platform_index].y - (SWORD_SIZE * 2)
    sword_rect = pygame.Rect(sword_world_x, sword_world_y, SWORD_SIZE * 2, SWORD_SIZE * 2)

    # Player sword state
    player.has_sword = False
    player.sword_angle = 0
    player.swing_timer = 0
    player.has_hit_enemy_this_swing = False

    camera_x = 0
    camera_y = 0
    running = True
    game_over = False
    player_won = False

    PARALLAX_FACTOR = 0.2

    while running:
        clock.tick(60)
        screen.fill(WHITE)

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
            if game_over and event.type == pygame.KEYDOWN:
                if event.key == pygame.K_r:
                    # Reset player
                    player.health = MAX_HEALTH
                    player.x = LEVEL_WIDTH - PLAYER_WIDTH - 20
                    player.y = LEVEL_HEIGHT - PLAYER_HEIGHT - 10
                    player.vx = 0
                    player.vy = 0
                    player.has_sword = False
                    player.sword_angle = 0
                    player.swing_timer = 0
                    player.has_hit_enemy_this_swing = False

                    # Reset enemy
                    enemy.x = 1000
                    enemy.y = 200 - ENEMY_HEIGHT
                    enemy.vx = 2
                    enemy.current_health = enemy.max_health
                    enemy.is_alive = True

                    game_over = False

        if not game_over:
            keys = pygame.key.get_pressed()
            player.handle_input(keys)
            player.update(platforms, [enemy])
            enemy.update()

            # Sword pickup
            if keys[pygame.K_e] and not player.has_sword:
                if player.rect.colliderect(sword_rect):
                    player.has_sword = True

            # Sword swing
            if keys[pygame.K_e] and player.has_sword and player.swing_timer == 0:
                player.sword_angle = 45
                player.swing_timer = 15
                player.has_hit_enemy_this_swing = False  # Reset per swing

            # Animate sword swing
            if player.has_sword and player.swing_timer > 0:
                player.swing_timer -= 1
                if player.swing_timer == 10:
                    player.sword_angle = 90
                elif player.swing_timer == 5:
                    player.sword_angle = 45
                elif player.swing_timer == 0:
                    player.sword_angle = 0
                    player.has_hit_enemy_this_swing = False

            if player.health <= 0:
                game_over = True
                player_won = False

            if enemy.current_health <= 0 and not game_over:
                game_over = True
                player_won = True
                enemy.is_alive = False

        camera_x = round(player.x - SCREEN_WIDTH // 2)
        camera_y = round(player.y - SCREEN_HEIGHT // 2)

        background_x = camera_x * PARALLAX_FACTOR
        background_x = max(0, min(background_x, background_image.get_width() - SCREEN_WIDTH))
        screen.blit(background_image, (-background_x, 0))

        for platform in platforms:
            pygame.draw.rect(screen, GREEN, (platform.x - camera_x, platform.y - camera_y, platform.width, platform.height))

        # Draw sword and prompt if not picked up
        if not player.has_sword:
            screen.blit(sword_image, (sword_rect.x - camera_x, sword_rect.y - camera_y))

            # Floating [E] prompt
            prompt_text = font_prompt.render("[E]", True, (255, 255, 255))
            text_x = sword_rect.x - camera_x + SWORD_SIZE - prompt_text.get_width() // 2
            text_y = sword_rect.y - camera_y - 20
            screen.blit(prompt_text, (text_x, text_y))

        # Draw enemy
        enemy.draw(screen, camera_x, camera_y)

        # Draw player
        player.draw(screen, camera_x, camera_y)

        # Draw sword on player
        if player.has_sword:
            if player.facing_right:
                sword_img = sword_image
                offset_x = 20
            else:
                sword_img = pygame.transform.flip(sword_image, True, False)
                offset_x = -20

            sword_img_final = sword_img
            if not player.facing_right:
                sword_img_final = pygame.transform.flip(sword_img, True, False)

            swing_angle = player.sword_angle if player.facing_right else -player.sword_angle
            sword_rotated = pygame.transform.rotate(sword_img_final, -swing_angle)
            sword_rect_draw = sword_rotated.get_rect(center=(player.rect.centerx - camera_x + offset_x,
                                                             player.rect.centery - 20 - camera_y))
            screen.blit(sword_rotated, sword_rect_draw)

            # Sword damage logic
            sword_world_rect = sword_rect_draw.move(camera_x, camera_y)
            if player.swing_timer > 0 and enemy.is_alive and not player.has_hit_enemy_this_swing:
                if sword_world_rect.colliderect(enemy.rect):
                    enemy.take_damage(10)
                    player.has_hit_enemy_this_swing = True

        # Draw hearts
        for i in range(MAX_HEALTH):
            x = 10 + i * (HEART_SIZE + 10)
            y = 10
            if i < player.health:
                screen.blit(heart_full, (x, y))
            else:
                screen.blit(heart_empty, (x, y))

        # Game Over UI (Victory or Defeat)
        if game_over:
            overlay_band = pygame.Surface((SCREEN_WIDTH, 100))
            overlay_band.set_alpha(200)
            overlay_band.fill((0, 0, 0))
            band_rect = overlay_band.get_rect(center=(SCREEN_WIDTH // 2, SCREEN_HEIGHT // 2))
            screen.blit(overlay_band, band_rect)

            outcome_msg = "GREAT ENEMY FELLED" if player_won else "YOU DIED"
            outcome_color = (255, 0, 0)

            text = font_big.render(outcome_msg, True, outcome_color)
            text_rect = text.get_rect(center=(SCREEN_WIDTH // 2, SCREEN_HEIGHT // 2))

            offsets = [(-2, 0), (2, 0), (0, -2), (0, 2)]
            for ox, oy in offsets:
                outline = font_big.render(outcome_msg, True, (0, 0, 0))
                outline_rect = outline.get_rect(center=(text_rect.centerx + ox, text_rect.centery + oy))
                screen.blit(outline, outline_rect)
            screen.blit(text, text_rect)

            restart_text = font_small.render("Press R to Restart", True, WHITE)
            restart_rect = restart_text.get_rect(center=(SCREEN_WIDTH // 2, SCREEN_HEIGHT // 2 + 40))
            for ox, oy in offsets:
                outline = font_small.render("Press R to Restart", True, (0, 0, 0))
                outline_rect = outline.get_rect(center=(restart_rect.centerx + ox, restart_rect.centery + oy))
                screen.blit(outline, outline_rect)
            screen.blit(restart_text, restart_rect)

        pygame.display.flip()

    pygame.quit()
    sys.exit()

if __name__ == "__main__":
    main()