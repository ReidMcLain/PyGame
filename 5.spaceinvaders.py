import pygame
import sys
import random
import math

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
BULLET_SPEED = 11
ENEMY_SPEED = 2
ENEMY_DROP = 30
ENEMY_ROWS = 5
ENEMY_COLS = 8
ENEMY_PADDING = 10

ITEM_SIZE = 20
ITEM_COLOR = (255, 255, 0)
ITEM_DROP_INTERVAL = 600  # frames (10 seconds)
ATTACK_BOOST_DURATION = 30 * 60  # 30 seconds
BULLET_SPREAD_ANGLE = math.radians(15)

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

# Bullets
bullet = None

# Enemies
enemies = []
for row in range(ENEMY_ROWS):
    for col in range(ENEMY_COLS):
        x = col * (ENEMY_WIDTH + ENEMY_PADDING) + 50
        y = row * (ENEMY_HEIGHT + ENEMY_PADDING) + 50
        enemies.append(pygame.Rect(x, y, ENEMY_WIDTH, ENEMY_HEIGHT))

enemy_direction = 1  # 1 for right, -1 for left

# Score and game state
score = 0
player_won = False
running = True
game_over = False

# Item drop
item = None
item_flash_counter = 0
item_timer = 0

# Attack boost
attack_boost_timer = 0

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
                attack_boost_timer = 0

    keys = pygame.key.get_pressed()
    if not game_over:
        # Player movement
        if keys[pygame.K_LEFT] and player.left > 0:
            player.x -= PLAYER_SPEED
        if keys[pygame.K_RIGHT] and player.right < SCREEN_WIDTH:
            player.x += PLAYER_SPEED

        # Bullet firing
        if keys[pygame.K_SPACE]:
            if bullet is None:
                bullet = [pygame.Rect(player.centerx - BULLET_WIDTH // 2, player.top - BULLET_HEIGHT, BULLET_WIDTH, BULLET_HEIGHT)]
                if attack_boost_timer > 0:
                    spread_vx = BULLET_SPEED * 3 * math.tan(BULLET_SPREAD_ANGLE)
                    bullet.append({
                        'rect': pygame.Rect(player.centerx - BULLET_WIDTH // 2, player.top - BULLET_HEIGHT, BULLET_WIDTH, BULLET_HEIGHT),
                        'vx': spread_vx,
                        'vy': -BULLET_SPEED * 3
                    })
                    bullet.append({
                        'rect': pygame.Rect(player.centerx - BULLET_WIDTH // 2, player.top - BULLET_HEIGHT, BULLET_WIDTH, BULLET_HEIGHT),
                        'vx': -spread_vx,
                        'vy': -BULLET_SPEED * 3
                    })

        # Bullet movement
        if bullet:
            if isinstance(bullet, list):
                to_remove = []
                for b in bullet:
                    if isinstance(b, pygame.Rect):
                        b.y -= BULLET_SPEED * (2 if attack_boost_timer > 0 else 1)
                        if b.bottom < 0:
                            to_remove.append(b)
                    else:
                        b['rect'].x += b['vx']
                        b['rect'].y += b['vy']
                        if (b['rect'].bottom < 0 or b['rect'].left < 0 or b['rect'].right > SCREEN_WIDTH):
                            to_remove.append(b)
                for b in to_remove:
                    bullet.remove(b)
                if not bullet:
                    bullet = None
            else:
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

        # Bullet collision
        if bullet:
            if isinstance(bullet, list):
                to_remove = []
                for b in bullet:
                    r = b if isinstance(b, pygame.Rect) else b['rect']
                    for enemy in enemies:
                        if r.colliderect(enemy):
                            enemies.remove(enemy)
                            to_remove.append(b)
                            score += 1
                            break
                for b in to_remove:
                    bullet.remove(b)
                if not bullet:
                    bullet = None
            else:
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

        # Attack boost timer
        if attack_boost_timer > 0:
            attack_boost_timer -= 1

        # Item drop logic
        item_timer += 1
        if item_timer >= ITEM_DROP_INTERVAL and item is None:
            item_x = random.randint(50, SCREEN_WIDTH - 50)
            item = pygame.Rect(item_x, 0, ITEM_SIZE, ITEM_SIZE)
            item_timer = 0

        # Move item downward
        if item:
            item.y += 2
            if item.top > SCREEN_HEIGHT:
                item = None

        # Pickup item
        if keys[pygame.K_e] and item:
            if abs(player.centerx - item.centerx) < 60 and abs(player.centery - item.centery) < 60:
                attack_boost_timer = ATTACK_BOOST_DURATION
                item = None

    # Draw player
    pygame.draw.rect(screen, GREEN, player)

    # Draw bullets
    if bullet:
        if isinstance(bullet, list):
            for b in bullet:
                r = b if isinstance(b, pygame.Rect) else b['rect']
                pygame.draw.rect(screen, RED, r)
        else:
            pygame.draw.rect(screen, RED, bullet)

    # Draw enemies
    for enemy in enemies:
        pygame.draw.rect(screen, WHITE, enemy)

    # Draw item
    if item:
        item_flash_counter = (item_flash_counter + 1) % 60
        if item_flash_counter < 30:
            pygame.draw.rect(screen, ITEM_COLOR, item)

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