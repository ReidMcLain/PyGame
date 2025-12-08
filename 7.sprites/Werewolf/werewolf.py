import pygame
import sys
import math


class Enemy:
    def __init__(self, x, y, idle_folder, walk_folder, anim_speed, hover_amplitude, hover_speed, player_ref):
        self.x = x
        self.y = y
        self.anim_speed = anim_speed
        self.hover_amplitude = hover_amplitude
        self.hover_speed = hover_speed
        self.base_y = y
        self.hover_time = 0
        self.player_ref = player_ref

        self.idle_frames = self._load_seq(idle_folder, "Wraith_01_Idle_{i:03}.png", 12, (128, 129))
        self.walk_frames = self._load_seq(walk_folder, "Wraith_01_Moving Forward_{i:03}.png", 12, (128, 129))
        self.hurt_frames = self._load_seq("Wraith1Hurt", "Wraith_01_Hurt_{i:03}.png", 12, (128, 129))

        self.frames = self.idle_frames
        self.frame_index = 0
        self.anim_timer = 0

        self.state = "idle"
        self.invuln_until = 0
        self.knockback_vx = 0
        self.facing_left = False
        self.hover_offset = 0

    def _load_seq(self, folder, pattern, count, size):
        return [
            pygame.transform.scale(
                pygame.image.load(f"assets/{folder}/{pattern.format(i=i)}").convert_alpha(),
                size
            )
            for i in range(count)
        ]

    def get_hurtbox(self):
        ox, oy, w, h = 36, 22, 56, 82
        return pygame.Rect(self.x + ox, self.y + oy, w, h)

    def get_solidbox(self):
        ox, oy, w, h = 36, 22, 56, 82
        return pygame.Rect(self.x + ox, self.y + self.hover_offset + oy, w, h)

    def _maybe_take_hit(self, now):
        if now < self.invuln_until:
            return
        hitbox = self.player_ref.get_attack_hitbox()
        if not hitbox:
            return
        if hitbox.colliderect(self.get_hurtbox()):
            self.state = "hurt"
            self.frames = self.hurt_frames
            self.frame_index = 0
            self.anim_timer = 0
            self.invuln_until = now + 300
            self.knockback_vx = -4 if self.player_ref.facing_left else 4

    def chase(self, player_x):
        if self.state == "hurt":
            return
        dx = player_x - self.x
        if abs(dx) > 5:
            self.frames = self.walk_frames
            self.facing_left = dx < 0
            self.x += -1 if self.facing_left else 1
            self.state = "walk"
        else:
            self.frames = self.idle_frames
            self.state = "idle"
            if abs(dx) > 12:
                self.facing_left = dx < 0

    def update(self, dt, now):
        self._maybe_take_hit(now)

        if self.state == "hurt":
            if self.knockback_vx != 0:
                self.x += self.knockback_vx
                self.knockback_vx *= 0.82
                if abs(self.knockback_vx) < 0.25:
                    self.knockback_vx = 0
            self.anim_timer += dt
            if self.anim_timer >= 70:
                self.anim_timer = 0
                self.frame_index += 1
                if self.frame_index >= len(self.hurt_frames):
                    self.state = "idle"
                    self.frames = self.idle_frames
                    self.frame_index = 0
            self.hover_time += dt
            self.hover_offset = math.sin(self.hover_time * self.hover_speed) * self.hover_amplitude
            return

        self.anim_timer += dt
        if self.anim_timer >= self.anim_speed:
            self.anim_timer = 0
            self.frame_index = (self.frame_index + 1) % len(self.frames)

        self.hover_time += dt
        self.hover_offset = math.sin(self.hover_time * self.hover_speed) * self.hover_amplitude

    def draw(self, surface, camera_x):
        frame = self.frames[self.frame_index]
        if self.facing_left:
            frame = pygame.transform.flip(frame, True, False)
        surface.blit(frame, (self.x - camera_x, self.y + self.hover_offset))


class Player:
    def __init__(self, x, y, tiles_across):
        self.x = x
        self.y = y
        self.tiles_across = tiles_across

        self.frame_width = 128
        self.frame_height = 128
        self.ground_y = y

        self.walk_frames = self.load_sheet("assets/WerewolfAnimations/walk.png", 11)
        self.idle_frames = self.load_sheet("assets/WerewolfAnimations/Idle.png", 8)
        self.jump_frames = self.load_sheet("assets/WerewolfAnimations/Jump.png", 11)
        self.run_frames = self.load_sheet("assets/WerewolfAnimations/Run.png", 9)
        self.attack1_frames = self.load_sheet("assets/WerewolfAnimations/Attack_1.png", 6)
        self.attack2_frames = self.load_sheet("assets/WerewolfAnimations/Attack_2.png", 4)
        self.attack3_frames = self.load_sheet("assets/WerewolfAnimations/Attack_3.png", 5)
        self.run_attack_frames = self.load_sheet("assets/WerewolfAnimations/Run+Attack.png", 7)

        self.fireball_sheet = pygame.image.load("assets/Skills/fireball.png").convert_alpha()
        self.fireball_frames = [
            pygame.transform.scale(self.fireball_sheet.subsurface(pygame.Rect(i * 72, 0, 72, 72)), (144, 144)) for i in range(4)
        ]

        self.label_rect = pygame.Rect(900, self.ground_y - 80, 160, 80)

        self.frame_index = 0
        self.animation_timer = 0
        self.mode = "idle"
        self.previous_mode = "idle"
        self.jumping = False
        self.velocity_y = 0
        self.gravity = 1.2
        self.jump_force = -18

        self.dx = 0
        self.facing_left = False
        self.attack_chain = 0
        self.attack_queued = False
        self.attack_mode = None
        self.attack_dx = 0

        self.fireballs = []
        self.last_fireball_time = 0
        self.fireball_cooldown = 500
        self.fireball_unlocked = False

    def load_sheet(self, filename, count):
        sheet = pygame.image.load(filename).convert_alpha()
        return [sheet.subsurface(pygame.Rect(i * self.frame_width, 0, self.frame_width, self.frame_height)) for i in range(count)]

    def get_fireball_cooldown_ratio(self):
        now = pygame.time.get_ticks()
        elapsed = now - self.last_fireball_time
        return min(elapsed / self.fireball_cooldown, 1.0)

    def get_rect(self):
        return pygame.Rect(
            self.x - self.frame_width // 2,
            self.y - self.frame_height // 2,
            self.frame_width,
            self.frame_height
        )

    def get_attack_hitbox(self):
        if not self.attack_mode:
            return None
        spec = {
            "attack1": {"frames": (2, 3), "reach": -10, "w": -10, "h": 44},
            "attack2": {"frames": (2, 3), "reach": -10, "w": -10, "h": 48},
            "attack3": {"frames": (2, 4), "reach": -10, "w": -10, "h": 50},
            "runattack": {"frames": (3, 4), "reach": -10, "w": -10, "h": 46},
        }
        if self.attack_mode not in spec:
            return None
        start_f, end_f = spec[self.attack_mode]["frames"]
        if not (start_f <= self.frame_index <= end_f):
            return None

        base = self.get_rect()
        w = spec[self.attack_mode]["w"]
        h = spec[self.attack_mode]["h"]
        reach = spec[self.attack_mode]["reach"]

        if self.facing_left:
            x = base.left - reach - w
        else:
            x = base.right + reach
        y = base.centery - h // 2
        return pygame.Rect(x, y, w, h)

    def _move_horiz(self, dx, solids):
        if not dx:
            return
        rect = self.get_rect()
        skin = 1

        if solids:
            for s in solids:
                if rect.colliderect(s):
                    if rect.centerx < s.centerx:
                        rect.right = s.left - skin
                    else:
                        rect.left = s.right + skin

        if dx > 0:
            allowed = dx
            if solids:
                for s in solids:
                    if rect.bottom <= s.top or rect.top >= s.bottom:
                        continue
                    dist = (s.left - skin) - rect.right
                    if dist >= 0 and dist < allowed:
                        allowed = max(0, dist)
            rect.x += allowed
        else:
            allowed = dx
            if solids:
                for s in solids:
                    if rect.bottom <= s.top or rect.top >= s.bottom:
                        continue
                    dist = (s.right + skin) - rect.left
                    if dist <= 0 and dist > allowed:
                        allowed = min(0, dist)
            rect.x += allowed

        if solids:
            for s in solids:
                if rect.colliderect(s):
                    if rect.centerx < s.centerx:
                        rect.right = s.left - skin
                    else:
                        rect.left = s.right + skin

        self.x = rect.left + self.frame_width // 2

    def handle_input(self, keys, mouse_buttons, current_time):
        self.dx = 0
        is_running = keys[pygame.K_LSHIFT] or keys[pygame.K_RSHIFT]

        if not self.jumping and not self.attack_mode:
            if keys[pygame.K_LEFT] or keys[pygame.K_a]:
                self.dx = -8 if is_running else -5
                self.facing_left = True
            elif keys[pygame.K_RIGHT] or keys[pygame.K_d]:
                self.dx = 8 if is_running else 5
                self.facing_left = False

        if keys[pygame.K_SPACE] and not self.jumping:
            self.jumping = True
            self.velocity_y = self.jump_force
            self.frame_index = 0
            self.animation_timer = 0
            self.previous_mode = self.mode
            self.mode = "jump"

        if not self.attack_mode and mouse_buttons[0]:
            if is_running and self.dx != 0:
                self.attack_mode = "runattack"
                self.attack_dx = self.dx
            else:
                self.attack_mode = f"attack{self.attack_chain + 1}"
                self.attack_queued = False
            self.frame_index = 0
            self.animation_timer = 0

        if self.attack_mode and mouse_buttons[0] and not self.attack_queued:
            self.attack_queued = True

        player_rect = pygame.Rect(self.x, self.y, self.frame_width, self.frame_height)
        if not self.fireball_unlocked and player_rect.colliderect(self.label_rect):
            if keys[pygame.K_e]:
                self.fireball_unlocked = True

        if self.fireball_unlocked and keys[pygame.K_1] and current_time - self.last_fireball_time >= self.fireball_cooldown:
            fireball_offset = 30
            spawn_x = self.x + (self.frame_width // 2 + fireball_offset) if not self.facing_left else self.x - (self.frame_width // 2 + fireball_offset)
            spawn_y = self.y + 20
            self.fireballs.append({"x": spawn_x, "y": spawn_y, "frame": 0, "timer": 0, "ttl": 1000, "facing": self.facing_left, "speed": -8 if self.facing_left else 8})
            self.last_fireball_time = current_time

    def update(self, dt, keys, solids=None):
        if not self.jumping and not self.attack_mode:
            self.mode = "run" if self.dx != 0 and (keys[pygame.K_LSHIFT] or keys[pygame.K_RSHIFT]) else "walk" if self.dx != 0 else "idle"

        if self.mode != self.previous_mode and self.mode != "jump" and not self.attack_mode:
            self.frame_index = 0
            self.animation_timer = 0
            self.previous_mode = self.mode

        if self.attack_mode == "runattack":
            self._move_horiz(self.attack_dx, solids)
        else:
            self._move_horiz(self.dx, solids)

        self.x = max(0, min(self.x, self.tiles_across * 64 - self.frame_width // 2))

        if self.jumping:
            self.velocity_y += self.gravity
            self.y += self.velocity_y
            if keys[pygame.K_LEFT] or keys[pygame.K_a]:
                self._move_horiz(-5, solids)
                self.facing_left = True
            elif keys[pygame.K_RIGHT] or keys[pygame.K_d]:
                self._move_horiz(5, solids)
                self.facing_left = False
            if self.y >= self.ground_y:
                self.y = self.ground_y
                self.velocity_y = 0
                self.jumping = False
                self.mode = "idle" if self.dx == 0 else "walk"
                self.previous_mode = "jump"
                self.animation_timer = 0
                self.frame_index = 0

        if self.attack_mode:
            frames = self.run_attack_frames if self.attack_mode == "runattack" else eval(f"self.{self.attack_mode}_frames")
            current_speed = 70
        elif self.mode == "jump":
            frames, current_speed = self.jump_frames, 60
        elif self.mode == "run":
            frames, current_speed = self.run_frames, 60
        elif self.mode == "walk":
            frames, current_speed = self.walk_frames, 100
        else:
            frames, current_speed = self.idle_frames, 100

        self.animation_timer += dt
        if self.animation_timer >= current_speed:
            self.animation_timer = 0
            self.frame_index += 1
            if self.attack_mode and self.frame_index >= len(frames):
                if self.attack_mode.startswith("attack") and self.attack_queued:
                    self.attack_chain = (self.attack_chain + 1) % 3
                    self.attack_mode = f"attack{self.attack_chain + 1}"
                    self.frame_index = 0
                    self.attack_queued = False
                else:
                    self.attack_mode = None
                    self.attack_chain = 0
                    self.frame_index = 0
            elif not self.attack_mode:
                self.frame_index %= len(frames)

    def draw(self, screen, camera_x, font, fireball_icon):
        if self.attack_mode:
            frames = self.run_attack_frames if self.attack_mode == "runattack" else eval(f"self.{self.attack_mode}_frames")
        elif self.mode == "jump":
            frames = self.jump_frames
        elif self.mode == "run":
            frames = self.run_frames
        elif self.mode == "walk":
            frames = self.walk_frames
        else:
            frames = self.idle_frames

        frame = frames[min(self.frame_index, len(frames) - 1)]
        if self.facing_left:
            frame = pygame.transform.flip(frame, True, False)
        screen.blit(frame, (self.x - self.frame_width // 2 - camera_x, self.y - self.frame_height // 2))

        for fb in self.fireballs[:]:
            fb["x"] += fb["speed"]
            fb["timer"] += 1
            if fb["timer"] >= 50:
                fb["timer"] = 0
                fb["frame"] = (fb["frame"] + 1) % len(self.fireball_frames)
            fb["ttl"] -= 1
            if fb["ttl"] <= 0:
                self.fireballs.remove(fb)
                continue
            fb_img = self.fireball_frames[fb["frame"]]
            if fb["facing"]:
                fb_img = pygame.transform.flip(fb_img, True, False)
            screen.blit(fb_img, (self.x - fb_img.get_width() // 2 - camera_x, self.y - fb_img.get_height() // 2))

        if not self.fireball_unlocked:
            fireball_text = font.render("FIREBALL", True, (255, 0, 0))
            prompt_text = font.render("[E]", True, (255, 255, 255))
            screen.blit(fireball_text, (self.label_rect.x - camera_x, self.label_rect.y))
            screen.blit(prompt_text, (self.label_rect.x + 40 - camera_x, self.label_rect.y + 32))
        else:
            screen.blit(fireball_icon, (10, 10))
            key_text = font.render("[1]", True, (255, 255, 255))
            screen.blit(key_text, (10, 10 + fireball_icon.get_height() + 2))

            cooldown_ratio = self.get_fireball_cooldown_ratio()
            if cooldown_ratio < 1.0:
                icon_width, icon_height = fireball_icon.get_size()
                overlay = pygame.Surface((icon_width, icon_height), pygame.SRCALPHA)
                grey_height = icon_height * (1 - cooldown_ratio)
                pygame.draw.rect(overlay, (0, 0, 0, 180), (0, 0, icon_width, grey_height))
                screen.blit(overlay, (10, 10))


pygame.init()

SCREEN_WIDTH, SCREEN_HEIGHT = 800, 600
FPS = 60
TILE_SIZE = 64

screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
pygame.display.set_caption("Werewolf Sim")

background_image = pygame.image.load("assets/Environment/spookybackground.png").convert()
background_image = pygame.transform.scale(background_image, (SCREEN_WIDTH, SCREEN_HEIGHT))

font = pygame.font.Font("assets/gamefont.ttf", 32)
fireball_icon = pygame.image.load("assets/Skills/fireballicon.png").convert_alpha()

gothic_sheet = pygame.image.load("assets/Environment/gothicblocks.png").convert_alpha()


def crop_tile(sheet, tile_x, tile_y, crop_size=384, tile_size=512):
    offset = (tile_size - crop_size) // 2
    x = tile_x * tile_size + offset
    y = tile_y * tile_size + offset
    return sheet.subsurface(pygame.Rect(x, y, crop_size, crop_size))


gothic_tile = pygame.transform.scale(crop_tile(gothic_sheet, 0, 0), (TILE_SIZE, TILE_SIZE))
tiles_across = (SCREEN_WIDTH + TILE_SIZE - 1) // TILE_SIZE
bridge_blocks = [
    pygame.Rect(i * TILE_SIZE, SCREEN_HEIGHT - TILE_SIZE, TILE_SIZE, TILE_SIZE)
    for i in range(tiles_across)
]

player = Player(SCREEN_WIDTH // 2, SCREEN_HEIGHT - TILE_SIZE - 64, tiles_across)

wraith = Enemy(
    x=SCREEN_WIDTH - 150,
    y=SCREEN_HEIGHT - TILE_SIZE - 128 + 30,
    idle_folder="Wraith1Idle",
    walk_folder="Wraith1Walking",
    anim_speed=100,
    hover_amplitude=8,
    hover_speed=0.005,
    player_ref=player
)

clock = pygame.time.Clock()
running = True

while running:
    dt = clock.tick(FPS)
    now = pygame.time.get_ticks()

    keys = pygame.key.get_pressed()
    mouse_buttons = pygame.mouse.get_pressed()
    camera_x = 0

    screen.blit(background_image, (0, 0))
    for block in bridge_blocks:
        screen.blit(gothic_tile, (block.x, block.y))

    player.handle_input(keys, mouse_buttons, now)
    player.update(dt, keys, solids=[wraith.get_solidbox()])
    player.draw(screen, camera_x, font, fireball_icon)

    wraith.chase(player.x)
    wraith.update(dt, now)
    wraith.draw(screen, camera_x)

    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running = False

    pygame.display.flip()

pygame.quit()
sys.exit()