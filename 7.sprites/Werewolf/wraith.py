import pygame
import math
import os

WRAITH_SOLID_OX = 30
WRAITH_SOLID_OY = 30
WRAITH_SOLID_W = 70
WRAITH_SOLID_H = 90


class Wraith:
    def __init__(self, x, y, idle_folder, walk_folder, anim_speed, hover_amplitude, hover_speed):
        self.x = x
        self.y = y

        self.anim_speed = anim_speed
        self.hover_amplitude = hover_amplitude
        self.hover_speed = hover_speed

        self.idle_frames = self._load_seq_flexible(
            idle_folder,
            patterns=["Wraith_01_Idle_{i:03}.png", "Wraith_01_Idle_{i:04}.png"],
            count=12,
            size=(128, 129),
        )
        self.walk_frames = self._load_seq_flexible(
            walk_folder,
            patterns=[
                "Wraith_01_Moving Forward_{i:03}.png",
                "Wraith_01_Moving_Forward_{i:03}.png",
                "Wraith_01_Walk_{i:03}.png",
                "Wraith_01_Walking_{i:03}.png",
            ],
            count=12,
            size=(128, 129),
        )
        self.attack_frames = self._load_seq_flexible(
            "Wraith1Attack",
            patterns=["Wraith_01_Attack_{i:03}.png", "Wraith_01_Attack_{i:04}.png"],
            count=12,
            size=(128, 129),
        )
        self.hurt_frames = self._load_seq_flexible(
            "Wraith1Hurt",
            patterns=["Wraith_01_Hurt_{i:03}.png", "Wraith_01_Hurt_{i:04}.png"],
            count=12,
            size=(128, 129),
        )
        self.dying_frames = self._load_seq_flexible(
            "Wraith1Dying",
            patterns=["Wraith_01_Dying_{i:03}.png", "Wraith_01_Dying_{i:04}.png"],
            count=15,
            size=(128, 129),
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

        self.invuln_until = 0
        self.knockback_vx = 0

        self.max_health = 3
        self.health = 3
        self.alive = True

        self.attack_frame_start = 5
        self.attack_frame_end = 7
        self.attack_damage = 10
        self.attack_cooldown_ms = 900
        self.attack_range_pad = 6
        self.next_attack_allowed_at = 0
        self.attack_has_hit = False

    def _folder_path(self, folder):
        return os.path.join("assets", folder)

    def _try_load_indexed(self, folder, pattern, count, size):
        frames = []
        base = self._folder_path(folder)

        for start in (0, 1):
            frames.clear()
            ok = True
            for k in range(count):
                i = start + k
                fn = os.path.join(base, pattern.format(i=i))
                if not os.path.exists(fn):
                    ok = False
                    break
                img = pygame.image.load(fn).convert_alpha()
                img = pygame.transform.scale(img, size)
                frames.append(img)
            if ok and len(frames) == count:
                return frames

        return None

    def _load_seq_flexible(self, folder, patterns, count, size):
        base = self._folder_path(folder)

        for pat in patterns:
            frames = self._try_load_indexed(folder, pat, count, size)
            if frames:
                return frames

        if not os.path.isdir(base):
            raise FileNotFoundError(f"Missing folder: {base}")

        pngs = [f for f in os.listdir(base) if f.lower().endswith(".png")]
        pngs.sort()
        if len(pngs) < count:
            raise FileNotFoundError(f"Not enough png files in {base}. Need {count}, found {len(pngs)}.")

        frames = []
        for name in pngs[:count]:
            fn = os.path.join(base, name)
            img = pygame.image.load(fn).convert_alpha()
            img = pygame.transform.scale(img, size)
            frames.append(img)
        return frames

    def get_solidbox(self):
        if not self.alive:
            return pygame.Rect(0, 0, 0, 0)

        return pygame.Rect(self.x + WRAITH_SOLID_OX, self.y + WRAITH_SOLID_OY, WRAITH_SOLID_W, WRAITH_SOLID_H)

    def get_hurtbox(self):
        return self.get_solidbox()

    def get_attack_box(self):
        box = self.get_solidbox()
        if box.width == 0:
            return box
        pad = self.attack_range_pad
        return pygame.Rect(box.x - pad, box.y - pad, box.width + pad * 2, box.height + pad * 2)

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

        self.health -= 1
        if self.health < 0:
            self.health = 0

        if self.health == 0:
            self.state = "dying"
            self.frames = self.dying_frames
            self.frame_index = 0
            self.anim_timer = 0
            self.knockback_vx = 0
            self.invuln_until = now + 9999
        else:
            self.state = "hurt"
            self.frames = self.hurt_frames
            self.frame_index = 0
            self.anim_timer = 0
            self.invuln_until = now + 300
            self.knockback_vx = -4 if player.facing_left else 4

    def _maybe_start_attack(self, now, player):
        if not self.alive or self.has_rider:
            return
        if self.state in ("hurt", "dying", "dead", "attack"):
            return
        if now < self.next_attack_allowed_at:
            return

        if self.get_attack_box().colliderect(player.get_rect()):
            self.state = "attack"
            self.frames = self.attack_frames
            self.frame_index = 0
            self.anim_timer = 0
            self.attack_has_hit = False
            self.last_step = 0

    def _attack_damage_window(self, player, now):
        if self.attack_has_hit:
            return
        if not (self.attack_frame_start <= self.frame_index <= self.attack_frame_end):
            return

        if self.get_attack_box().colliderect(player.get_rect()):
            if player.take_damage(self.attack_damage, now):
                self.attack_has_hit = True

    def chase(self, player_x):
        self.last_step = 0

        if self.has_rider or self.state in ("hurt", "dying", "dead", "attack") or not self.alive:
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
        self._maybe_take_hit(now, player)

        if self.state == "dead":
            self.hover_offset = 0
            return

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

        if self.state == "dying":
            self.anim_timer += dt
            if self.anim_timer >= 70:
                self.anim_timer = 0
                self.frame_index += 1
                if self.frame_index >= len(self.dying_frames):
                    self.frame_index = len(self.dying_frames) - 1
                    self.state = "dead"
                    self.alive = False
            self.hover_offset = 0
            return

        self._maybe_start_attack(now, player)

        if self.state == "attack":
            self.anim_timer += dt
            if self.anim_timer >= 70:
                self.anim_timer = 0
                self.frame_index += 1
                if self.frame_index >= len(self.attack_frames):
                    self.state = "idle"
                    self.frames = self.idle_frames
                    self.frame_index = 0
                    self.next_attack_allowed_at = now + self.attack_cooldown_ms
                    self.attack_has_hit = False
                    return

            self._attack_damage_window(player, now)
            self.hover_time += dt
            self.hover_offset = math.sin(self.hover_time * self.hover_speed) * self.hover_amplitude
            return

        self.anim_timer += dt
        if self.anim_timer >= self.anim_speed:
            self.anim_timer = 0
            self.frame_index = (self.frame_index + 1) % len(self.frames)

        if self.has_rider:
            self.hover_offset = 0
        else:
            self.hover_time += dt
            self.hover_offset = math.sin(self.hover_time * self.hover_speed) * self.hover_amplitude

    def draw(self, surface, camera_x=0, debug_boxes=False):
        frame = self.frames[self.frame_index]
        if self.facing_left:
            frame = pygame.transform.flip(frame, True, False)

        surface.blit(frame, (self.x - camera_x, self.y + self.hover_offset))

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

            if self.state == "attack":
                pygame.draw.rect(surface, (255, 0, 255), self.get_attack_box(), 1)
            else:
                pygame.draw.rect(surface, (120, 0, 120), self.get_attack_box(), 1)