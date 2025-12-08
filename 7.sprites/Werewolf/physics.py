# physics.py
import pygame

def move_with_collisions(entity, solids, gravity=0.8):
    """
    Simple platformer physics:
    - entity must have: x, y, vx, vy, frame_width, frame_height, on_ground, get_rect()
    - solids is a list of pygame.Rect
    """

    rect = entity.get_rect()

    # Apply gravity
    entity.vy += gravity

    # --- Horizontal movement ---
    rect.x += int(entity.vx)
    for s in solids:
        if rect.colliderect(s):
            if entity.vx > 0:      # moving right; bump left
                rect.right = s.left
            elif entity.vx < 0:    # moving left; bump right
                rect.left = s.right
            entity.vx = 0

    # --- Vertical movement ---
    rect.y += int(entity.vy)
    entity.on_ground = False
    for s in solids:
        if rect.colliderect(s):
            if entity.vy > 0:      # falling; land on top
                rect.bottom = s.top
                entity.on_ground = True
            elif entity.vy < 0:    # jumping up; hit head
                rect.top = s.bottom
            entity.vy = 0

    # Write back to entity center
    entity.x = rect.left + entity.frame_width // 2
    entity.y = rect.top + entity.frame_height // 2