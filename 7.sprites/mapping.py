import pygame
import sys

pygame.init()

# --- Configuration ---
IMAGE_PATH = "knightspritesheet.jpg"  # Or your updated .png if preferred
WINDOW_TITLE = "Sprite Sheet Frame Visualizer"
LINE_COLOR = (255, 0, 0)
LINE_WIDTH = 1
SCALE = 0.5  # Change to zoom in/out (e.g. 1.0 = full size)

# Load image first (but convert later)
raw_image = pygame.image.load(IMAGE_PATH)
raw_width, raw_height = raw_image.get_size()

# Scale image
scaled_width = int(raw_width * SCALE)
scaled_height = int(raw_height * SCALE)
scaled_image = pygame.transform.scale(raw_image, (scaled_width, scaled_height))

# Set up screen and convert image
screen = pygame.display.set_mode((scaled_width, scaled_height))
pygame.display.set_caption(WINDOW_TITLE)
sprite_sheet = scaled_image.convert_alpha()

# --- Frame data (Idle + Walk)
original_frames = [
    # IDLE (row 1)
    {"x": 430, "y": 50, "w": 134, "h": 150},
    {"x": 564, "y": 50, "w": 134, "h": 150},
    {"x": 698, "y": 50, "w": 134, "h": 150},
    {"x": 832, "y": 50, "w": 134, "h": 150},

    # WALK (row 2 - full 8 frames)
    {"x": 430, "y": 200, "w": 134, "h": 150},
    {"x": 564, "y": 200, "w": 134, "h": 150},
    {"x": 698, "y": 200, "w": 134, "h": 150},
    {"x": 832, "y": 200, "w": 134, "h": 150},
    {"x": 986,  "y": 200, "w": 134, "h": 150},
    {"x": 1120, "y": 200, "w": 134, "h": 150},
    {"x": 1254, "y": 200, "w": 134, "h": 150},
    {"x": 1388, "y": 200, "w": 134, "h": 150}
]

# Apply scale to all frame rects
frame_rects = [
    {
        "x": int(f["x"] * SCALE),
        "y": int(f["y"] * SCALE),
        "w": int(f["w"] * SCALE),
        "h": int(f["h"] * SCALE)
    } for f in original_frames
]

# --- Draw loop ---
running = True
while running:
    screen.fill((0, 0, 0))
    screen.blit(sprite_sheet, (0, 0))

    for rect in frame_rects:
        pygame.draw.rect(
            screen,
            LINE_COLOR,
            pygame.Rect(rect["x"], rect["y"], rect["w"], rect["h"]),
            LINE_WIDTH
        )

    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running = False

    pygame.display.flip()

pygame.quit()
sys.exit()
