import pygame
import os

class Player:
    def __init__(self, x, y, tiles_across):
        self.x = x
        self.y = y
        self.tiles_across = tiles_across

        self.frame_width = 128
        self.frame_height = 128
        self.ground_y = y

        self.walk_frames = self.load_sheet("walk.png", 11)
        self.idle_frames = self.load_sheet("Idle.png", 8)
        self.jump_frames = self.load_sheet("Jump.png", 11)
        self.run_frames = self.load_sheet("Run.png", 9)
        self.attack1_frames = self.load_sheet("Attack_1.png", 6)
        self.attack2_frames = self.load_sheet("Attack_2.png", 4)
        self.attack3_frames = self.load_sheet("Attack_3.png", 5)
        self.run_attack_frames = self.load_sheet("Run+Attack.png", 7)
        self.fireball_sheet = pygame.image.load("fireball.png").convert_alpha()
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

    def update(self, dt, keys):
        if not self.jumping and not self.attack_mode:
            self.mode = "run" if self.dx != 0 and (keys[pygame.K_LSHIFT] or keys[pygame.K_RSHIFT]) else "walk" if self.dx != 0 else "idle"

        if self.mode != self.previous_mode and self.mode != "jump" and not self.attack_mode:
            self.frame_index = 0
            self.animation_timer = 0
            self.previous_mode = self.mode

        if self.attack_mode == "runattack":
            self.x += self.attack_dx
        else:
            self.x += self.dx

        self.x = max(0, min(self.x, self.tiles_across * 64 - self.frame_width // 2))

        if self.jumping:
            self.velocity_y += self.gravity
            self.y += self.velocity_y
            if keys[pygame.K_LEFT] or keys[pygame.K_a]:
                self.x -= 5
                self.facing_left = True
            elif keys[pygame.K_RIGHT] or keys[pygame.K_d]:
                self.x += 5
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
            screen.blit(fb_img, (fb["x"] - fb_img.get_width() // 2 - camera_x, fb["y"] - fb_img.get_height() // 2))

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