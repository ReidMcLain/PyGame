import pygame
from settings import *
from assets import player_image_original, player_image_flipped

class Player:
    def __init__(self):
        self.x = LEVEL_WIDTH - PLAYER_WIDTH - 20
        self.y = LEVEL_HEIGHT - PLAYER_HEIGHT - 10
        self.vx = 0
        self.vy = 0
        self.on_ground = False
        self.rect = pygame.Rect(self.x, self.y, PLAYER_WIDTH, PLAYER_HEIGHT)
        self.coyote_timer = 0
        self.facing_right = False
        self.health = MAX_HEALTH
        self.hit_cooldown = 0

    def handle_input(self, keys):
        self.vx = 0
        if keys[pygame.K_a]:
            self.vx = -PLAYER_SPEED
            self.facing_right = False
        if keys[pygame.K_d]:
            self.vx = PLAYER_SPEED
            self.facing_right = True
        if keys[pygame.K_SPACE] and (self.on_ground or self.coyote_timer > 0):
            self.vy = JUMP_STRENGTH
            self.coyote_timer = 0

    def update(self, platforms, enemies):
        self.vy += GRAVITY
        self.x += self.vx
        self.rect.x = int(self.x)

        # Horizontal collisions
        for platform in platforms:
            if self.rect.colliderect(platform):
                if self.vx > 0:
                    self.rect.right = platform.left
                    self.x = self.rect.x
                elif self.vx < 0:
                    self.rect.left = platform.right
                    self.x = self.rect.x

        self.y += self.vy
        self.rect.y = int(self.y)
        self.on_ground = False

        # Vertical collisions
        for platform in platforms:
            if self.rect.colliderect(platform):
                if self.vy > 0:
                    self.rect.bottom = platform.top
                    self.y = self.rect.y
                    self.vy = 0
                    self.on_ground = True
                elif self.vy < 0:
                    self.rect.top = platform.bottom
                    self.y = self.rect.y
                    self.vy = 0

        # Coyote time logic
        if self.on_ground:
            self.coyote_timer = COYOTE_TIME
        elif self.coyote_timer > 0:
            self.coyote_timer -= 1

        # Hit cooldown
        if self.hit_cooldown > 0:
            self.hit_cooldown -= 1

        # Enemy collisions and conditional damage logic
        for enemy in enemies:
            if enemy.is_alive and self.rect.colliderect(enemy.rect):
                if self.vy > 0 and self.rect.bottom <= enemy.rect.top + 20:
                    # Mario-style stomp
                    enemy.take_damage(1)
                    self.vy = JUMP_STRENGTH
                elif self.hit_cooldown == 0:
                    # Check if enemy is moving toward the player
                    player_center = self.rect.centerx
                    enemy_center = enemy.rect.centerx

                    is_player_right = player_center > enemy_center
                    is_enemy_moving_right = enemy.vx > 0

                    if (is_player_right and is_enemy_moving_right) or \
                       (not is_player_right and not is_enemy_moving_right):
                        # Enemy is moving toward player → apply damage
                        self.health -= 1
                        self.hit_cooldown = 60

    def draw(self, screen, camera_x, camera_y):
        if self.facing_right:
            screen.blit(player_image_flipped, (round(self.rect.x - camera_x), round(self.rect.y - camera_y)))
        else:
            screen.blit(player_image_original, (round(self.rect.x - camera_x), round(self.rect.y - camera_y)))