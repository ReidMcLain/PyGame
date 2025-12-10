import pygame
import math

WRAITH_SOLID_OX = 30
WRAITH_SOLID_OY = 30
WRAITH_SOLID_W  = 70
WRAITH_SOLID_H  = 90


class Wraith:
    def __init__(self, x, y, idle_folder, walk_folder, anim_speed, hover_amplitude, hover_speed):
        self.x = x
        self.y = y

        self.anim_speed = anim_speed
        self.hover_amplitude = hover_amplitude
        self.hover_speed = hover_speed

        # Animations
        self.idle_frames = self._load_seq(idle_folder, "Wraith_01_Idle_{i:03}.png", 12, (128, 129))
        self.walk_frames = self._load_seq(
            walk_folder, "Wraith_01_Moving Forward_{i:03}.png", 12, (128, 129)
        )
        self.hurt_frames = self._load_seq(
            "Wraith1Hurt", "Wraith_01_Hurt_{i:03}.png", 12, (128, 129)
        )
        self.dying_frames = self._load_seq(
            "Wraith1Dying", "Wraith_01_Dying_{i:03}.png", 15, (128, 129)
        )

        self.frames = self.idle_frames
        self.frame_index = 0
        self.anim_timer = 0

        # State
        self.state = "idle"   # "idle", "walk", "hurt", "dying", "dead"
        self.facing_left = False
        self.speed = 1.0

        # Hovering
        self.hover_time = 0
        self.hover_offset = 0

        # Movement bookkeeping
        self.last_step = 0
        self.has_rider = False

        # Hurt / knockback / invulnerability
        self.invuln_until = 0
        self.knockback_vx = 0

        # Health
        self.max_health = 3
        self.health = 3
        self.alive = True

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
        # Once dead, no longer collidable
        if not self.alive:
            return pygame.Rect(0, 0, 0, 0)

        ox = WRAITH_SOLID_OX
        oy = WRAITH_SOLID_OY
        w = WRAITH_SOLID_W
        h = WRAITH_SOLID_H
        return pygame.Rect(self.x + ox, self.y + oy, w, h)

    def get_hurtbox(self):
        return self.get_solidbox()

    def _maybe_take_hit(self, now, player):
        if not self.alive or self.state == "dying":
            return

        if now < self.invuln_until:
            return

        hitbox = player.get_attack_hitbox()
        if not hitbox:
            return

        if not hitbox.colliderect(self.get_hurtbox()):
            return

        # We got hit
        self.health -= 1
        if self.health < 0:
            self.health = 0

        if self.health == 0:
            # Start dying animation
            self.state = "dying"
            self.frames = self.dying_frames
            self.frame_index = 0
            self.anim_timer = 0
            self.knockback_vx = 0
            # Optional: long invuln to avoid re-processing in same frame
            self.invuln_until = now + 9999
        else:
            # Normal hurt reaction
            self.state = "hurt"
            self.frames = self.hurt_frames
            self.frame_index = 0
            self.anim_timer = 0
            self.invuln_until = now + 300  # ms of i-frames
            self.knockback_vx = -4 if player.facing_left else 4

    def chase(self, player_x):
        self.last_step = 0

        # Don't chase if riding, hurt, dying, or dead
        if self.has_rider or self.state in ("hurt", "dying", "dead") or not self.alive:
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

    def update(self, dt, now, player):
        # Check if the player is hitting us
        self._maybe_take_hit(now, player)

        # Dead: no movement or animation updates
        if self.state == "dead":
            self.hover_offset = 0
            return

        # Hurt behavior
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

            # Keep hovering visually
            self.hover_time += dt
            self.hover_offset = math.sin(self.hover_time * self.hover_speed) * self.hover_amplitude
            return

        # Dying behavior
        if self.state == "dying":
            self.anim_timer += dt
            if self.anim_timer >= 70:
                self.anim_timer = 0
                self.frame_index += 1
                if self.frame_index >= len(self.dying_frames):
                    # Stay on last frame, mark as dead
                    self.frame_index = len(self.dying_frames) - 1
                    self.state = "dead"
                    self.alive = False

            # Option: freeze hover while dying
            self.hover_offset = 0
            return

        # Normal idle/walk animation
        self.anim_timer += dt
        if self.anim_timer >= self.anim_speed:
            self.anim_timer = 0
            self.frame_index = (self.frame_index + 1) % len(self.frames)

        # Hovering
        if self.has_rider:
            self.hover_offset = 0
        else:
            self.hover_time += dt
            self.hover_offset = math.sin(self.hover_time * self.hover_speed) * self.hover_amplitude

    def draw(self, surface, camera_x=0, debug_boxes=False):
        frame = self.frames[self.frame_index]
        if self.facing_left:
            frame = pygame.transform.flip(frame, True, False)

        surface.blit(
            frame,
            (self.x - camera_x, self.y + self.hover_offset),
        )

        # Tiny health bar above the wraith
        if self.alive or self.state == "dying":
            box = self.get_solidbox()
            if box.width > 0 and box.height > 0:
                bar_width = 40
                bar_height = 4
                frac = self.health / self.max_health if self.max_health > 0 else 0
                if frac < 0:
                    frac = 0

                bar_x = box.centerx - bar_width // 2 - camera_x
                bar_y = box.top - 10

                bg_rect = pygame.Rect(bar_x, bar_y, bar_width, bar_height)
                fg_rect = pygame.Rect(bar_x, bar_y, int(bar_width * frac), bar_height)

                pygame.draw.rect(surface, (0, 0, 0), bg_rect)
                pygame.draw.rect(surface, (200, 0, 0), fg_rect)

        if debug_boxes:
            pygame.draw.rect(surface, (255, 0, 0), self.get_solidbox(), 1)
            pygame.draw.rect(surface, (255, 255, 0), self.get_hurtbox(), 1)