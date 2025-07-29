import pygame
import sys

pygame.init()

# --- Configuration ---
SCREEN_WIDTH, SCREEN_HEIGHT = 800, 600
FPS = 60
BG_COLOR = (162, 162, 162)
WALK_SPEED = 5
ANIMATION_SPEED = 100  # milliseconds per frame

# Load and setup
screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
pygame.display.set_caption("Knight Walk + Idle Animation")

sprite_sheet = pygame.image.load("knightspritesheet.jpg").convert_alpha()

# --- Frame data ---
walk_frames_data = [
    {"x": 430, "y": 200, "w": 134, "h": 150},
    {"x": 564, "y": 200, "w": 134, "h": 150},
    {"x": 698, "y": 200, "w": 134, "h": 150},
    {"x": 832, "y": 200, "w": 134, "h": 150},
    {"x": 986,  "y": 200, "w": 134, "h": 150},
    {"x": 1120, "y": 200, "w": 134, "h": 150},
    {"x": 1254, "y": 200, "w": 134, "h": 150},
    {"x": 1388, "y": 200, "w": 134, "h": 150}
]

idle_frames_data = [
    {"x": 430, "y": 50, "w": 134, "h": 150},
    {"x": 564, "y": 50, "w": 134, "h": 150},
    {"x": 698, "y": 50, "w": 134, "h": 150},
    {"x": 832, "y": 50, "w": 134, "h": 150}
]

def extract_frames(sheet, frame_data_list):
    return [
        sheet.subsurface(pygame.Rect(f["x"], f["y"], f["w"], f["h"])).convert_alpha()
        for f in frame_data_list
    ]

walk_frames = extract_frames(sprite_sheet, walk_frames_data)
idle_frames = extract_frames(sprite_sheet, idle_frames_data)

# --- State ---
x = SCREEN_WIDTH // 2
y = SCREEN_HEIGHT // 2
dx = 0
facing_left = False
frame_index = 0
animation_timer = 0
mode = "idle"

# --- Game loop ---
clock = pygame.time.Clock()
running = True

while running:
    dt = clock.tick(FPS)
    screen.fill(BG_COLOR)

    # Input
    keys = pygame.key.get_pressed()
    dx = 0

    if keys[pygame.K_LEFT] or keys[pygame.K_a]:
        dx = -WALK_SPEED
        facing_left = True
    elif keys[pygame.K_RIGHT] or keys[pygame.K_d]:
        dx = WALK_SPEED
        facing_left = False

    # Set mode
    mode = "walk" if dx != 0 else "idle"

    # Move and clamp to screen
    x += dx
    x = max(0, min(x, SCREEN_WIDTH))

    # Animation
    frames = walk_frames if mode == "walk" else idle_frames
    animation_timer += dt
    if animation_timer >= ANIMATION_SPEED:
        animation_timer = 0
        frame_index = (frame_index + 1) % len(frames)

    # Reset animation when switching modes
    if frame_index >= len(frames):
        frame_index = 0

    frame = frames[frame_index]
    if facing_left:
        frame = pygame.transform.flip(frame, True, False)

    screen.blit(frame, (x - frame.get_width() // 2, y - frame.get_height() // 2))

    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running = False

    pygame.display.flip()

pygame.quit()
sys.exit()