import pygame
import sys

pygame.init()

# --- Configuration ---
SCREEN_WIDTH, SCREEN_HEIGHT = 800, 600
FPS = 60
WHITE = (255, 255, 255)

# Load and setup
screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
pygame.display.set_caption("Knight Animation - Idle Only")

sprite_sheet = pygame.image.load("knightspritesheet.jpg").convert_alpha()

# --- Frame data for idle animation (manual slicing) ---
idle_frames_data = [
    {"x": 430, "y": 50, "w": 134, "h": 150},
    {"x": 564, "y": 50, "w": 134, "h": 150},
    {"x": 698, "y": 50, "w": 134, "h": 150},
    {"x": 832, "y": 50, "w": 134, "h": 150}
]

def extract_frames(sheet, frame_data_list):
    return [
        sheet.subsurface(pygame.Rect(f["x"], f["y"], f["w"], f["h"]))
        for f in frame_data_list
    ]

idle_frames = extract_frames(sprite_sheet, idle_frames_data)

# --- Animation state ---
x, y = SCREEN_WIDTH // 2, SCREEN_HEIGHT // 2
frame_index = 0
animation_timer = 0
animation_speed = 150  # ms per frame

# --- Game loop ---
clock = pygame.time.Clock()
running = True

while running:
    dt = clock.tick(FPS)
    screen.fill(WHITE)

    animation_timer += dt
    if animation_timer >= animation_speed:
        animation_timer = 0
        frame_index = (frame_index + 1) % len(idle_frames)

    screen.blit(idle_frames[frame_index], (x, y))

    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running = False

    pygame.display.flip()

pygame.quit()
sys.exit()