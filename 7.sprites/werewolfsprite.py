import pygame
import sys

pygame.init()

# --- Configuration ---
SCREEN_WIDTH, SCREEN_HEIGHT = 800, 600
FPS = 60
WALK_SPEED = 5
JUMP_SPEED = 32
WALK_ANIM_SPEED = 100
IDLE_ANIM_SPEED = 100
JUMP_ANIM_SPEED = 60
BG_COLOR = (0, 0, 0)

screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
pygame.display.set_caption("Werewolf Sim")

# --- Load background and scale to screen ---
background_image = pygame.image.load("werewolfbg.png").convert()
background_image = pygame.transform.scale(background_image, (SCREEN_WIDTH, SCREEN_HEIGHT))

# --- Load sprite sheets ---
walk_sheet = pygame.image.load("walk.png").convert_alpha()
idle_sheet = pygame.image.load("Idle.png").convert_alpha()
jump_sheet = pygame.image.load("Jump.png").convert_alpha()

# --- Extract frames ---
frame_width = 128
frame_height = 128

walk_frames = [
    walk_sheet.subsurface(pygame.Rect(i * frame_width, 0, frame_width, frame_height)).convert_alpha()
    for i in range(11)
]

idle_frames = [
    idle_sheet.subsurface(pygame.Rect(i * frame_width, 0, frame_width, frame_height)).convert_alpha()
    for i in range(8)
]

jump_frames = [
    jump_sheet.subsurface(pygame.Rect(i * frame_width, 0, frame_width, frame_height)).convert_alpha()
    for i in range(11)
]

jump_offsets = [
    -16 * i if i <= 5 else -16 * (10 - i)
    for i in range(11)
]

# --- State ---
x = SCREEN_WIDTH // 2
y = SCREEN_HEIGHT // 2
ground_y = SCREEN_HEIGHT - frame_height // 2
dx = 0
facing_left = False
frame_index = 0
animation_timer = 0
mode = "idle"
previous_mode = "idle"
jumping = False

# --- Game Loop ---
clock = pygame.time.Clock()
running = True

while running:
    dt = clock.tick(FPS)
    screen.blit(background_image, (0, 0))  # Draw scaled background

    keys = pygame.key.get_pressed()
    dx = 0

    if not jumping:
        if keys[pygame.K_LEFT] or keys[pygame.K_a]:
            dx = -WALK_SPEED
            facing_left = True
        elif keys[pygame.K_RIGHT] or keys[pygame.K_d]:
            dx = WALK_SPEED
            facing_left = False

    if keys[pygame.K_SPACE] and not jumping:
        jumping = True
        frame_index = 0
        animation_timer = 0
        previous_mode = mode
        mode = "jump"

    if not jumping:
        mode = "walk" if dx != 0 else "idle"

    if mode != previous_mode and mode != "jump":
        frame_index = 0
        animation_timer = 0
        previous_mode = mode

    if not jumping:
        x += dx
        x = max(0, min(x, SCREEN_WIDTH))

    frames = jump_frames if mode == "jump" else walk_frames if mode == "walk" else idle_frames
    current_speed = JUMP_ANIM_SPEED if mode == "jump" else WALK_ANIM_SPEED if mode == "walk" else IDLE_ANIM_SPEED

    animation_timer += dt
    if animation_timer >= current_speed:
        animation_timer = 0
        frame_index += 1

        if mode == "jump" and frame_index < len(jump_frames):
            if keys[pygame.K_LEFT] or keys[pygame.K_a]:
                x -= JUMP_SPEED
                facing_left = True
            elif keys[pygame.K_RIGHT] or keys[pygame.K_d]:
                x += JUMP_SPEED
                facing_left = False
            x = max(0, min(x, SCREEN_WIDTH))

        if mode == "jump" and frame_index >= len(jump_frames):
            frame_index = 0
            jumping = False
            mode = "idle" if dx == 0 else "walk"
            previous_mode = "jump"
            animation_timer = 0

        if mode != "jump":
            frame_index %= len(frames)

    frame = frames[frame_index % len(frames)]
    if facing_left:
        frame = pygame.transform.flip(frame, True, False)

    y_offset = jump_offsets[frame_index] if mode == "jump" and frame_index < len(jump_offsets) else 0
    screen.blit(frame, (x - frame_width // 2, ground_y + y_offset - frame_height // 2))

    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running = False

    pygame.display.flip()

pygame.quit()
sys.exit()