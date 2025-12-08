# physics.py
import pygame


GRAVITY = 1.2
MAX_FALL_SPEED = 25


def move_with_collisions(obj, solids):
    """
    Simple AABB platformer physics.

    Expects obj to have:
      - vx, vy
      - on_ground (bool)
      - get_rect() -> pygame.Rect
      - x, y (center position)
    """
    rect = obj.get_rect()

    # --- vertical movement ---
    obj.vy += GRAVITY
    if obj.vy > MAX_FALL_SPEED:
        obj.vy = MAX_FALL_SPEED

    rect.y += int(round(obj.vy))
    obj.on_ground = False

    for s in solids:
        if rect.colliderect(s):
            if obj.vy > 0:
                # falling, hit floor
                rect.bottom = s.top
                obj.on_ground = True
            elif obj.vy < 0:
                # moving up, hit ceiling
                rect.top = s.bottom
            obj.vy = 0

    # --- horizontal movement ---
    rect.x += int(round(obj.vx))

    for s in solids:
        if rect.colliderect(s):
            if obj.vx > 0:
                rect.right = s.left
            elif obj.vx < 0:
                rect.left = s.right
            obj.vx = 0

    # --- write back via rect center (so hitbox can be any size) ---
    obj.x = rect.centerx
    obj.y = rect.centery