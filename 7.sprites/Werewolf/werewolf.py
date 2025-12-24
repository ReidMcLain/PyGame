import pygame
import sys

from physics import move_with_collisions
from wraith import Wraith
from level_manager import LevelManager

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

        self.hurt_frames = self.load_sheet("assets/WerewolfAnimations/Hurt.png", 2)
        self.dead_frames = self.load_sheet("assets/WerewolfAnimations/Dead.png", 2)

        self.state = "idle"
        self.previous_state = self.state
        self.frame_index = 0
        self.anim_timer = 0
        self.anim_speed_idle = 120
        self.anim_speed_walk = 80
        self.anim_speed_attack = 70
        self.anim_speed_hurt = 80
        self.anim_speed_dead = 120

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

        self.max_health = 100
        self.health = 100
        self.invuln_until = 0
        self.iframes_ms = 600

        self.hurt_lock_frames = 2
        self.hurt_lock_remaining = 0

        self.dead = False

    def load_sheet(self, filename, count):
        sheet = pygame.image.load(filename).convert_alpha()
        frames = []
        for i in range(count):
            frame = sheet.subsurface(pygame.Rect(i * self.frame_width, 0, self.frame_width, self.frame_height))
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

    def take_damage(self, amount, now):
        if self.dead:
            return False
        if now < self.invuln_until:
            return False

        self.health -= amount
        if self.health < 0:
            self.health = 0

        self.invuln_until = now + self.iframes_ms
        self.hurt_lock_remaining = self.hurt_lock_frames

        if self.health == 0:
            self.dead = True
            self.state = "dead"
            self.previous_state = "dead"
            self.attack_mode = None
            self.attack_chain = 0
            self.attack_queued = False
            self.frame_index = 0
            self.anim_timer = 0

        return True

    def handle_input(self, keys, mouse_buttons):
        if self.dead:
            self.vx = 0
            return

        if self.hurt_lock_remaining > 0:
            self.vx = 0
            return

        self.vx = 0

        if self.attack_mode is None:
            if keys[pygame.K_LEFT] or keys[pygame.K_a]:
                self.vx = -self.speed
                self.facing_left = True
            elif keys[pygame.K_RIGHT] or keys[pygame.K_d]:
                self.vx = self.speed
                self.facing_left = False

        if (keys[pygame.K_SPACE] or keys[pygame.K_w] or keys[pygame.K_UP]) and self.on_ground and self.attack_mode is None:
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
        if self.dead:
            self.vx = 0
            self.vy = 0
            self.anim_timer += dt
            if self.anim_timer >= self.anim_speed_dead:
                self.anim_timer = 0
                if self.frame_index < len(self.dead_frames) - 1:
                    self.frame_index += 1
            return

        move_with_collisions(self, solids)

        if self.hurt_lock_remaining > 0:
            self.hurt_lock_remaining -= 1

        if self.hurt_lock_remaining > 0:
            self.state = "hurt"
            frames = self.hurt_frames
            speed = self.anim_speed_hurt
        else:
            if self.attack_mode is not None:
                if self.attack_mode == "attack1":
                    frames = self.attack1_frames
                elif self.attack_mode == "attack2":
                    frames = self.attack2_frames
                else:
                    frames = self.attack3_frames
                speed = self.anim_speed_attack
            else:
                if self.on_ground and abs(self.vx) > 0.1:
                    self.state = "walk"
                elif self.on_ground:
                    self.state = "idle"
                else:
                    if self.state not in ("walk", "idle"):
                        self.state = "idle"

                if self.state == "walk":
                    frames = self.walk_frames
                    speed = self.anim_speed_walk
                else:
                    frames = self.idle_frames
                    speed = self.anim_speed_idle

        if self.attack_mode is None and self.state in ("idle", "walk"):
            if self.state != self.previous_state:
                self.frame_index = 0
                self.anim_timer = 0
                self.previous_state = self.state

        self.anim_timer += dt
        if self.anim_timer >= speed:
            self.anim_timer = 0
            self.frame_index += 1

            if self.hurt_lock_remaining > 0:
                if self.frame_index >= len(frames):
                    self.frame_index = 0
            elif self.attack_mode is not None:
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
        if self.dead:
            frames = self.dead_frames
        elif self.hurt_lock_remaining > 0:
            frames = self.hurt_frames
        elif self.attack_mode is not None:
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
    return False


def draw_player_hud(surface, player, level_manager):
    bar_x = 20
    bar_y = 20
    bar_w = 240
    bar_h = 18

    frac = player.health / player.max_health if player.max_health > 0 else 0
    if frac < 0:
        frac = 0
    if frac > 1:
        frac = 1

    bg = pygame.Rect(bar_x, bar_y, bar_w, bar_h)
    fg = pygame.Rect(bar_x, bar_y, int(bar_w * frac), bar_h)

    pygame.draw.rect(surface, (0, 0, 0), bg)
    pygame.draw.rect(surface, (180, 0, 0), fg)

    font = pygame.font.SysFont(None, 22)
    text = font.render(f"HP: {player.health}/{player.max_health}", True, (255, 255, 255))
    surface.blit(text, (bar_x, bar_y + bar_h + 6))

    font2 = pygame.font.SysFont(None, 28)
    lvl = font2.render(f"Level: {level_manager.level}", True, (255, 255, 255))
    surface.blit(lvl, (bar_x, bar_y + bar_h + 30))


def draw_game_over(surface, level_manager):
    font = pygame.font.SysFont(None, 56)
    font2 = pygame.font.SysFont(None, 28)

    msg = font.render("GAME OVER", True, (255, 255, 255))
    msg2 = font2.render(f"You reached level {level_manager.reached_level()}", True, (255, 255, 255))
    msg3 = font2.render("Press ESC to quit", True, (255, 255, 255))

    surface.blit(msg, (SCREEN_WIDTH // 2 - msg.get_width() // 2, SCREEN_HEIGHT // 2 - 80))
    surface.blit(msg2, (SCREEN_WIDTH // 2 - msg2.get_width() // 2, SCREEN_HEIGHT // 2 - 20))
    surface.blit(msg3, (SCREEN_WIDTH // 2 - msg3.get_width() // 2, SCREEN_HEIGHT // 2 + 20))


def spawn_wraith_at(x):
    return Wraith(
        x=x,
        y=SCREEN_HEIGHT - TILE_SIZE - 128 + 30,
        idle_folder="Wraith1Idle",
        walk_folder="Wraith1Walking",
        anim_speed=100,
        hover_amplitude=8,
        hover_speed=0.005,
    )


def main():
    clock = pygame.time.Clock()

    player_start_y = SCREEN_HEIGHT - TILE_SIZE - 64
    player = Player(SCREEN_WIDTH // 2, player_start_y)

    level_manager = LevelManager(
        SCREEN_WIDTH,
        SCREEN_HEIGHT,
        fade_out_ms=700,
        fade_in_ms=400,
        breather_ms=3000,
        spawn_min_dist=250,
        spawn_max_dist=450,
        edge_margin=90,
    )

    wraiths = []

    running = True
    while running:
        dt = clock.tick(FPS)
        now = pygame.time.get_ticks()

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
            elif event.type == pygame.KEYDOWN:
                if event.key == pygame.K_F1:
                    global DEBUG_BOXES
                    DEBUG_BOXES = not DEBUG_BOXES

        keys = pygame.key.get_pressed()
        mouse_buttons = pygame.mouse.get_pressed()

        if level_manager.is_game_over():
            if keys[pygame.K_ESCAPE]:
                running = False

            screen.blit(background_image, (0, 0))
            for block in bridge_blocks:
                screen.blit(gothic_tile, (block.x, block.y))

            for w in wraiths:
                w.draw(screen, 0, DEBUG_BOXES)
            player.draw(screen, 0)

            draw_game_over(screen, level_manager)
            pygame.display.flip()
            continue

        level_manager.begin_level_if_needed(now, player.x)
        spawn_xs = level_manager.consume_spawn_queue()
        if spawn_xs:
            wraiths = [spawn_wraith_at(x) for x in spawn_xs]

        transition_locked = level_manager.is_transition_locked()

        prev_player_rect = player.get_rect()

        if not transition_locked:
            for w in wraiths:
                w.chase(player.x)
                w.update(dt, now, player)
        else:
            for w in wraiths:
                w.last_step = 0

        solids = list(bridge_blocks)

        if not transition_locked:
            player.handle_input(keys, mouse_buttons)
            player.update(dt, solids)
        else:
            player.vx = 0
            player.vy = 0
            player.attack_mode = None
            player.attack_chain = 0
            player.attack_queued = False
            player.update(0, solids)

        for w in wraiths:
            if w.get_solidbox().colliderect(prev_player_rect) and w.last_step != 0:
                w.x -= w.last_step

        for w in wraiths:
            resolve_player_vs_wraith_horizontal(player, prev_player_rect, w)

        level_manager.notify_level_clear_if_ready(now, wraiths)
        level_manager.update(now)

        if player.dead and player.frame_index >= len(player.dead_frames) - 1:
            level_manager.trigger_game_over()

        screen.blit(background_image, (0, 0))
        for block in bridge_blocks:
            screen.blit(gothic_tile, (block.x, block.y))

        camera_x = 0
        for w in wraiths:
            w.draw(screen, camera_x, DEBUG_BOXES)
        player.draw(screen, camera_x)

        draw_player_hud(screen, player, level_manager)
        level_manager.draw_fade(screen)

        pygame.display.flip()

    pygame.quit()
    sys.exit()


if __name__ == "__main__":
    main()