import pygame
import sys
import math

from physics import move_with_collisions
from wraith import Wraith

pygame.init()

SCREEN_WIDTH, SCREEN_HEIGHT = 800, 600
FPS = 60
TILE_SIZE = 64

PLAYER_HIT_MARGIN_X = 30
PLAYER_HIT_MARGIN_Y = 20

LAND_OFFSET = 0

DEBUG_BOXES = False

screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
pygame.display.set_caption("Werewolf 2 - Pygame Physics")

background_image = pygame.image.load("assets/Environment/spookybackground.png").convert()
background_image = pygame.transform.scale(background_image, (SCREEN_WIDTH, SCREEN_HEIGHT))

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


class Player:
    def __init__(self, x, y):
        self.x = x
        self.y = y

        self.frame_width = 128
        self.frame_height = 128

        self.idle_frames = self.load_sheet("assets/WerewolfAnimations/Idle.png", 8)
        self.walk_frames = self.load_sheet("assets/WerewolfAnimations/walk.png", 11)

        self.attack1_frames = self.load_sheet("assets/WerewolfAnimations/Attack_1.png", 6)
        self.attack2_frames = self.load_sheet("assets/WerewolfAnimations/Attack_2.png", 4)
        self.attack3_frames = self.load_sheet("assets/WerewolfAnimations/Attack_3.png", 5)

        self.state = "idle"
        self.previous_state = self.state
        self.frame_index = 0
        self.anim_timer = 0
        self.anim_speed_idle = 120
        self.anim_speed_walk = 80
        self.anim_speed_attack = 70

        self.vx = 0
        self.vy = 0
        self.speed = 5
        self.jump_impulse = -18
        self.on_ground = False
        self.facing_left = False

        self.on_wraith = False

        self.hit_margin_x = PLAYER_HIT_MARGIN_X
        self.hit_margin_y = PLAYER_HIT_MARGIN_Y

        self.attack_mode = None
        self.attack_chain = 0
        self.attack_queued = False

    def load_sheet(self, filename, count):
        sheet = pygame.image.load(filename).convert_alpha()
        frames = []
        for i in range(count):
            frame = sheet.subsurface(
                pygame.Rect(i * self.frame_width, 0, self.frame_width, self.frame_height)
            )
            frames.append(frame)
        return frames

    def get_rect(self):
        margin_x = self.hit_margin_x
        margin_y = self.hit_margin_y

        return pygame.Rect(
            self.x - self.frame_width // 2 + margin_x,
            self.y - self.frame_height // 2 + margin_y,
            self.frame_width - margin_x * 2,
            self.frame_height - margin_y * 2,
        )

    def get_attack_hitbox(self):
        if not self.attack_mode:
            return None

        spec = {
            "attack1": {"frames": (2, 3), "reach": 10, "w": 40, "h": 44},
            "attack2": {"frames": (2, 3), "reach": 12, "w": 44, "h": 48},
            "attack3": {"frames": (2, 4), "reach": 14, "w": 48, "h": 50},
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

    def handle_input(self, keys, mouse_buttons):
        self.vx = 0

        if self.attack_mode is None:
            if keys[pygame.K_LEFT] or keys[pygame.K_a]:
                self.vx = -self.speed
                self.facing_left = True
            elif keys[pygame.K_RIGHT] or keys[pygame.K_d]:
                self.vx = self.speed
                self.facing_left = False

        if (
            (keys[pygame.K_SPACE] or keys[pygame.K_w] or keys[pygame.K_UP])
            and self.on_ground
            and self.attack_mode is None
        ):
            self.vy = self.jump_impulse
            self.on_wraith = False

        left_click = mouse_buttons[0]

        if left_click:
            if self.attack_mode is None:
                self.attack_mode = f"attack{self.attack_chain + 1}"
                self.attack_queued = False
                self.frame_index = 0
                self.anim_timer = 0
                self.vx = 0
            else:
                if not self.attack_queued:
                    self.attack_queued = True

    def update(self, dt, solids):
        if not self.on_wraith:
            move_with_collisions(self, solids)
        else:
            self.x += self.vx
            self.vy = 0
            self.on_ground = True

        if self.attack_mode is None:
            if self.on_ground and abs(self.vx) > 0.1:
                self.state = "walk"
            elif self.on_ground:
                self.state = "idle"
            else:
                if self.state not in ("walk", "idle"):
                    self.state = "idle"

            if self.state != self.previous_state:
                self.frame_index = 0
                self.anim_timer = 0
                self.previous_state = self.state

        if self.attack_mode is not None:
            if self.attack_mode == "attack1":
                frames = self.attack1_frames
            elif self.attack_mode == "attack2":
                frames = self.attack2_frames
            else:
                frames = self.attack3_frames
            speed = self.anim_speed_attack
        else:
            if self.state == "walk":
                frames = self.walk_frames
                speed = self.anim_speed_walk
            else:
                frames = self.idle_frames
                speed = self.anim_speed_idle

        self.anim_timer += dt
        if self.anim_timer >= speed:
            self.anim_timer = 0
            self.frame_index += 1

            if self.attack_mode is not None:
                if self.frame_index >= len(frames):
                    if self.attack_mode.startswith("attack") and self.attack_queued:
                        self.attack_chain = (self.attack_chain + 1) % 3
                        self.attack_mode = f"attack{self.attack_chain + 1}"
                        self.frame_index = 0
                        self.attack_queued = False
                    else:
                        self.attack_mode = None
                        self.attack_chain = 0
                        self.frame_index = 0
            else:
                self.frame_index %= len(frames)

    def draw(self, surface, camera_x=0):
        if self.attack_mode is not None:
            if self.attack_mode == "attack1":
                frames = self.attack1_frames
            elif self.attack_mode == "attack2":
                frames = self.attack2_frames
            else:
                frames = self.attack3_frames
        elif self.state == "walk":
            frames = self.walk_frames
        else:
            frames = self.idle_frames

        idx = min(self.frame_index, len(frames) - 1)
        frame = frames[idx]
        if self.facing_left:
            frame = pygame.transform.flip(frame, True, False)

        surface.blit(
            frame,
            (
                self.x - self.frame_width // 2 - camera_x,
                self.y - self.frame_height // 2 - self.hit_margin_y,
            ),
        )

        if DEBUG_BOXES:
            pygame.draw.rect(surface, (0, 255, 0), self.get_rect(), 1)
            atk = self.get_attack_hitbox()
            if atk:
                pygame.draw.rect(surface, (0, 255, 255), atk, 1)


def resolve_player_vs_wraith_horizontal(player, prev_rect, wraith):
    p_rect = player.get_rect()
    w_rect = wraith.get_solidbox()

    if not p_rect.colliderect(w_rect):
        return

    if prev_rect.right <= w_rect.left < p_rect.right:
        p_rect.right = w_rect.left
        player.x = p_rect.centerx
        if player.vx > 0:
            player.vx = 0
        return

    if prev_rect.left >= w_rect.right > p_rect.left:
        p_rect.left = w_rect.right
        player.x = p_rect.centerx
        if player.vx < 0:
            player.vx = 0
        return


def land_player_on_wraith_from_above(player, prev_rect, wraith):
    p_rect = player.get_rect()
    w_rect = wraith.get_solidbox()

    if player.vy < 0:
        return False

    if p_rect.right <= w_rect.left or p_rect.left >= w_rect.right:
        return False

    if prev_rect.bottom > w_rect.top:
        return False

    if p_rect.bottom < w_rect.top:
        return False

    p_rect.bottom = w_rect.top - LAND_OFFSET
    player.y = p_rect.centery
    player.vy = 0
    player.vx = 0
    player.on_ground = True
    player.on_wraith = True
    wraith.has_rider = True
    return True


def main():
    clock = pygame.time.Clock()

    player_start_y = SCREEN_HEIGHT - TILE_SIZE - 64
    player = Player(SCREEN_WIDTH // 2, player_start_y)

    wraith = Wraith(
        x=SCREEN_WIDTH - 150,
        y=SCREEN_HEIGHT - TILE_SIZE - 128 + 30,
        idle_folder="Wraith1Idle",
        walk_folder="Wraith1Walking",
        anim_speed=100,
        hover_amplitude=8,
        hover_speed=0.005,
    )

    running = True
    while running:
        dt = clock.tick(FPS)
        now = pygame.time.get_ticks()

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False

        keys = pygame.key.get_pressed()
        mouse_buttons = pygame.mouse.get_pressed()

        prev_player_rect = player.get_rect()

        wraith.chase(player.x)
        wraith.update(dt, now, player)

        if not player.on_wraith and wraith.get_solidbox().colliderect(prev_player_rect):
            wraith.x -= wraith.last_step

        solids = list(bridge_blocks)
        player.handle_input(keys, mouse_buttons)
        player.update(dt, solids)

        if player.on_wraith:
            w_rect = wraith.get_solidbox()
            p_rect = player.get_rect()
            p_rect.bottom = w_rect.top - LAND_OFFSET
            player.y = p_rect.centery
            player.vy = 0
            player.on_ground = True
            wraith.has_rider = True

            if p_rect.right <= w_rect.left or p_rect.left >= w_rect.right:
                player.on_wraith = False
                wraith.has_rider = False

        landed = land_player_on_wraith_from_above(player, prev_player_rect, wraith)

        if not landed and not player.on_wraith:
            wraith.has_rider = False
            resolve_player_vs_wraith_horizontal(player, prev_player_rect, wraith)

        screen.blit(background_image, (0, 0))
        for block in bridge_blocks:
            screen.blit(gothic_tile, (block.x, block.y))

        camera_x = 0
        wraith.draw(screen, camera_x, DEBUG_BOXES)
        player.draw(screen, camera_x)

        pygame.display.flip()

    pygame.quit()
    sys.exit()


if __name__ == "__main__":
    main()