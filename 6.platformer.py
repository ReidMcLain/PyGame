import pygame
import sys

# Initialize Pygame
pygame.init()

# Constants
SCREEN_WIDTH = 600
SCREEN_HEIGHT = 400
PLAYER_WIDTH = 40
PLAYER_HEIGHT = 60
PLAYER_SPEED = 8
JUMP_STRENGTH = -15
GRAVITY = 0.5
COYOTE_TIME = 0.5 * 60  # 0.5 seconds * 60 FPS
LEVEL_WIDTH = 1800
LEVEL_HEIGHT = 1200  # Increased level height for vertical exploration
MAX_HEALTH = 3  # Maximum hearts

# Colors
BLACK = (0, 0, 0)
WHITE = (255, 255, 255)
GREEN = (0, 255, 0)

# Setup screen
screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
pygame.display.set_caption("Scrolling Platformer")
clock = pygame.time.Clock()

# Load images
player_image_original = pygame.image.load("player.png").convert_alpha()
player_image_original = pygame.transform.scale(player_image_original, (PLAYER_WIDTH, PLAYER_HEIGHT))
player_image_flipped = pygame.transform.flip(player_image_original, True, False)

ENEMY_WIDTH = 80  # 2x size
ENEMY_HEIGHT = 120  # 2x size
enemy_image = pygame.image.load("patrol.png").convert_alpha()
enemy_image = pygame.transform.scale(enemy_image, (ENEMY_WIDTH, ENEMY_HEIGHT))

# Load heart images
HEART_SIZE = 30
heart_full = pygame.image.load("heart.png").convert_alpha()
heart_full = pygame.transform.scale(heart_full, (HEART_SIZE, HEART_SIZE))
heart_empty = pygame.image.load("heart_empty.png").convert_alpha()
heart_empty = pygame.transform.scale(heart_empty, (HEART_SIZE, HEART_SIZE))

# Player class
class Player:
    def __init__(self):
        self.x = LEVEL_WIDTH - PLAYER_WIDTH - 20  # Start at bottom right
        self.y = LEVEL_HEIGHT - PLAYER_HEIGHT - 10
        self.vx = 0
        self.vy = 0
        self.on_ground = False
        self.rect = pygame.Rect(self.x, self.y, PLAYER_WIDTH, PLAYER_HEIGHT)
        self.coyote_timer = 0
        self.facing_right = False  # Default direction (original image faces left)
        self.health = 3
        self.hit_cooldown = 0  # NEW: cooldown to prevent rapid health loss

    def handle_input(self, keys):
        self.vx = 0
        if keys[pygame.K_a]:
            self.vx = -PLAYER_SPEED
            self.facing_right = False  # Facing left
        if keys[pygame.K_d]:
            self.vx = PLAYER_SPEED
            self.facing_right = True  # Facing right
        if keys[pygame.K_SPACE] and (self.on_ground or self.coyote_timer > 0):
            self.vy = JUMP_STRENGTH
            self.coyote_timer = 0

    def update(self, platforms, enemies):
        self.vy += GRAVITY

        # Horizontal movement
        self.x += self.vx
        self.rect.x = int(self.x)
        for platform in platforms:
            if self.rect.colliderect(platform):
                if self.vx > 0:
                    self.rect.right = platform.left
                    self.x = self.rect.x
                elif self.vx < 0:
                    self.rect.left = platform.right
                    self.x = self.rect.x

        # Vertical movement
        self.y += self.vy
        self.rect.y = int(self.y)
        self.on_ground = False
        for platform in platforms:
            if self.rect.colliderect(platform):
                if self.vy > 0:
                    self.rect.bottom = platform.top
                    self.y = self.rect.y
                    self.vy = 0
                    self.on_ground = True
                elif self.vy < 0:
                    self.rect.top = platform.bottom
                    self.y = self.rect.y
                    self.vy = 0

        # Coyote time
        if self.on_ground:
            self.coyote_timer = COYOTE_TIME
        elif self.coyote_timer > 0:
            self.coyote_timer -= 1

        # Handle enemy collision
        if self.hit_cooldown > 0:
            self.hit_cooldown -= 1
        for enemy in enemies:
            if self.rect.colliderect(enemy.rect) and self.hit_cooldown == 0:
                self.health -= 1
                self.hit_cooldown = 60  # 1 second delay

    def draw(self, camera_x, camera_y):
        if self.facing_right:
            screen.blit(player_image_flipped, (round(self.rect.x - camera_x), round(self.rect.y - camera_y)))
        else:
            screen.blit(player_image_original, (round(self.rect.x - camera_x), round(self.rect.y - camera_y)))

# Enemy class with patrol logic
class Enemy:
    def __init__(self, x, y):
        self.x = x
        self.y = y - ENEMY_HEIGHT  # align top
        self.vx = 2  # Patrol speed
        self.min_x = x - 100  # Left patrol boundary
        self.max_x = x + 100  # Right patrol boundary
        self.rect = pygame.Rect(self.x, self.y, ENEMY_WIDTH, ENEMY_HEIGHT)

    def update(self):
        self.x += self.vx
        self.rect.x = int(self.x)
        if self.x < self.min_x or self.x > self.max_x:
            self.vx *= -1  # Reverse direction

    def draw(self, camera_x, camera_y):
        screen.blit(enemy_image, (round(self.x - camera_x), round(self.y - camera_y)))

# Platforms
platforms = [
    # Ground
    pygame.Rect(0, LEVEL_HEIGHT - 10, LEVEL_WIDTH, 10),

    # Lower platforms
    pygame.Rect(100, 1100, 200, 10),
    pygame.Rect(400, 1000, 150, 10),
    pygame.Rect(700, 950, 200, 10),
    pygame.Rect(1000, 900, 150, 10),
    pygame.Rect(200, 800, 200, 10),

    # Middle platform (the one with opening above)
    pygame.Rect(600, 700, 200, 10),

    # Higher platforms leading to top bar
    pygame.Rect(900, 600, 200, 10),
    pygame.Rect(1200, 500, 200, 10),

    # Horizontal T top bar (middle)
    pygame.Rect(300, 200, 1800, 10),

    # Right-side T-bar (continuous)
    pygame.Rect(2100, 200, 600, 10),

    # Left-side T-bar (continuous)
    pygame.Rect(-600, 200, 600, 10),

    # Left-side connecting platforms
    pygame.Rect(200, 300, 100, 10),
    pygame.Rect(150, 400, 100, 10),
    pygame.Rect(100, 500, 100, 10),

    # NEW intermediate platform aligned with bottom platform's left edge
    pygame.Rect(500, 600, 150, 10),

    # Walls
    pygame.Rect(0, 200, 10, LEVEL_HEIGHT - 210),  # left wall
    pygame.Rect(LEVEL_WIDTH - 10, 210, 10, LEVEL_HEIGHT - 210)  # right wall
]

# Create patrolling enemy on the top bar
enemy = Enemy(1000, 200)

# Player health
player_health = MAX_HEALTH

# Game loop
player = Player()
camera_x = 0
camera_y = 0

running = True
while running:
    clock.tick(60)
    screen.fill(BLACK)

    # Event handling
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running = False

    # Input
    keys = pygame.key.get_pressed()
    player.handle_input(keys)

    # Update
    player.update(platforms, [enemy])
    enemy.update()

    # Check for collision with enemy
   # Check game over
    if player.health <= 0:
        print("Game Over!")
        running = False


    # Update camera
    camera_x = round(player.x - SCREEN_WIDTH // 2)
    camera_y = round(player.y - SCREEN_HEIGHT // 2)

    # Draw platforms and walls
    for platform in platforms:
        pygame.draw.rect(screen, GREEN, (platform.x - camera_x, platform.y - camera_y, platform.width, platform.height))

    # Draw enemy
    enemy.draw(camera_x, camera_y)

    # Draw player
    player.draw(camera_x, camera_y)

    # Draw hearts (top right)
    for i in range(MAX_HEALTH):
        x = 10 + i * (HEART_SIZE + 10)
        y = 10
        if i < player.health:
            screen.blit(heart_full, (x, y))
        else:
            screen.blit(heart_empty, (x, y))

    pygame.display.flip()

pygame.quit()
sys.exit()