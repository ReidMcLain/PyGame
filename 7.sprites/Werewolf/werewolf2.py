import pygame
import sys
import math

from physics import move_with_collisions

pygame.init()

SCREEN_WIDTH, SCREEN_HEIGHT = 800, 600
FPS = 60
TILE_SIZE = 64

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

LAND_OFFSET = 45

DEBUG_BOXES = True


class Player:
    def __init__(self, x, y):
        self.x = x
        self.y = y

        self.frame_width = 128
        self.frame_height = 128

        self.idle_frames = self.load_sheet("assets/WerewolfAnimations/Idle.png", 8)
        self.walk_frames = self.load_sheet("assets/WerewolfAnimations/walk.png", 11)

        self.state = "idle"
        self.previous_state = self.state
        self.frame_index = 0
        self.anim_timer = 0
        self.anim_speed_idle = 120
        self.anim_speed_walk = 80

        self.vx = 0
        self.vy = 0
        self.speed = 5
        self.jump_impulse = -18
        self.on_ground = False
        self.facing_left = False

        self.on_wraith = False

    def load_sheet(self, filename, count):
        sheet = pygame.image.load(filename).convert_alpha()
        frames = []
        for i in range(count):
            frame = sheet.subsurface(
                pygame.Rect(i * self.frame_width, 0, self.frame_width, self.frame_height)
            )
            frames.append(frame)
        return frames
    
    # werewolf hitbox
    def get_rect(self):
        return pygame.Rect(
            self.x - self.frame_width // 2,
            self.y - self.frame_height // 2,
            self.frame_width ,
            self.frame_height,
        )

    def handle_input(self, keys):
        self.vx = 0

        if keys[pygame.K_LEFT] or keys[pygame.K_a]:
            self.vx = -self.speed
            self.facing_left = True
        elif keys[pygame.K_RIGHT] or keys[pygame.K_d]:
            self.vx = self.speed
            self.facing_left = False

        if (keys[pygame.K_SPACE] or keys[pygame.K_w] or keys[pygame.K_UP]) and self.on_ground:
            self.vy = self.jump_impulse
            self.on_wraith = False

    def update(self, dt, solids):
        if not self.on_wraith:
            move_with_collisions(self, solids)
        else:
            self.x += self.vx
            self.vy = 0
            self.on_ground = True

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

        if self.state == "walk":
            frames = self.walk_frames
            speed = self.anim_speed_walk
        else:
            frames = self.idle_frames
            speed = self.anim_speed_idle

        self.anim_timer += dt
        if self.anim_timer >= speed:
            self.anim_timer = 0
            self.frame_index = (self.frame_index + 1) % len(frames)

    def draw(self, surface, camera_x=0):
        if self.state == "walk":
            frames = self.walk_frames
        else:
            frames = self.idle_frames

        idx = min(self.frame_index, len(frames) - 1)
        frame = frames[idx]
        if self.facing_left:
            frame = pygame.transform.flip(frame, True, False)

        surface.blit(
            frame,
            (self.x - self.frame_width // 2 - camera_x,
             self.y - self.frame_height // 2),
        )

        if DEBUG_BOXES:
            pygame.draw.rect(surface, (0, 255, 0), self.get_rect(), 1)


class Wraith:
    def __init__(self, x, y, idle_folder, walk_folder, anim_speed, hover_amplitude, hover_speed):
        self.x = x
        self.y = y

        self.anim_speed = anim_speed
        self.hover_amplitude = hover_amplitude
        self.hover_speed = hover_speed

        self.idle_frames = self._load_seq(idle_folder, "Wraith_01_Idle_{i:03}.png", 12, (128, 129))
        self.walk_frames = self._load_seq(
            walk_folder, "Wraith_01_Moving Forward_{i:03}.png", 12, (128, 129)
        )

        self.frames = self.idle_frames
        self.frame_index = 0
        self.anim_timer = 0

        self.state = "idle"
        self.facing_left = False
        self.speed = 1.0

        self.hover_time = 0
        self.hover_offset = 0
        self.last_step = 0
        self.has_rider = False

    def _load_seq(self, folder, pattern, count, size):
        frames = []
        for i in range(count):
            img = pygame.image.load(
                f"assets/{folder}/{pattern.format(i=i)}"
            ).convert_alpha()
            img = pygame.transform.scale(img, size)
            frames.append(img)
        return frames

    def get_solidbox(self):
        ox = 60
        oy = 60
        w = 10
        h = 60
        return pygame.Rect(self.x + ox, self.y + oy, w, h)

    def chase(self, player_x):
        self.last_step = 0

        if self.has_rider:
            return

        dx = player_x - self.x
        if abs(dx) > 5:
            self.state = "walk"
            self.frames = self.walk_frames
            self.facing_left = dx < 0
            step = -self.speed if self.facing_left else self.speed
            self.x += step
            self.last_step = step
        else:
            self.state = "idle"
            self.frames = self.idle_frames

    def update(self, dt):
        self.anim_timer += dt
        if self.anim_timer >= self.anim_speed:
            self.anim_timer = 0
            self.frame_index = (self.frame_index + 1) % len(self.frames)

        if self.has_rider:
            self.hover_offset = 0
        else:
            self.hover_time += dt
            self.hover_offset = math.sin(self.hover_time * self.hover_speed) * self.hover_amplitude

    def draw(self, surface, camera_x=0):
        frame = self.frames[self.frame_index]
        if self.facing_left:
            frame = pygame.transform.flip(frame, True, False)

        surface.blit(
            frame,
            (self.x - camera_x, self.y + self.hover_offset),
        )

        if DEBUG_BOXES:
            pygame.draw.rect(surface, (255, 0, 0), self.get_solidbox(), 1)


def resolve_player_vs_wraith_horizontal(player, prev_rect, wraith):

    p_rect = player.get_rect()
    w_rect = wraith.get_solidbox()

    if not p_rect.colliderect(w_rect):
        return

    # From left
    if prev_rect.right <= w_rect.left < p_rect.right:
        p_rect.right = w_rect.left
        player.x = p_rect.left + player.frame_width // 2
        if player.vx > 0:
            player.vx = 0
        return

    # From right
    if prev_rect.left >= w_rect.right > p_rect.left:
        p_rect.left = w_rect.right
        player.x = p_rect.left + player.frame_width // 2
        if player.vx < 0:
            player.vx = 0
        return


def land_player_on_wraith_from_above(player, prev_rect, wraith):

    p_rect = player.get_rect()
    w_rect = wraith.get_solidbox()

    # must be falling
    if player.vy < 0:
        return False

    if p_rect.right <= w_rect.left or p_rect.left >= w_rect.right:
        return False

    if prev_rect.bottom > w_rect.top:
        return False

    if p_rect.bottom < w_rect.top:
        return False

    p_rect.bottom = w_rect.top - LAND_OFFSET
    player.y = p_rect.top + player.frame_height // 2
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

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False

        keys = pygame.key.get_pressed()

        prev_player_rect = player.get_rect()

        wraith.chase(player.x)
        wraith.update(dt)

        if not player.on_wraith and wraith.get_solidbox().colliderect(prev_player_rect):
            wraith.x -= wraith.last_step

        solids = list(bridge_blocks)
        player.handle_input(keys)
        player.update(dt, solids)

        if player.on_wraith:
            w_rect = wraith.get_solidbox()
            p_rect = player.get_rect()
            p_rect.bottom = w_rect.top - LAND_OFFSET
            player.y = p_rect.top + player.frame_height // 2
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
        player.draw(screen, camera_x)
        wraith.draw(screen, camera_x)

        pygame.display.flip()

    pygame.quit()
    sys.exit()


if __name__ == "__main__":
    main()
