import pygame
import sys

# Initialize PyGame
pygame.init()

# Constants
SCREEN_WIDTH = 600
SCREEN_HEIGHT = 800
PADDLE_WIDTH = 100
PADDLE_HEIGHT = 20
BALL_RADIUS = 10
BLOCK_HEIGHT = 30
ROWS = 5
COLS = 10
BLOCK_SPACING = 5  # horizontal spacing between blocks

# Calculate block width and total spacing
total_horizontal_spacing = (COLS - 1) * BLOCK_SPACING
BLOCK_WIDTH = (SCREEN_WIDTH - total_horizontal_spacing) // COLS

# Colors
WHITE = (255,255,255)
BLACK = (0,0,0)
BLUE = (0,0,255)
RED = (255,0,0)

# Print the file name for good debugging habits!
print("Running: breakout.py")

# Initialize screen
screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
pygame.display.set_caption("Breakout")
clock = pygame.time.Clock()

# Paddle
paddle = pygame.Rect(SCREEN_WIDTH//2 - PADDLE_WIDTH//2, SCREEN_HEIGHT - 40, PADDLE_WIDTH, PADDLE_HEIGHT)

# Ball
ball = pygame.Rect(SCREEN_WIDTH//2 - BALL_RADIUS, SCREEN_HEIGHT//2, BALL_RADIUS*2, BALL_RADIUS*2)
ball_dx = 4
ball_dy = -4

# Blocks
blocks = []
for row in range(ROWS):
    for col in range(COLS):
        block_x = col * (BLOCK_WIDTH + BLOCK_SPACING)
        block_y = row * (BLOCK_HEIGHT + 5) + 50
        block = pygame.Rect(block_x, block_y, BLOCK_WIDTH, BLOCK_HEIGHT)
        blocks.append(block)

# Font for messages
font = pygame.font.SysFont("monospace", 50)

# Game loop
running = True
while running:
    clock.tick(60)  # 60 FPS
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running = False

    # Move paddle
    keys = pygame.key.get_pressed()
    if keys[pygame.K_LEFT] and paddle.left > 0:
        paddle.move_ip(-6, 0)
    if keys[pygame.K_RIGHT] and paddle.right < SCREEN_WIDTH:
        paddle.move_ip(6, 0)

    # Move ball
    ball.x += ball_dx
    ball.y += ball_dy

    # Ball collision with walls
    if ball.left <= 0 or ball.right >= SCREEN_WIDTH:
        ball_dx = -ball_dx
    if ball.top <= 0:
        ball_dy = -ball_dy
    if ball.bottom >= SCREEN_HEIGHT:
        # Game Over
        text = font.render("Game Over!", True, WHITE)
        screen.blit(text, (SCREEN_WIDTH//4, SCREEN_HEIGHT//2))
        pygame.display.update()
        pygame.time.delay(3000)
        running = False

    # Ball collision with paddle
    if ball.colliderect(paddle):
        ball_dy = -ball_dy

    # Ball collision with blocks
    hit_index = ball.collidelist(blocks)
    if hit_index != -1:
        hit_block = blocks.pop(hit_index)
        ball_dy = -ball_dy

        # Check win
        if not blocks:
            text = font.render("You Win!", True, WHITE)
            screen.blit(text, (SCREEN_WIDTH//4, SCREEN_HEIGHT//2))
            pygame.display.update()
            pygame.time.delay(3000)
            running = False

    # Draw everything
    screen.fill(BLACK)
    pygame.draw.rect(screen, WHITE, paddle)
    pygame.draw.ellipse(screen, RED, ball)
    for block in blocks:
        pygame.draw.rect(screen, BLUE, block)

    pygame.display.flip()

pygame.quit()
sys.exit()