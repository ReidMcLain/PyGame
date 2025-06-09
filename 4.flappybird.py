import pygame
import sys
import random

# Initialize Pygame
pygame.init()

# Constants
SCREEN_WIDTH = 400
SCREEN_HEIGHT = 600
PIPE_WIDTH = 60
PIPE_GAP = 180  # Increased gap size
PIPE_SPEED = 3
PIPE_FREQUENCY = 1500  # milliseconds
BIRD_SIZE = 34
GRAVITY = 0.3
FLAP_STRENGTH = -6  # Slightly nerfed jump

# Colors
BLACK = (0, 0, 0)
GREEN = (0, 255, 0)
RED = (255, 0, 0)
WHITE = (255, 255, 255)

# Setup screen
screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
pygame.display.set_caption("Flappy Bird - Pipes + Bird + Score")
clock = pygame.time.Clock()
font = pygame.font.SysFont("monospace", 24)  # Smaller font

# Pipe pair class
class PipePair:
    def __init__(self):
        self.gap_y = random.randint(100, SCREEN_HEIGHT - 100 - PIPE_GAP)
        self.top_rect = pygame.Rect(SCREEN_WIDTH, 0, PIPE_WIDTH, self.gap_y)
        self.bottom_rect = pygame.Rect(SCREEN_WIDTH, self.gap_y + PIPE_GAP, PIPE_WIDTH, SCREEN_HEIGHT - self.gap_y - PIPE_GAP)
        self.passed = False  # For scoring

    def update(self):
        self.top_rect.x -= PIPE_SPEED
        self.bottom_rect.x -= PIPE_SPEED

    def draw(self):
        pygame.draw.rect(screen, GREEN, self.top_rect)
        pygame.draw.rect(screen, GREEN, self.bottom_rect)

# Bird class
class Bird:
    def __init__(self):
        self.x = 50
        self.y = SCREEN_HEIGHT // 2
        self.velocity = 0
        self.rect = pygame.Rect(self.x, self.y, BIRD_SIZE, BIRD_SIZE)

    def update(self):
        self.velocity += GRAVITY
        self.y += self.velocity
        self.rect.y = int(self.y)

    def flap(self):
        self.velocity = FLAP_STRENGTH

    def draw(self):
        pygame.draw.rect(screen, RED, self.rect)

# Game state
pipes = [PipePair()]  # Start with one pipe right away
last_pipe_time = pygame.time.get_ticks()
bird = Bird()
game_over = False
score = 0

# Game loop
running = True
while running:
    clock.tick(60)
    screen.fill(BLACK)

    # Event handling
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running = False
        if event.type == pygame.KEYDOWN:
            if not game_over:
                if event.key == pygame.K_SPACE:
                    bird.flap()
            if game_over and event.key == pygame.K_r:
                bird = Bird()
                pipes = [PipePair()]
                game_over = False
                last_pipe_time = pygame.time.get_ticks()
                score = 0

    if not game_over:
        # Update bird
        bird.update()

        # Spawn pipes
        current_time = pygame.time.get_ticks()
        if current_time - last_pipe_time > PIPE_FREQUENCY:
            last_pipe_time = current_time
            pipes.append(PipePair())

        # Update pipes
        for pipe in pipes:
            pipe.update()

        # Remove off-screen pipes
        pipes = [pipe for pipe in pipes if pipe.top_rect.right > 0]

        # Check collisions
        for pipe in pipes:
            if bird.rect.colliderect(pipe.top_rect) or bird.rect.colliderect(pipe.bottom_rect):
                game_over = True

            # Check scoring
            if not pipe.passed and pipe.top_rect.right < bird.x:
                score += 1
                pipe.passed = True

        # Check ground and ceiling
        if bird.y <= 0 or bird.y + BIRD_SIZE >= SCREEN_HEIGHT:
            game_over = True

    # Draw pipes
    for pipe in pipes:
        pipe.draw()

    # Draw bird
    bird.draw()

    # Draw score
    score_text = font.render(f"Score: {score}", True, WHITE)
    screen.blit(score_text, (10, 10))

    # Draw game over text
    if game_over:
        text1 = font.render("Game Over!", True, WHITE)
        text2 = font.render("Press R to Restart", True, WHITE)
        screen.blit(text1, (SCREEN_WIDTH // 2 - text1.get_width() // 2, SCREEN_HEIGHT // 2 - 30))
        screen.blit(text2, (SCREEN_WIDTH // 2 - text2.get_width() // 2, SCREEN_HEIGHT // 2 + 10))

    pygame.display.flip()

pygame.quit()
sys.exit()