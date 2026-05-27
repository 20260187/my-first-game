import pygame
import sys
import math
import random
import os

# ─────────────────────────────────────────────
# 경로 설정 (상대경로 기준)
# ─────────────────────────────────────────────
BASE_DIR   = os.path.dirname(os.path.abspath(__file__))
ASSETS_DIR = os.path.join(BASE_DIR, "assets")

# ─────────────────────────────────────────────
# 1. 초기화
# ─────────────────────────────────────────────
pygame.init()
WIDTH, HEIGHT = 1000, 700
screen = pygame.display.set_mode((WIDTH, HEIGHT))
pygame.display.set_caption("Blue Company")
clock = pygame.time.Clock()

font_medium = pygame.font.SysFont("arial", 32, bold=True)
font_ui     = pygame.font.SysFont("arial", 28, bold=True)

# ─────────────────────────────────────────────
# 색상
# ─────────────────────────────────────────────
BG_COLOR          = (15,  15,  18)
WALL_COLOR        = (60,  60,  65)
FLOOR_COLOR_A     = (35,  35,  40)
FLOOR_COLOR_B     = (45,  45,  52)
ENEMY_COLOR       = (255, 80,  80)
BULLET_COLOR      = (255, 220, 80)
DOOR_CLOSED_COLOR = (200, 40,  40)
DOOR_FRAME_COLOR  = (100, 100, 110)
MM_BG      = (5,   5,   5)
MM_CURRENT = (255, 255, 255)
MM_VISITED = (80,  80,  80)
MM_LINE    = (40,  40,  40)

CHECKER_SIZE = 100

# ─────────────────────────────────────────────
# 2. 에셋 로드
# ─────────────────────────────────────────────
def load_image_colorkey(path, colorkey=(0, 0, 0)):
    img = pygame.image.load(path).convert()
    img.set_colorkey(colorkey)
    return img

# 타이틀 이미지
title_img = None
title_img_path = os.path.join(ASSETS_DIR, "start.png")
if os.path.exists(title_img_path):
    raw = pygame.image.load(title_img_path).convert_alpha()
    img_w, img_h = raw.get_size()
    scale = min(WIDTH / img_w, HEIGHT / img_h)
    title_img = pygame.transform.smoothscale(raw, (int(img_w * scale), int(img_h * scale)))

# 캐릭터 스프라이트 시트 (Hina_move.png) 가로 1280 x 세로 320, 4프레임
SPRITE_FRAME_W   = 320
SPRITE_FRAME_H   = 320
SPRITE_FRAMES    = 4
PLAYER_DRAW_SIZE = 64

sprite_frames_right = []
sprite_frames_left  = []

hina_move_path = os.path.join(ASSETS_DIR, "Hina_move.png")
if os.path.exists(hina_move_path):
    sheet = load_image_colorkey(hina_move_path)
    for i in range(SPRITE_FRAMES):
        frame_raw = sheet.subsurface(pygame.Rect(i * SPRITE_FRAME_W, 0, SPRITE_FRAME_W, SPRITE_FRAME_H))
        scaled = pygame.transform.smoothscale(frame_raw, (PLAYER_DRAW_SIZE, PLAYER_DRAW_SIZE))
        scaled.set_colorkey((0, 0, 0))
        sprite_frames_right.append(scaled)
        flipped = pygame.transform.flip(scaled, True, False)
        flipped.set_colorkey((0, 0, 0))
        sprite_frames_left.append(flipped)

# 총 이미지 (hina_gun.png) 320x320
GUN_DRAW_SIZE = 60
gun_img_right = None
gun_img_path  = os.path.join(ASSETS_DIR, "hina_gun.png")
if os.path.exists(gun_img_path):
    gun_raw       = load_image_colorkey(gun_img_path)
    gun_img_right = pygame.transform.smoothscale(gun_raw, (GUN_DRAW_SIZE, GUN_DRAW_SIZE))
    gun_img_right.set_colorkey((0, 0, 0))

# 총 회전 이미지 캐시 (1도 단위 사전 계산, 360장)
gun_rotated_cache = {}
if gun_img_right:
    for deg in range(360):
        rot = pygame.transform.rotate(gun_img_right, -deg)
        rot.set_colorkey((0, 0, 0))
        gun_rotated_cache[deg] = rot

# ─────────────────────────────────────────────
# 3. 방(Room) 설정
# ─────────────────────────────────────────────
ROOM_SIZE  = 1000
GRID_STEP  = ROOM_SIZE + 300
CORRIDOR_W = 200

class Room:
    def __init__(self, room_id, grid_x, grid_y):
        self.id        = room_id
        self.grid_pos  = (grid_x, grid_y)
        self.width     = ROOM_SIZE
        self.height    = ROOM_SIZE
        self.world_x   = grid_x * GRID_STEP
        self.world_y   = grid_y * GRID_STEP
        self.rect      = pygame.Rect(self.world_x, self.world_y, self.width, self.height)
        self.is_cleared  = False
        self.has_enemies = False
        self.doors       = []
        self.floor_surf  = None   # 사전 렌더링된 체크무늬 Surface

    def build_doors(self, connected_ids, all_rooms):
        self.doors = []
        id_to_room = {r.id: r for r in all_rooms}
        for oid in connected_ids:
            other = id_to_room[oid]
            dx = other.grid_pos[0] - self.grid_pos[0]
            dy = other.grid_pos[1] - self.grid_pos[1]
            thick = 24
            dlen  = CORRIDOR_W
            if dx == 1:
                self.doors.append({'rect': pygame.Rect(self.world_x + self.width - thick,
                                                        self.world_y + (self.height - dlen) // 2,
                                                        thick, dlen), 'axis': 'v'})
            elif dx == -1:
                self.doors.append({'rect': pygame.Rect(self.world_x,
                                                        self.world_y + (self.height - dlen) // 2,
                                                        thick, dlen), 'axis': 'v'})
            elif dy == 1:
                self.doors.append({'rect': pygame.Rect(self.world_x + (self.width - dlen) // 2,
                                                        self.world_y + self.height - thick,
                                                        dlen, thick), 'axis': 'h'})
            elif dy == -1:
                self.doors.append({'rect': pygame.Rect(self.world_x + (self.width - dlen) // 2,
                                                        self.world_y,
                                                        dlen, thick), 'axis': 'h'})

    def build_floor(self):
        """체크무늬 바닥을 Surface에 한 번만 그려서 저장"""
        surf = pygame.Surface((self.width, self.height))
        base_col = self.world_x // CHECKER_SIZE
        base_row = self.world_y // CHECKER_SIZE
        cols = self.width  // CHECKER_SIZE + 1
        rows = self.height // CHECKER_SIZE + 1
        for row in range(rows):
            for col in range(cols):
                color = FLOOR_COLOR_A if (base_col + col + base_row + row) % 2 == 0 else FLOOR_COLOR_B
                pygame.draw.rect(surf, color,
                                 (col * CHECKER_SIZE, row * CHECKER_SIZE, CHECKER_SIZE, CHECKER_SIZE))
        self.floor_surf = surf

# ─────────────────────────────────────────────
# 4. 방·통로 생성
# ─────────────────────────────────────────────
rooms = [Room(1,0,0), Room(2,1,0), Room(3,0,1), Room(4,0,2)]
connections = {1:[2,3], 2:[1], 3:[1,4], 4:[3]}
for room in rooms:
    room.build_doors(connections[room.id], rooms)
    room.build_floor()   # 체크무늬 사전 렌더링

def make_corridor(r1, r2):
    dx = r2.grid_pos[0] - r1.grid_pos[0]
    dy = r2.grid_pos[1] - r1.grid_pos[1]
    if dx == 1:
        return pygame.Rect(r1.world_x + r1.width,
                           r1.world_y + (r1.height - CORRIDOR_W) // 2,
                           GRID_STEP - ROOM_SIZE, CORRIDOR_W)
    elif dy == 1:
        return pygame.Rect(r1.world_x + (r1.width - CORRIDOR_W) // 2,
                           r1.world_y + r1.height,
                           CORRIDOR_W, GRID_STEP - ROOM_SIZE)
    return None

id_map    = {r.id: r for r in rooms}
corridors = []
seen      = set()
for sid, eids in connections.items():
    for eid in eids:
        key = tuple(sorted((sid, eid)))
        if key not in seen:
            seen.add(key)
            r1, r2 = id_map[sid], id_map[eid]
            if (r1.grid_pos[0]+r1.grid_pos[1]) > (r2.grid_pos[0]+r2.grid_pos[1]):
                r1, r2 = r2, r1
            c = make_corridor(r1, r2)
            if c: corridors.append(c)

mini_connections = [(1,2),(1,3),(3,4)]

# ─────────────────────────────────────────────
# 5. 문 그리기
# ─────────────────────────────────────────────
def draw_door(surface, door_dict, camera_x, camera_y):
    r  = door_dict['rect']
    sx, sy, sw, sh = r.x + camera_x, r.y + camera_y, r.width, r.height
    fp = 8
    pygame.draw.rect(surface, DOOR_FRAME_COLOR,
                     pygame.Rect(sx-fp, sy-fp, sw+fp*2, sh+fp*2), border_radius=4)
    pygame.draw.rect(surface, DOOR_CLOSED_COLOR, pygame.Rect(sx, sy, sw, sh), border_radius=3)
    if door_dict['axis'] == 'v':
        mx = int(sx + sw // 2)
        pygame.draw.line(surface, (255,255,255), (mx, int(sy+6)), (mx, int(sy+sh-6)), 3)
        pygame.draw.circle(surface, (220,220,220), (mx, int(sy+sh//2)), 6)
    else:
        my = int(sy + sh // 2)
        pygame.draw.line(surface, (255,255,255), (int(sx+6), my), (int(sx+sw-6), my), 3)
        pygame.draw.circle(surface, (220,220,220), (int(sx+sw//2), my), 6)
    lx = int(sx + sw // 2)
    ly = int(sy + sh // 2) - 10
    pygame.draw.rect(surface, (255,200,0), pygame.Rect(lx-7, ly+5, 14, 10), border_radius=2)
    pygame.draw.arc(surface, (255,200,0), pygame.Rect(lx-6, ly-5, 12, 14), 0, math.pi, 3)

# ─────────────────────────────────────────────
# 6. 플레이어
# ─────────────────────────────────────────────
GUN_VISIBLE_MS = 300

class Player:
    def __init__(self):
        self.world_x         = rooms[0].world_x + rooms[0].width  // 2
        self.world_y         = rooms[0].world_y + rooms[0].height // 2
        self.radius          = 20

        # ── 스펙 ──────────────────────────────────────────────────
        self.speed          = 6
        self.attack_range   = 500
        self.fire_cooldown  = 200
        self.bullet_speed   = 14
        self.bullet_range   = 800
        self.bullet_radius  = 6
        # ────────────────────────────────────────────────────────────

        self.last_shot_time  = 0
        self.target_enemy    = None
        self.current_room_id = 1

        self.anim_frame    = 0
        self.anim_timer    = 0
        self.anim_interval = 120
        self.facing_right  = True
        self.is_moving     = False
        self.gun_angle     = 0.0
        self._cached_deg   = None   # 각도 캐시용

    def update(self, keys, enemies, current_time, bullets):
        dx, dy = 0, 0
        if keys[pygame.K_LEFT]  or keys[pygame.K_a]: dx -= 1
        if keys[pygame.K_RIGHT] or keys[pygame.K_d]: dx += 1
        if keys[pygame.K_UP]    or keys[pygame.K_w]: dy -= 1
        if keys[pygame.K_DOWN]  or keys[pygame.K_s]: dy += 1

        self.is_moving = (dx != 0 or dy != 0)
        if dx > 0: self.facing_right = True
        elif dx < 0: self.facing_right = False

        if dx and dy:
            dx *= 0.7071; dy *= 0.7071

        nx, ny = self.world_x + dx * self.speed, self.world_y + dy * self.speed

        active_room = None
        for room in rooms:
            if room.rect.collidepoint(self.world_x, self.world_y):
                active_room = room
                self.current_room_id = room.id
                break

        in_room     = any(r.rect.collidepoint(nx, ny) for r in rooms)
        in_corridor = any(c.collidepoint(nx, ny) for c in corridors)

        can_exit = True
        if active_room and not active_room.is_cleared and active_room.has_enemies:
            if active_room.rect.collidepoint(self.world_x, self.world_y):
                if not active_room.rect.collidepoint(nx, ny):
                    can_exit = False

        if (in_room or in_corridor) and can_exit:
            self.world_x, self.world_y = nx, ny

        # 애니메이션
        if self.is_moving and sprite_frames_right:
            if current_time - self.anim_timer > self.anim_interval:
                self.anim_frame = (self.anim_frame + 1) % SPRITE_FRAMES
                self.anim_timer = current_time
        else:
            self.anim_frame = 0

        # 자동 조준
        self.target_enemy = None
        min_dist = self.attack_range
        for enemy in enemies:
            if active_room and active_room.rect.collidepoint(enemy.world_x, enemy.world_y):
                # hypot 대신 거리 제곱으로 비교 (sqrt 생략)
                ddx = enemy.world_x - self.world_x
                ddy = enemy.world_y - self.world_y
                d_sq = ddx * ddx + ddy * ddy
                if d_sq < min_dist * min_dist:
                    min_dist = math.sqrt(d_sq)
                    self.target_enemy = enemy

        if self.target_enemy:
            self.gun_angle = math.atan2(
                self.target_enemy.world_y - self.world_y,
                self.target_enemy.world_x - self.world_x)
            self.facing_right = self.target_enemy.world_x >= self.world_x

        if self.target_enemy and (current_time - self.last_shot_time > self.fire_cooldown):
            self.fire(bullets, current_time)

    def fire(self, bullets, current_time):
        bullets.append(Bullet(self.world_x, self.world_y, self.gun_angle,
                               self.bullet_speed, self.bullet_radius, self.bullet_range))
        self.last_shot_time = current_time

    def draw(self, surface, screen_cx, screen_cy, current_time):
        half = PLAYER_DRAW_SIZE // 2

        # 스프라이트 먼저
        if sprite_frames_right:
            frames = sprite_frames_right if self.facing_right else sprite_frames_left
            surface.blit(frames[self.anim_frame], (screen_cx - half, screen_cy - half))
        else:
            pygame.draw.circle(surface, (50, 150, 255), (screen_cx, screen_cy), self.radius)

        # 총: 발사 후 GUN_VISIBLE_MS 이내일 때만, 캐시된 회전 이미지 사용
        if (current_time - self.last_shot_time) < GUN_VISIBLE_MS and gun_rotated_cache:
            deg = int(math.degrees(self.gun_angle)) % 360
            rotated = gun_rotated_cache[deg]
            offset  = 28
            gun_cx  = screen_cx + int(math.cos(self.gun_angle) * offset)
            gun_cy  = screen_cy + int(math.sin(self.gun_angle) * offset)
            surface.blit(rotated, rotated.get_rect(center=(gun_cx, gun_cy)))

# ─────────────────────────────────────────────
# 7. 적 / 총알
# ─────────────────────────────────────────────
class Enemy:
    def __init__(self, x, y, room_id):
        self.world_x = x; self.world_y = y
        self.radius  = 22; self.room_id = room_id

class Bullet:
    def __init__(self, x, y, angle, speed, radius, max_range):
        self.world_x = x; self.world_y = y
        self.angle   = angle
        self.speed   = speed
        self.radius  = radius
        self.dx      = math.cos(angle) * speed   # 매 프레임 cos/sin 재계산 제거
        self.dy      = math.sin(angle) * speed
        self.distance_traveled = 0
        self.max_range = max_range

    def update(self):
        self.world_x += self.dx
        self.world_y += self.dy
        self.distance_traveled += self.speed

# ─────────────────────────────────────────────
# 8. 객체 생성 및 적 배치
# ─────────────────────────────────────────────
player  = Player()
enemies = []
for room in rooms:
    if room.id != 1:
        room.has_enemies = True
        for _ in range(random.randint(3, 5)):
            ex = random.randint(room.world_x + 80, room.world_x + room.width  - 80)
            ey = random.randint(room.world_y + 80, room.world_y + room.height - 80)
            enemies.append(Enemy(ex, ey, room.id))
bullets = []
current_stage_text = "2-5"

# ─────────────────────────────────────────────
# 9. 타이틀 화면
# ─────────────────────────────────────────────
def draw_title_screen(surface, tick):
    surface.fill((10, 10, 15))
    if title_img:
        img_rect = title_img.get_rect(center=(WIDTH//2, HEIGHT//2))
        surface.blit(title_img, img_rect)
        overlay = pygame.Surface((WIDTH, HEIGHT), pygame.SRCALPHA)
        overlay.fill((0, 0, 0, 120))
        surface.blit(overlay, (0, 0))
    else:
        for gx in range(0, WIDTH, 60):
            pygame.draw.line(surface, (20,20,30), (gx,0), (gx,HEIGHT))
        for gy in range(0, HEIGHT, 60):
            pygame.draw.line(surface, (20,20,30), (0,gy), (WIDTH,gy))

    if (tick // 500) % 2 == 0:
        prompt = font_medium.render("PRESS  SPACE  TO  START", True, (220, 220, 60))
        surface.blit(prompt, prompt.get_rect(center=(WIDTH//2, HEIGHT - 80)))

# ─────────────────────────────────────────────
# 10. 메인 루프
# ─────────────────────────────────────────────
game_state = "title"
running    = True

while running:
    current_time = pygame.time.get_ticks()

    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running = False
        if event.type == pygame.KEYDOWN:
            if event.key == pygame.K_SPACE and game_state == "title":
                game_state = "playing"
            if event.key == pygame.K_ESCAPE:
                running = False

    if game_state == "title":
        draw_title_screen(screen, current_time)
        pygame.display.flip()
        clock.tick(60)
        continue

    keys = pygame.key.get_pressed()
    player.update(keys, enemies, current_time, bullets)

    # 방 클리어 체크
    for room in rooms:
        if room.has_enemies:
            room.is_cleared = not any(e.room_id == room.id for e in enemies)
        else:
            room.is_cleared = True

    # 총알 이동 & 충돌 — bullet in bullets 제거, 플래그로 처리
    for bullet in bullets[:]:
        bullet.update()
        if bullet.distance_traveled > bullet.max_range:
            bullets.remove(bullet)
            continue
        hit = False
        for enemy in enemies[:]:
            ddx = bullet.world_x - enemy.world_x
            ddy = bullet.world_y - enemy.world_y
            if ddx*ddx + ddy*ddy < enemy.radius * enemy.radius:
                enemies.remove(enemy)
                hit = True
                break
        if hit:
            bullets.remove(bullet)

    camera_x = WIDTH  // 2 - player.world_x
    camera_y = HEIGHT // 2 - player.world_y

    screen.fill(BG_COLOR)

    # [1] 방 바닥 (사전 렌더링 Surface blit) + 외벽
    for room in rooms:
        screen.blit(room.floor_surf, (room.world_x + camera_x, room.world_y + camera_y))
        rr = pygame.Rect(room.world_x+camera_x, room.world_y+camera_y, room.width, room.height)
        pygame.draw.rect(screen, WALL_COLOR, rr, 8)

    # [2] 통로 바닥
    for corr in corridors:
        pygame.draw.rect(screen, FLOOR_COLOR_A,
                         (corr.x+camera_x, corr.y+camera_y, corr.width, corr.height))

    # [3] 문: 플레이어가 방 안에 있고 적이 살아있을 때만 표시
    active_room_now = next((r for r in rooms if r.rect.collidepoint(player.world_x, player.world_y)), None)
    if active_room_now and active_room_now.has_enemies and not active_room_now.is_cleared:
        for door_dict in active_room_now.doors:
            draw_door(screen, door_dict, camera_x, camera_y)

    # [4] 적
    for enemy in enemies:
        ex = int(enemy.world_x + camera_x)
        ey = int(enemy.world_y + camera_y)
        pygame.draw.circle(screen, ENEMY_COLOR, (ex, ey), enemy.radius)
        pygame.draw.circle(screen, (255,255,255), (ex-6, ey-5), 5)
        pygame.draw.circle(screen, (255,255,255), (ex+6, ey-5), 5)
        pygame.draw.circle(screen, (0,0,0),       (ex-5, ey-5), 3)
        pygame.draw.circle(screen, (0,0,0),       (ex+7, ey-5), 3)

    # [5] 총알
    for bullet in bullets:
        pygame.draw.circle(screen, BULLET_COLOR,
                           (int(bullet.world_x+camera_x), int(bullet.world_y+camera_y)), bullet.radius)

    # [6] 플레이어
    player.draw(screen, WIDTH//2, HEIGHT//2, current_time)

    # [7] 미니맵
    mm_box_w, mm_box_h = 170, 180
    mm_x = WIDTH  - mm_box_w - 20
    mm_y = 20
    pygame.draw.rect(screen, MM_BG,      (mm_x,mm_y,mm_box_w,mm_box_h), border_radius=6)
    pygame.draw.rect(screen, (40,40,40), (mm_x,mm_y,mm_box_w,mm_box_h), 2, border_radius=6)

    icon_size    = 20
    grid_spacing = 40
    cx = mm_x + mm_box_w // 2
    cy = mm_y + mm_box_h // 2 - 10

    for sid, eid in mini_connections:
        r1, r2 = id_map[sid], id_map[eid]
        pygame.draw.line(screen, MM_LINE,
            (cx + r1.grid_pos[0]*grid_spacing, cy + r1.grid_pos[1]*grid_spacing),
            (cx + r2.grid_pos[0]*grid_spacing, cy + r2.grid_pos[1]*grid_spacing), 6)

    for room in rooms:
        rcx = cx + room.grid_pos[0] * grid_spacing
        rcy = cy + room.grid_pos[1] * grid_spacing
        ir = pygame.Rect(rcx-icon_size//2, rcy-icon_size//2, icon_size, icon_size)
        if room.id == player.current_room_id:
            col = MM_CURRENT
        elif room.is_cleared:
            col = (60, 180, 80)
        else:
            col = MM_VISITED
        pygame.draw.rect(screen, col, ir, border_radius=3)
        if room.has_enemies and not room.is_cleared:
            pygame.draw.rect(screen, DOOR_CLOSED_COLOR, ir, 2, border_radius=3)

    stage_surf = font_ui.render(current_stage_text, True, (255,255,255))
    screen.blit(stage_surf, stage_surf.get_rect(centerx=mm_x+mm_box_w//2, top=mm_y+mm_box_h+8))

    pygame.display.flip()
    clock.tick(60)

pygame.quit()
sys.exit()