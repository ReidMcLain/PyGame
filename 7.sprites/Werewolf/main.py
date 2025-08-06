import pygame
import sys
from player import Player
from enemy import Enemy

pygame.init()

SCREEN_WIDTH, SCREEN_HEIGHT = 800, 600
FPS = 60
TILE_SIZE = 64

screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
pygame.display.set_caption("Werewolf Sim")

background_image = pygame.image.load("spookybackground.png").convert()
background_image = pygame.transform.scale(background_image, (1920, SCREEN_HEIGHT))

font = pygame.font.Font("gamefont.ttf", 32)
fireball_icon = pygame.image.load("fireballicon.png").convert_alpha()

# Load gothic tile
gothic_sheet = pygame.image.load("gothicblocks.png").convert_alpha()
def crop_tile(sheet, tile_x, tile_y, crop_size=384, tile_size=512):
    offset = (tile_size - crop_size) // 2
    x = tile_x * tile_size + offset
    y = tile_y * tile_size + offset
    return sheet.subsurface(pygame.Rect(x, y, crop_size, crop_size))

gothic_tile = pygame.transform.scale(crop_tile(gothic_sheet, 0, 0), (TILE_SIZE, TILE_SIZE))
tiles_across = background_image.get_width() // TILE_SIZE
bridge_blocks = [pygame.Rect(i * TILE_SIZE, SCREEN_HEIGHT - TILE_SIZE, TILE_SIZE, TILE_SIZE) for i in range(tiles_across)]

# Load wraith idle frames
def load_wraith_idle_frames(folder_path):
    return [
        pygame.transform.scale(
            pygame.image.load(f"{folder_path}/Wraith_01_Idle_{i:03}.png").convert_alpha(),
            (128, 129)
        )
        for i in range(12)
    ]

# Load wraith walking frames
def load_wraith_walk_frames(folder_path):
    return [
        pygame.transform.scale(
            pygame.image.load(f"{folder_path}/Wraith_01_Moving Forward_{i:03}.png").convert_alpha(),
            (128, 129)
        )
        for i in range(12)
    ]

player = Player(SCREEN_WIDTH // 2, SCREEN_HEIGHT - TILE_SIZE - 64, tiles_across)

wraith = Enemy(
    x=1300,
    y=SCREEN_HEIGHT - TILE_SIZE - 128 + 30,
    idle_frames=load_wraith_idle_frames("Wraith1Idle"),
    walk_frames=load_wraith_walk_frames("Wraith1Walking"),
    anim_speed=100,
    hover_amplitude=8,
    hover_speed=0.005,
    player_ref=player
)

clock = pygame.time.Clock()
running = True

while running:
    dt = clock.tick(FPS)
    current_time = pygame.time.get_ticks()

    keys = pygame.key.get_pressed()
    mouse_buttons = pygame.mouse.get_pressed()
    camera_x = max(0, min(player.x - SCREEN_WIDTH // 2, background_image.get_width() - SCREEN_WIDTH))

    screen.blit(background_image, (-camera_x, 0))
    for block in bridge_blocks:
        screen.blit(gothic_tile, (block.x - camera_x, block.y))

    player.handle_input(keys, mouse_buttons, current_time)
    player.update(dt, keys)
    player.draw(screen, camera_x, font, fireball_icon)

    wraith.chase(player.x)
    wraith.update(dt)
    wraith.draw(screen, camera_x)

    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running = False

    pygame.display.flip()

pygame.quit()
sys.exit()