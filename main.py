# game with map generation 15.03.2024
import pygame
import random
import math
import json

TILE_SIZE = 32
MAP_WIDTH = 30
SD = "map"
MAP_HEIGHT = 20
SCREEN_WIDTH = MAP_WIDTH * TILE_SIZE
SCREEN_HEIGHT = MAP_HEIGHT * TILE_SIZE
PLAYER_SIZE = TILE_SIZE
PLAYER_SPEED = TILE_SIZE
BULLET_SPEED = 10
BULLET_SIZE = 5
ENEMY_SIZE = TILE_SIZE
ENEMY_COUNT = 5
ENEMY_SPEED = TILE_SIZE // 10
PLAYER_HEALTH = 100
ENEMY_DAMAGE = 10
FPS = 60

DEBUG_ENEMY = True

pygame.init()
screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
pygame.display.set_caption("gmxz")

COLORS = {
    'grass': (34, 139, 34),
    'earth': (153, 102, 51),
    'sand': (194, 178, 128),
    'player': (255, 0, 0),
    'bullet': (255, 255, 0),
    'enemy': (0, 0, 255),
    'block': (30, 30, 21)
}

TILE_TYPES = ['grass', 'earth', 'sand']
blocks = []


class BlockPlacer:
    def __init__(self, x, y, px, py, hp=10):
        tile_x = x // TILE_SIZE
        tile_y = y // TILE_SIZE
        self.x = tile_x * TILE_SIZE
        self.y = tile_y * TILE_SIZE
        self.rect = pygame.Rect(self.x, self.y, TILE_SIZE, TILE_SIZE)
        self.hp = hp
        self.block_color = COLORS['block']
        self.block_size = TILE_SIZE
        self.max_distance = TILE_SIZE * 4
        self.distance = math.sqrt(((x - px) ** 2 + (y - py) ** 2))
        if self.distance <= self.max_distance:
            blocks.append(self)
        for obg in blocks:
            try:
                if obg.rect.colliderect(self.rect) and obg != self:
                    blocks.remove(self)
            except ValueError:
                pass

    def place_block(self):
        pygame.draw.rect(screen, self.block_color, self.rect)

    def damage(self):
        self.hp -= 1
        if self.hp <= 0:
            blocks.remove(self)


class HpBar:
    def __init__(self, x, y, width, height, max_health):
        self.x = x
        self.y = y
        self.width = width
        self.height = height
        self.max_health = max_health
        self.current_health = max_health
        self.health_color = (255, 0, 0)

    def update(self, current_health):
        self.current_health = current_health

    def draw(self):
        health_width = (self.current_health / self.max_health) * self.width
        pygame.draw.rect(screen, (0, 0, 0), (self.x-2.5, self.y-2.5, self.width+5, self.height+5))
        pygame.draw.rect(screen, (255, 255, 255), (self.x, self.y, self.width, self.height))
        pygame.draw.rect(screen, self.health_color, (self.x, self.y, health_width, self.height))


def generate_map():
    return [[random.choice(TILE_TYPES) for _ in range(MAP_WIDTH)] for _ in range(MAP_HEIGHT)]


def draw_map(game_map, offset_x, offset_y):
    for y in range(MAP_HEIGHT):
        for x in range(MAP_WIDTH):
            tile_type = game_map[y][x]
            color = COLORS[tile_type]
            screen_x = (x * TILE_SIZE) - offset_x
            screen_y = (y * TILE_SIZE) - offset_y
            pygame.draw.rect(screen, color, (screen_x, screen_y, TILE_SIZE, TILE_SIZE))


def draw_player(player_pos):
    pygame.draw.rect(screen, COLORS['player'], (*player_pos, PLAYER_SIZE, PLAYER_SIZE))


def draw_bullets(bullets):
    for bullet in bullets:
        pygame.draw.rect(screen, COLORS['bullet'], (*bullet['pos'], BULLET_SIZE, BULLET_SIZE))


def draw_enemies(enemies):
    for enemy in enemies:
        pygame.draw.rect(screen, COLORS['enemy'], (*enemy['pos'], ENEMY_SIZE, ENEMY_SIZE))


def calculate_bullet_direction(player_pos, mouse_pos):
    player_center = (player_pos[0] + PLAYER_SIZE // 2, player_pos[1] + PLAYER_SIZE // 2)
    angle = math.atan2(mouse_pos[1] - player_center[1], mouse_pos[0] - player_center[0])
    return math.cos(angle), math.sin(angle)


def generate_enemies(enemy_count=ENEMY_COUNT):
    enemies = []
    for _ in range(enemy_count):
        enemy_pos = [random.randint(2, MAP_WIDTH - 1) * TILE_SIZE,
                     random.randint(2, MAP_HEIGHT - 1) * TILE_SIZE]
        enemies.append({'pos': enemy_pos, 'dir': [random.choice([-1, 1]), random.choice([-1, 1])]})
    return enemies


def move_enemies(enemies):
    for enemy in enemies:
        ox, oy = enemy['pos'][0], enemy['pos'][1]
        enemy_collision = False
        enemy_rect = pygame.Rect(enemy['pos'][0], enemy['pos'][1], TILE_SIZE, TILE_SIZE)
        enemy['pos'][0] += enemy['dir'][0] * ENEMY_SPEED
        enemy['pos'][1] += enemy['dir'][1] * ENEMY_SPEED
        if enemy['pos'][0] < 0 or enemy['pos'][0] >= SCREEN_WIDTH - ENEMY_SIZE:
            enemy['dir'][0] *= -1
        if enemy['pos'][1] < 0 or enemy['pos'][1] >= SCREEN_HEIGHT - ENEMY_SIZE:
            enemy['dir'][1] *= -1
        for block in blocks:
            if enemy_rect.colliderect(block.rect):
                enemy['pos'][0], enemy['pos'][1] = ox, oy
                block.damage()
                enemy_collision = True
        if enemy_collision:
            enemy['pos'][0] -= enemy['dir'][0] * ENEMY_SPEED
            enemy['pos'][1] -= enemy['dir'][1] * ENEMY_SPEED
            enemy['dir'][0] *= -1
            enemy['dir'][1] *= -1


def check_bullet_enemy_collision(bullets, enemies):
    for bullet in bullets:
        bullet_rect = pygame.Rect(*bullet['pos'], BULLET_SIZE, BULLET_SIZE)
        for enemy in enemies:
            enemy_rect = pygame.Rect(*enemy['pos'], ENEMY_SIZE, ENEMY_SIZE)
            if bullet_rect.colliderect(enemy_rect):
                bullets.remove(bullet)
                enemies.remove(enemy)
                break


def check_bullet_block_collision(bullets, blocks):
    for bullet in bullets:
        bullet_rect = pygame.Rect(*bullet['pos'], BULLET_SIZE, BULLET_SIZE)
        for block in blocks:
            if bullet_rect.colliderect(block.rect):
                bullets.remove(bullet)
                block.damage()
                break


def check_player_enemy_collision(player_pos, enemies, player_health):
    player_rect = pygame.Rect(*player_pos, PLAYER_SIZE, PLAYER_SIZE)
    for enemy in enemies:
        enemy_rect = pygame.Rect(*enemy['pos'], ENEMY_SIZE, ENEMY_SIZE)
        if player_rect.colliderect(enemy_rect):
            player_health -= ENEMY_DAMAGE
            enemies.remove(enemy)
            break
    return player_health


def save_map(filename, game_map, blocks, enemies):
    map_data = {
        'map': game_map,
        'blocks': [{'x': block.x, 'y': block.y, 'hp': block.hp} for block in blocks],
        'enemies': enemies,
    }
    with open(f'data/{filename}', 'w', encoding='utf-8') as f:
        json.dump(map_data, f)


def load_map(filename):
    with open(f'data/{filename}', 'r', encoding='utf-8') as f:
        map_data = json.load(f)
    game_map = map_data['map']
    blocks_data = map_data['blocks']
    enemy = map_data['enemies']
    for block_data in blocks_data:
        BlockPlacer(block_data['x'], block_data['y'], block_data['x'], block_data['y'], hp=block_data['hp'])
    return game_map, enemy


def main():
    clock = pygame.time.Clock()
    map_x, map_y = 0, 0
    try:
        current_map, enemies = load_map(f'{SD}{map_x}_{map_y}.json')
    except FileNotFoundError:
        current_map = generate_map()
        enemies = generate_enemies()
    player_pos = [((MAP_WIDTH // 2) - 1) * TILE_SIZE, ((MAP_HEIGHT // 2) - 1) * TILE_SIZE]
    cooldown = 0
    enemy_delay = 5000
    map_offset_x = 0
    map_offset_y = 0

    bullets = []
    enemies = generate_enemies(ENEMY_COUNT)

    if DEBUG_ENEMY:
        enemies.clear()
    player_hp_bar = HpBar(5, 5, 200, 20, PLAYER_HEALTH)
    player_health = check_player_enemy_collision(player_pos, enemies, PLAYER_HEALTH)
    running = True
    while running:
        player_rect = pygame.Rect(player_pos[0], player_pos[1], TILE_SIZE, TILE_SIZE)
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
            elif event.type == pygame.MOUSEBUTTONDOWN:
                if event.button == 1:
                    mouse_pos = pygame.mouse.get_pos()
                    direction = calculate_bullet_direction(player_pos, mouse_pos)
                    bullet_pos = [player_pos[0] + PLAYER_SIZE // 2, player_pos[1] + PLAYER_SIZE // 2]
                    bullets.append({'pos': bullet_pos, 'dir': direction})
                if event.button == 3:
                    mouse_pos = pygame.mouse.get_pos()
                    if not player_rect.collidepoint(mouse_pos):
                        BlockPlacer(mouse_pos[0], mouse_pos[1], player_pos[0], player_pos[1])
        keys = pygame.key.get_pressed()
        ox, oy = player_pos[0], player_pos[1]
        if cooldown == 0:
            if keys[pygame.K_a]:
                player_pos[0] -= PLAYER_SPEED
                cooldown = 5
            if keys[pygame.K_d]:
                player_pos[0] += PLAYER_SPEED
                cooldown = 5
            if keys[pygame.K_w]:
                player_pos[1] -= PLAYER_SPEED
                cooldown = 5
            if keys[pygame.K_s]:
                player_pos[1] += PLAYER_SPEED
                cooldown = 5
            player_rect = pygame.Rect(player_pos[0], player_pos[1], PLAYER_SIZE, PLAYER_SIZE)
            for obg in blocks:
                if player_rect.colliderect(obg.rect):
                    player_pos[0], player_pos[1] = ox, oy
        else:
            cooldown -= 1

        if player_pos[0] < 0:
            player_pos[0] += SCREEN_WIDTH
            map_offset_x += SCREEN_WIDTH
            save_map(f'{SD}{map_x}_{map_y}.json', current_map, blocks, enemies)
            blocks.clear()
            bullets.clear()
            map_x -= 1
            try:
                current_map, enemies = load_map(f'{SD}{map_x}_{map_y}.json')
            except FileNotFoundError:
                current_map = generate_map()
                enemies = generate_enemies()
        elif player_pos[0] >= SCREEN_WIDTH:
            player_pos[0] -= SCREEN_WIDTH
            map_offset_x -= SCREEN_WIDTH
            save_map(f'{SD}{map_x}_{map_y}.json', current_map, blocks, enemies)
            blocks.clear()
            bullets.clear()
            map_x += 1
            try:
                current_map, enemies = load_map(f'{SD}{map_x}_{map_y}.json')
            except FileNotFoundError:
                current_map = generate_map()
                enemies = generate_enemies()
        if player_pos[1] < 0:
            player_pos[1] += SCREEN_HEIGHT
            map_offset_y += SCREEN_HEIGHT
            save_map(f'{SD}{map_x}_{map_y}.json', current_map, blocks, enemies)
            blocks.clear()
            bullets.clear()
            map_y -= 1
            try:
                current_map, enemies = load_map(f'{SD}{map_x}_{map_y}.json')
            except FileNotFoundError:
                current_map = generate_map()
                enemies = generate_enemies()
        elif player_pos[1] >= SCREEN_HEIGHT:
            player_pos[1] -= SCREEN_HEIGHT
            map_offset_y -= SCREEN_HEIGHT
            save_map(f'{SD}{map_x}_{map_y}.json', current_map, blocks, enemies)
            blocks.clear()
            bullets.clear()
            map_y += 1
            try:
                current_map, enemies = load_map(f'{SD}{map_x}_{map_y}.json')
            except FileNotFoundError:
                current_map = generate_map()
                enemies = generate_enemies()

        for bullet in bullets:
            bullet['pos'][0] += bullet['dir'][0] * BULLET_SPEED
            bullet['pos'][1] += bullet['dir'][1] * BULLET_SPEED

        move_enemies(enemies)
        check_bullet_block_collision(bullets, blocks)
        check_bullet_enemy_collision(bullets, enemies)
        player_health = check_player_enemy_collision(player_pos, enemies, player_health)

        if player_health <= 0:
            running = False

        screen.fill((0, 0, 0))
        draw_map(current_map, map_offset_x % SCREEN_WIDTH, map_offset_y % SCREEN_HEIGHT)
        draw_player(player_pos)
        draw_bullets(bullets)
        draw_enemies(enemies)
        for block in blocks:
            block.place_block()
        player_hp_bar.update(player_health)
        player_hp_bar.draw()
        pygame.display.flip()
        clock.tick(60)
        if enemy_delay > 0:
            enemy_delay -= 1
        else:
            if len(enemies) == 0:
                enemies = generate_enemies(random.randint(1, 3))
                enemy_delay = 2500

    pygame.quit()


if __name__ == "__main__":
    main()
