import pygame

GRAVITY = 1.2
MAX_FALL_SPEED = 25


def move_with_collisions(obj, solids):
    rect = obj.get_rect()

    obj.vy += GRAVITY
    if obj.vy > MAX_FALL_SPEED:
        obj.vy = MAX_FALL_SPEED

    rect.y += int(round(obj.vy))
    obj.on_ground = False

    for s in solids:
        if rect.colliderect(s):
            if obj.vy > 0:
                rect.bottom = s.top
                obj.on_ground = True
            elif obj.vy < 0:
                rect.top = s.bottom
            obj.vy = 0

    rect.x += int(round(obj.vx))

    for s in solids:
        if rect.colliderect(s):
            if obj.vx > 0:
                rect.right = s.left
            elif obj.vx < 0:
                rect.left = s.right
            obj.vx = 0

    obj.x = rect.centerx
    obj.y = rect.centery