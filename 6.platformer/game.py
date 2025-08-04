import pygame
import time
from settings import *
import assets  # use global variables from here
from assets import SWORD_SIZE
from platforms import platforms
from player import Player
from enemy import Enemy
from sword import Sword
import ui  # ✅ Leave this last to prevent potential circular import issues

class Game:
    def __init__(self):
        self.background_image = assets.background_image
        self.sword_image = assets.sword_image
        self.tile_swamp = assets.tile_swamp

        self.font_big = pygame.font.SysFont("monospace", 48)
        self.font_small = pygame.font.SysFont("monospace", 24)
        self.font_prompt = pygame.font.SysFont("monospace", 18, bold=True)

        self.player = Player()
        self.player.sword = None
        self.enemy = Enemy(1000, 200)

        sword_platform_index = 9
        sword_x = platforms[sword_platform_index].left - 900
        sword_y = platforms[sword_platform_index].y - (SWORD_SIZE * 2)
        self.sword_rect = pygame.Rect(sword_x, sword_y, SWORD_SIZE * 2, SWORD_SIZE * 2)

        self.camera_x = 0
        self.camera_y = 0
        self.running = True
        self.game_over = False
        self.player_won = False
        self.enemy1_defeated_timer = 0
        self.enemy1_heart_granted = False
        self.PARALLAX_FACTOR = 0.2

        # 🕒 Timer & Split System
        self.start_time = pygame.time.get_ticks()
        self.split_times = []
        self.timer_paused = False
        self.time_at_pause = 0

    def handle_events(self):
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                self.running = False

    def reset(self):
        self.player.health = MAX_HEALTH - 1
        self.player.max_unlocked_health = MAX_HEALTH - 1
        self.player.x = LEVEL_WIDTH - PLAYER_WIDTH - 32
        self.player.y = LEVEL_HEIGHT - PLAYER_HEIGHT - 32
        self.player.vx = 0
        self.player.vy = 0
        self.player.sword = None
        self.enemy = Enemy(1000, 200)
        self.game_over = False
        self.player_won = False
        self.enemy1_defeated_timer = 0
        self.enemy1_heart_granted = False

        # 🕒 Reset timer
        self.start_time = pygame.time.get_ticks()
        self.split_times = []
        self.timer_paused = False
        self.time_at_pause = 0

    def update(self):
        keys = pygame.key.get_pressed()
        self.player.handle_input(keys)
        self.player.update(platforms, [self.enemy])
        self.enemy.update()

        if self.player.sword:
            self.player.sword.update()

        if keys[pygame.K_e] and self.player.sword is None:
            if self.player.rect.colliderect(self.sword_rect):
                self.player.sword = Sword(self.player)

        if keys[pygame.K_e] and self.player.sword and self.player.sword.swing_timer == 0:
            self.player.sword.start_swing()

        if self.player.health <= 0:
            self.game_over = True
            self.player_won = False

        if self.enemy.current_health <= 0 and not self.game_over:
            self.game_over = True
            self.player_won = True
            self.enemy.is_alive = False

            # 🕒 Record first split (enemy defeated)
            split_time = pygame.time.get_ticks() - self.start_time
            self.split_times.append(split_time)
            self.time_at_pause = split_time
            self.timer_paused = True

        if self.game_over and self.enemy1_defeated_timer < 300:
            self.enemy1_defeated_timer += 1

        if self.game_over and self.enemy1_defeated_timer >= 300 and not self.enemy1_heart_granted:
            self.player.max_unlocked_health = MAX_HEALTH
            self.player.health = MAX_HEALTH
            self.enemy1_heart_granted = True

        self.camera_x = round(self.player.x - SCREEN_WIDTH // 2)
        self.camera_y = round(self.player.y - SCREEN_HEIGHT // 2)

    def draw(self, screen):
        bg_x = self.camera_x * self.PARALLAX_FACTOR
        screen.blit(self.background_image, (-max(0, min(bg_x,
                    self.background_image.get_width() - SCREEN_WIDTH)), 0))

        for platform in platforms:
            draw_x = platform.x - self.camera_x
            draw_y = platform.y - self.camera_y
            tiles_wide = (platform.width + 31) // 32
            tiles_tall = (platform.height + 31) // 32
            for tx in range(tiles_wide):
                for ty in range(tiles_tall):
                    screen.blit(self.tile_swamp, (draw_x + tx * 32, draw_y + ty * 32))

        if self.player.sword is None:
            screen.blit(self.sword_image, (self.sword_rect.x - self.camera_x, self.sword_rect.y - self.camera_y))
            ui.draw_prompt(screen, self.font_prompt, "[E]",
                           self.sword_rect.x, self.sword_rect.y, self.camera_x, self.camera_y)

        self.enemy.draw(screen, self.camera_x, self.camera_y)
        self.player.draw(screen, self.camera_x, self.camera_y)

        if self.player.sword:
            self.player.sword.draw(screen, self.camera_x, self.camera_y, self.enemy)

        ui.draw_hearts(screen, self.player.health, self.player.max_unlocked_health)

        # 🎯 Draw split timer (top right)
        def format_time(ms):
            s = ms // 1000
            m = s // 60
            return f"{m:02}:{s % 60:02}"

        current_time = self.time_at_pause if self.timer_paused else pygame.time.get_ticks() - self.start_time
        timer_surface = self.font_small.render(f"Time: {format_time(current_time)}", True, (255, 255, 255))
        screen.blit(timer_surface, (SCREEN_WIDTH - timer_surface.get_width() - 10, 10))

        if self.player_won and self.enemy1_defeated_timer < 300:
            ui.draw_game_outcome(screen, self.font_big, self.font_small, True)