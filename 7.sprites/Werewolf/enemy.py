import pygame
import math

class Enemy:
    def __init__(self, x, y, idle_frames, walk_frames, anim_speed, hover_amplitude, hover_speed, player_ref):
        self.x = x
        self.y = y
        self.idle_frames = idle_frames
        self.walk_frames = walk_frames
        self.frames = idle_frames  # Default to idle
        self.anim_speed = anim_speed
        self.hover_amplitude = hover_amplitude
        self.hover_speed = hover_speed
        self.base_y = y
        self.hover_time = 0

        self.frame_index = 0
        self.anim_timer = 0

        self.player_ref = player_ref

    def chase(self, player_x):
        # Determine whether enemy should move
        if abs(player_x - self.x) > 5:
            self.frames = self.walk_frames
            if player_x < self.x:
                self.x -= 1
            elif player_x > self.x:
                self.x += 1
        else:
            self.frames = self.idle_frames

    def update(self, dt):
        self.anim_timer += dt
        if self.anim_timer >= self.anim_speed:
            self.anim_timer = 0
            self.frame_index = (self.frame_index + 1) % len(self.frames)
        self.hover_time += dt
        self.hover_offset = math.sin(self.hover_time * self.hover_speed) * self.hover_amplitude

    def draw(self, surface, camera_x):
        frame = self.frames[self.frame_index]
        facing_left = self.player_ref.x < self.x
        if facing_left:
            frame = pygame.transform.flip(frame, True, False)
        surface.blit(frame, (self.x - camera_x, self.y + self.hover_offset))