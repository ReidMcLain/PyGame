import pygame
import sys

pygame.init()

# --- Configuration ---
SCREEN_WIDTH, SCREEN_HEIGHT = 800, 600
FPS = 60
WALK_SPEED = 5
RUN_SPEED = 8
JUMP_SPEED = 5
WALK_ANIM_SPEED = 100
RUN_ANIM_SPEED = 60
IDLE_ANIM_SPEED = 100
JUMP_ANIM_SPEED = 60
FIREBALL_ANIM_SPEED = 50
ATTACK_ANIM_SPEED = 70
TILE_SIZE = 64

font_path = "gamefont.ttf"
font_size = 32
game_font = pygame.font.Font(font_path, font_size)

screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
pygame.display.set_caption("Werewolf Sim")

# --- Load assets ---
background_image = pygame.image.load("spookybackground.png").convert()
background_image = pygame.transform.scale(background_image, (1920, SCREEN_HEIGHT))
walk_sheet = pygame.image.load("walk.png").convert_alpha()
idle_sheet = pygame.image.load("Idle.png").convert_alpha()
jump_sheet = pygame.image.load("Jump.png").convert_alpha()
run_sheet = pygame.image.load("Run.png").convert_alpha()
fireball_sheet = pygame.image.load("fireball.png").convert_alpha()
gothic_sheet = pygame.image.load("gothicblocks.png").convert_alpha()
fireball_icon = pygame.image.load("fireballicon.png").convert_alpha()
attack1_sheet = pygame.image.load("Attack_1.png").convert_alpha()
attack2_sheet = pygame.image.load("Attack_2.png").convert_alpha()
attack3_sheet = pygame.image.load("Attack_3.png").convert_alpha()
run_attack_sheet = pygame.image.load("Run+Attack.png").convert_alpha()

# --- Extract tiles ---
def crop_tile(sheet, tile_x, tile_y, crop_size=384, tile_size=512):
    offset = (tile_size - crop_size) // 2
    x = tile_x * tile_size + offset
    y = tile_y * tile_size + offset
    return sheet.subsurface(pygame.Rect(x, y, crop_size, crop_size))

gothic_tile = pygame.transform.scale(crop_tile(gothic_sheet, 0, 0), (TILE_SIZE, TILE_SIZE))

tiles_across = background_image.get_width() // TILE_SIZE
bridge_blocks = [pygame.Rect(i * TILE_SIZE, SCREEN_HEIGHT - TILE_SIZE, TILE_SIZE, TILE_SIZE) for i in range(tiles_across)]

frame_width, frame_height = 128, 128
walk_frames = [walk_sheet.subsurface(pygame.Rect(i * frame_width, 0, frame_width, frame_height)) for i in range(11)]
idle_frames = [idle_sheet.subsurface(pygame.Rect(i * frame_width, 0, frame_width, frame_height)) for i in range(8)]
jump_frames = [jump_sheet.subsurface(pygame.Rect(i * frame_width, 0, frame_width, frame_height)) for i in range(11)]
run_frames = [run_sheet.subsurface(pygame.Rect(i * frame_width, 0, frame_width, frame_height)) for i in range(9)]
attack1_frames = [attack1_sheet.subsurface(pygame.Rect(i * frame_width, 0, frame_width, frame_height)) for i in range(6)]
attack2_frames = [attack2_sheet.subsurface(pygame.Rect(i * frame_width, 0, frame_width, frame_height)) for i in range(4)]
attack3_frames = [attack3_sheet.subsurface(pygame.Rect(i * frame_width, 0, frame_width, frame_height)) for i in range(5)]
run_attack_frames = [run_attack_sheet.subsurface(pygame.Rect(i * frame_width, 0, frame_width, frame_height)) for i in range(7)]
fireball_frames = [pygame.transform.scale(fireball_sheet.subsurface(pygame.Rect(i * 72, 0, 72, 72)), (144, 144)) for i in range(4)]

x = SCREEN_WIDTH // 2
ground_y = SCREEN_HEIGHT - TILE_SIZE - frame_height // 2
y = ground_y
dx = 0
facing_left = False
frame_index = 0
animation_timer = 0
mode = "idle"
previous_mode = "idle"
jumping = False
velocity_y = 0
gravity = 1.2
jump_force = -18

fireballs = []
last_fireball_time = 0
fireball_cooldown = 500
fireball_unlocked = False

attack_chain = 0
attack_queued = False
attack_mode = None
attack_dx = 0

fireball_label_x = 900
fireball_label_y = SCREEN_HEIGHT - TILE_SIZE - 80
label_rect = pygame.Rect(fireball_label_x, fireball_label_y, 160, 80)

clock = pygame.time.Clock()
running = True

def get_fireball_cooldown_ratio():
    now = pygame.time.get_ticks()
    elapsed = now - last_fireball_time
    return min(elapsed / fireball_cooldown, 1.0)

while running:
    dt = clock.tick(FPS)
    current_time = pygame.time.get_ticks()
    camera_x = max(0, min(x - SCREEN_WIDTH // 2, background_image.get_width() - SCREEN_WIDTH))
    screen.blit(background_image, (-camera_x, 0))

    keys = pygame.key.get_pressed()
    dx = 0
    is_running = keys[pygame.K_LSHIFT] or keys[pygame.K_RSHIFT]

    if not jumping and not attack_mode:
        if keys[pygame.K_LEFT] or keys[pygame.K_a]:
            dx = -RUN_SPEED if is_running else -WALK_SPEED
            facing_left = True
        elif keys[pygame.K_RIGHT] or keys[pygame.K_d]:
            dx = RUN_SPEED if is_running else WALK_SPEED
            facing_left = False

    if keys[pygame.K_SPACE] and not jumping:
        jumping = True
        velocity_y = jump_force
        frame_index = 0
        animation_timer = 0
        previous_mode = mode
        mode = "jump"

    if not attack_mode and pygame.mouse.get_pressed()[0]:
        if is_running and dx != 0:
            attack_mode = "runattack"
            attack_dx = dx
        else:
            attack_mode = f"attack{attack_chain + 1}"
            attack_queued = False
        frame_index = 0
        animation_timer = 0

    if attack_mode and pygame.mouse.get_pressed()[0] and not attack_queued:
        attack_queued = True

    player_rect = pygame.Rect(x, y, frame_width, frame_height)
    if not fireball_unlocked and player_rect.colliderect(label_rect):
        if keys[pygame.K_e]:
            fireball_unlocked = True

    if fireball_unlocked and keys[pygame.K_1] and current_time - last_fireball_time >= fireball_cooldown:
        fireball_offset = 30
        spawn_x = x + (frame_width // 2 + fireball_offset) if not facing_left else x - (frame_width // 2 + fireball_offset)
        spawn_y = y + 20
        fireballs.append({"x": spawn_x, "y": spawn_y, "frame": 0, "timer": 0, "ttl": 1000, "facing": facing_left, "speed": -8 if facing_left else 8})
        last_fireball_time = current_time

    if not jumping and not attack_mode:
        mode = "run" if dx != 0 and is_running else "walk" if dx != 0 else "idle"
    if mode != previous_mode and mode != "jump" and not attack_mode:
        frame_index = 0
        animation_timer = 0
        previous_mode = mode

    if attack_mode == "runattack":
        x += attack_dx
    else:
        x += dx

    x = max(0, min(x, tiles_across * TILE_SIZE - frame_width // 2))

    if jumping:
        velocity_y += gravity
        y += velocity_y
        if keys[pygame.K_LEFT] or keys[pygame.K_a]:
            x -= JUMP_SPEED
            facing_left = True
        elif keys[pygame.K_RIGHT] or keys[pygame.K_d]:
            x += JUMP_SPEED
            facing_left = False
        if y >= ground_y:
            y = ground_y
            velocity_y = 0
            jumping = False
            mode = "idle" if dx == 0 else "walk"
            previous_mode = "jump"
            animation_timer = 0
            frame_index = 0

    if attack_mode:
        frames = run_attack_frames if attack_mode == "runattack" else eval(f"attack{attack_chain + 1}_frames")
        current_speed = ATTACK_ANIM_SPEED
    elif mode == "jump":
        frames, current_speed = jump_frames, JUMP_ANIM_SPEED
    elif mode == "run":
        frames, current_speed = run_frames, RUN_ANIM_SPEED
    elif mode == "walk":
        frames, current_speed = walk_frames, WALK_ANIM_SPEED
    else:
        frames, current_speed = idle_frames, IDLE_ANIM_SPEED

    animation_timer += dt
    if animation_timer >= current_speed:
        animation_timer = 0
        frame_index += 1
        if attack_mode and frame_index >= len(frames):
            if attack_mode.startswith("attack") and attack_queued:
                attack_chain = (attack_chain + 1) % 3
                attack_mode = f"attack{attack_chain + 1}"
                frame_index = 0
                attack_queued = False
            else:
                attack_mode = None
                attack_chain = 0
                frame_index = 0
        elif not attack_mode:
            frame_index %= len(frames)

    frame = frames[min(frame_index, len(frames) - 1)]
    if facing_left:
        frame = pygame.transform.flip(frame, True, False)
    screen.blit(frame, (x - frame_width // 2 - camera_x, y - frame_height // 2))

    for block in bridge_blocks:
        screen.blit(gothic_tile, (block.x - camera_x, block.y))

    for fb in fireballs[:]:
        fb["x"] += fb["speed"]
        fb["timer"] += dt
        if fb["timer"] >= FIREBALL_ANIM_SPEED:
            fb["timer"] = 0
            fb["frame"] = (fb["frame"] + 1) % len(fireball_frames)
        fb["ttl"] -= dt
        if fb["ttl"] <= 0:
            fireballs.remove(fb)
            continue
        fb_img = fireball_frames[fb["frame"]]
        if fb["facing"]:
            fb_img = pygame.transform.flip(fb_img, True, False)
        img_offset_x = fb_img.get_width() // 2
        img_offset_y = fb_img.get_height() // 2
        screen.blit(fb_img, (fb["x"] - img_offset_x - camera_x, fb["y"] - img_offset_y))

    if not fireball_unlocked:
        fireball_text = game_font.render("FIREBALL", True, (255, 0, 0))
        prompt_text = game_font.render("[E]", True, (255, 255, 255))
        screen.blit(fireball_text, (fireball_label_x - camera_x, fireball_label_y))
        screen.blit(prompt_text, (fireball_label_x + 40 - camera_x, fireball_label_y + 32))
    else:
        screen.blit(fireball_icon, (10, 10))
        key_text = game_font.render("[1]", True, (255, 255, 255))
        screen.blit(key_text, (10, 10 + fireball_icon.get_height() + 2))

        cooldown_ratio = get_fireball_cooldown_ratio()
        if cooldown_ratio < 1.0:
            icon_width, icon_height = fireball_icon.get_size()
            overlay = pygame.Surface((icon_width, icon_height), pygame.SRCALPHA)
            grey_height = icon_height * (1 - cooldown_ratio)
            pygame.draw.rect(overlay, (0, 0, 0, 180), (0, 0, icon_width, grey_height))
            screen.blit(overlay, (10, 10))

    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running = False

    pygame.display.flip()

pygame.quit()
sys.exit()