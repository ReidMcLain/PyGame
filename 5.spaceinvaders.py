import pygame
import sys
import random

# Initialize Pygame
pygame.init()

# Constants
SCREEN_WIDTH = 600
SCREEN_HEIGHT = 800
PLAYER_WIDTH = 60
PLAYER_HEIGHT = 20
ENEMY_WIDTH = 40
ENEMY_HEIGHT = 30
BULLET_WIDTH = 5
BULLET_HEIGHT = 10
PLAYER_SPEED = 5
BULLET_SPEED = 11  # 1.5x faster than before
ENEMY_SPEED = 2
ENEMY_DROP = 30
ENEMY_ROWS = 5
ENEMY_COLS = 8
ENEMY_PADDING = 10

# Colors
BLACK = (0, 0, 0)
WHITE = (255, 255, 255)
GREEN = (0, 255, 0)
RED = (255, 0, 0)

# Setup screen
screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
pygame.display.set_caption("Space Invaders")
clock = pygame.time.Clock()
font = pygame.font.SysFont("monospace", 24)

# Player
player = pygame.Rect(SCREEN_WIDTH // 2 - PLAYER_WIDTH // 2, SCREEN_HEIGHT - 60, PLAYER_WIDTH, PLAYER_HEIGHT)

# Bullet
bullet = None

# Enemies
enemies = []
for row in range(ENEMY_ROWS):
    for col in range(ENEMY_COLS):
        x = col * (ENEMY_WIDTH + ENEMY_PADDING) + 50
        y = row * (ENEMY_HEIGHT + ENEMY_PADDING) + 50
        enemies.append(pygame.Rect(x, y, ENEMY_WIDTH, ENEMY_HEIGHT))

enemy_direction = 1  # 1 for right, -1 for left

# Score
score = 0
player_won = False  # New flag

# Game loop
running = True
game_over = False
while running:
    clock.tick(60)
    screen.fill(BLACK)

    # Event handling
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running = False
        if event.type == pygame.KEYDOWN:
            if game_over and event.key == pygame.K_r:
                # Restart game
                player.x = SCREEN_WIDTH // 2 - PLAYER_WIDTH // 2
                bullet = None
                enemies.clear()
                for row in range(ENEMY_ROWS):
                    for col in range(ENEMY_COLS):
                        x = col * (ENEMY_WIDTH + ENEMY_PADDING) + 50
                        y = row * (ENEMY_HEIGHT + ENEMY_PADDING) + 50
                        enemies.append(pygame.Rect(x, y, ENEMY_WIDTH, ENEMY_HEIGHT))
                enemy_direction = 1
                score = 0
                game_over = False
                player_won = False

    keys = pygame.key.get_pressed()
    if not game_over:
        # Player movement
        if keys[pygame.K_LEFT] and player.left > 0:
            player.x -= PLAYER_SPEED
        if keys[pygame.K_RIGHT] and player.right < SCREEN_WIDTH:
            player.x += PLAYER_SPEED

        # Bullet movement
        if keys[pygame.K_SPACE]:
            if bullet is None:
                bullet = pygame.Rect(player.centerx - BULLET_WIDTH // 2, player.top - BULLET_HEIGHT, BULLET_WIDTH, BULLET_HEIGHT)

        if bullet:
            bullet.y -= BULLET_SPEED
            if bullet.bottom < 0:
                bullet = None

        # Enemy movement
        move_down = False
        for enemy in enemies:
            enemy.x += ENEMY_SPEED * enemy_direction
            if enemy.right >= SCREEN_WIDTH or enemy.left <= 0:
                move_down = True

        if move_down:
            enemy_direction *= -1
            for enemy in enemies:
                enemy.y += ENEMY_DROP

        # Check bullet collision
        if bullet:
            for enemy in enemies:
                if bullet.colliderect(enemy):
                    enemies.remove(enemy)
                    bullet = None
                    score += 1
                    break

        # Check game over (loss)
        for enemy in enemies:
            if enemy.bottom >= player.top:
                game_over = True
                player_won = False
                break

        # Check game over (win)
        if not enemies:
            game_over = True
            player_won = True

    # Draw player
    pygame.draw.rect(screen, GREEN, player)

    # Draw bullet
    if bullet:
        pygame.draw.rect(screen, RED, bullet)

    # Draw enemies
    for enemy in enemies:
        pygame.draw.rect(screen, WHITE, enemy)

    # Draw score
    score_text = font.render(f"Score: {score}", True, WHITE)
    screen.blit(score_text, (10, 10))

    # Draw game over or win text
    if game_over:
        if player_won:
            text1 = font.render("You Win!", True, WHITE)
        else:
            text1 = font.render("Game Over!", True, WHITE)
        text2 = font.render("Press R to Restart", True, WHITE)
        screen.blit(text1, (SCREEN_WIDTH // 2 - text1.get_width() // 2, SCREEN_HEIGHT // 2 - 30))
        screen.blit(text2, (SCREEN_WIDTH // 2 - text2.get_width() // 2, SCREEN_HEIGHT // 2 + 10))

    pygame.display.flip()

pygame.quit()
sys.exit()