# sword.py
import pygame
from assets import sword_image, SWORD_SIZE

class Sword:
    def __init__(self, player):
        self.player = player
        self.angle = 0
        self.swing_timer = 0
        self.has_hit_enemy_this_swing = False

    def start_swing(self):
        if self.swing_timer == 0:
            self.angle = 45
            self.swing_timer = 15
            self.has_hit_enemy_this_swing = False

    def update(self):
        if self.swing_timer > 0:
            self.swing_timer -= 1
            if self.swing_timer == 10:
                self.angle = 90
            elif self.swing_timer == 5:
                self.angle = 45
            elif self.swing_timer == 0:
                self.angle = 0
                self.has_hit_enemy_this_swing = False

    def draw(self, screen, camera_x, camera_y, enemy):
        if self.player.sword is not self:
            return

        if self.player.facing_right:
            sword_img = sword_image
            offset_x = 20
        else:
            sword_img = pygame.transform.flip(sword_image, True, False)
            offset_x = -20

        swing_angle = self.angle if self.player.facing_right else -self.angle
        sword_rotated = pygame.transform.rotate(sword_img, -swing_angle)
        sword_rect_draw = sword_rotated.get_rect(center=(
            self.player.rect.centerx - camera_x + offset_x,
            self.player.rect.centery - 20 - camera_y
        ))
        screen.blit(sword_rotated, sword_rect_draw)

        # Damage logic
        sword_world_rect = sword_rect_draw.move(camera_x, camera_y)
        if self.swing_timer > 0 and enemy.is_alive and not self.has_hit_enemy_this_swing:
            if sword_world_rect.colliderect(enemy.rect):
                enemy.take_damage(10)
                self.has_hit_enemy_this_swing = True