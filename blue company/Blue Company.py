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
# 1. 초기화 및 설정
# ─────────────────────────────────────────────
pygame.init()
WIDTH, HEIGHT = 1000, 700
screen = pygame.display.set_mode((WIDTH, HEIGHT))
clock = pygame.time.Clock()

font_large  = pygame.font.SysFont("arial", 64, bold=True)
font_medium = pygame.font.SysFont("arial", 32, bold=True)
font_small  = pygame.font.SysFont("arial", 22, bold=True)
font_ui     = pygame.font.SysFont("arial", 28, bold=True)

# 색상 정의
BG_COLOR          = (15,  15,  18)
WALL_COLOR        = (60,  60,  65)
FLOOR_COLOR_A     = (35,  35,  40)   # 체크무늬 색 A
FLOOR_COLOR_B     = (45,  45,  52)   # 체크무늬 색 B (살짝 밝게)
PLAYER_COLOR      = (50,  150, 255)
ENEMY_COLOR       = (255, 80,  80)
GUN_COLOR         = (180, 180, 180)
BULLET_COLOR      = (255, 220, 80)
DOOR_CLOSED_COLOR = (200, 40,  40)
DOOR_OPEN_COLOR   = (40,  200, 80)
DOOR_FRAME_COLOR  = (100, 100, 110)

MM_BG      = (5,   5,   5)
MM_CURRENT = (255, 255, 255)
MM_VISITED = (80,  80,  80)
MM_LINE    = (40,  40,  40)

CHECKER_SIZE = 100   # 체크무늬 한 칸 크기 (픽셀, 월드 단위)

# ─────────────────────────────────────────────
# 2. 타이틀 이미지 로드
# ─────────────────────────────────────────────
title_img = None
title_img_path = os.path.join(ASSETS_DIR, "start.png")
if os.path.exists(title_img_path):
    raw = pygame.image.load(title_img_path).convert_alpha()
    # 화면 비율 유지하며 최대 크기로 스케일
    img_w, img_h = raw.get_size()
    scale = min(WIDTH / img_w, HEIGHT / img_h)
    title_img = pygame.transform.smoothscale(raw, (int(img_w * scale), int(img_h * scale)))

# ─────────────────────────────────────────────
# 3. 방(Room) 설정
# ─────────────────────────────────────────────
ROOM_SIZE  = 2000
GRID_STEP  = ROOM_SIZE + 400
CORRIDOR_W = 300

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
        self.doors       = []   # list of { rect, axis }

    def build_doors(self, connected_ids, all_rooms):
        self.doors = []
        id_to_room = {r.id: r for r in all_rooms}
        for oid in connected_ids:
            other = id_to_room[oid]
            dx = other.grid_pos[0] - self.grid_pos[0]
            dy = other.grid_pos[1] - self.grid_pos[1]
            thick = 30
            dlen  = CORRIDOR_W
            if dx == 1:
                cx = self.world_x + self.width - thick
                cy = self.world_y + (self.height - dlen) // 2
                self.doors.append({'rect': pygame.Rect(cx, cy, thick, dlen), 'axis': 'v'})
            elif dx == -1:
                cx = self.world_x
                cy = self.world_y + (self.height - dlen) // 2
                self.doors.append({'rect': pygame.Rect(cx, cy, thick, dlen), 'axis': 'v'})
            elif dy == 1:
                cx = self.world_x + (self.width  - dlen) // 2
                cy = self.world_y + self.height - thick
                self.doors.append({'rect': pygame.Rect(cx, cy, dlen, thick), 'axis': 'h'})
            elif dy == -1:
                cx = self.world_x + (self.width  - dlen) // 2
                cy = self.world_y
                self.doors.append({'rect': pygame.Rect(cx, cy, dlen, thick), 'axis': 'h'})

# ─────────────────────────────────────────────
# 4. 방·통로 생성
# ─────────────────────────────────────────────
rooms = [Room(1,0,0), Room(2,1,0), Room(3,0,1), Room(4,0,2)]
connections = {1:[2,3], 2:[1], 3:[1,4], 4:[3]}
for room in rooms:
    room.build_doors(connections[room.id], rooms)

def make_corridor(r1, r2):
    dx = r2.grid_pos[0] - r1.grid_pos[0]
    dy = r2.grid_pos[1] - r1.grid_pos[1]
    if dx == 1:
        return pygame.Rect(r1.world_x+r1.width,
                           r1.world_y+(r1.height-CORRIDOR_W)//2,
                           GRID_STEP-ROOM_SIZE, CORRIDOR_W)
    elif dy == 1:
        return pygame.Rect(r1.world_x+(r1.width-CORRIDOR_W)//2,
                           r1.world_y+r1.height,
                           CORRIDOR_W, GRID_STEP-ROOM_SIZE)
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
# 5. 체크무늬 바닥 Surface 생성 헬퍼
# ─────────────────────────────────────────────
def draw_checker_floor(surface, world_rect, camera_x, camera_y):
    """world_rect 영역에 체크무늬 바닥을 그린다."""
    wx, wy, ww, wh = world_rect.x, world_rect.y, world_rect.width, world_rect.height

    # 월드 좌표 기준 체크 시작 타일 인덱스
    start_col = wx // CHECKER_SIZE
    start_row = wy // CHECKER_SIZE
    end_col   = (wx + ww) // CHECKER_SIZE + 1
    end_row   = (wy + wh) // CHECKER_SIZE + 1

    for row in range(start_row, end_row):
        for col in range(start_col, end_col):
            tile_wx = col * CHECKER_SIZE
            tile_wy = row * CHECKER_SIZE

            # world_rect 와 교차하는 부분만 클리핑
            inter_x = max(tile_wx, wx)
            inter_y = max(tile_wy, wy)
            inter_r = min(tile_wx + CHECKER_SIZE, wx + ww)
            inter_b = min(tile_wy + CHECKER_SIZE, wy + wh)
            if inter_r <= inter_x or inter_b <= inter_y:
                continue

            color = FLOOR_COLOR_A if (col + row) % 2 == 0 else FLOOR_COLOR_B
            sx = inter_x + camera_x
            sy = inter_y + camera_y
            pygame.draw.rect(surface, color,
                             (sx, sy, inter_r - inter_x, inter_b - inter_y))

# ─────────────────────────────────────────────
# 6. 문 그리기 헬퍼
# ─────────────────────────────────────────────
def draw_door(surface, door_dict, camera_x, camera_y, is_locked):
    r  = door_dict['rect']
    sx, sy, sw, sh = r.x+camera_x, r.y+camera_y, r.width, r.height

    # 문틀
    fp = 8
    pygame.draw.rect(surface, DOOR_FRAME_COLOR,
                     pygame.Rect(sx-fp, sy-fp, sw+fp*2, sh+fp*2), border_radius=4)
    # 문 패널
    color = DOOR_CLOSED_COLOR if is_locked else DOOR_OPEN_COLOR
    pygame.draw.rect(surface, color, pygame.Rect(sx, sy, sw, sh), border_radius=3)

    # 장식선 + 손잡이
    if door_dict['axis'] == 'v':
        mx = int(sx + sw//2)
        pygame.draw.line(surface, (255,255,255), (mx, int(sy+6)), (mx, int(sy+sh-6)), 3)
        pygame.draw.circle(surface, (220,220,220), (mx, int(sy+sh//2)), 6)
    else:
        my = int(sy + sh//2)
        pygame.draw.line(surface, (255,255,255), (int(sx+6), my), (int(sx+sw-6), my), 3)
        pygame.draw.circle(surface, (220,220,220), (int(sx+sw//2), my), 6)

    # 자물쇠
    if is_locked:
        lx = int(sx + sw//2)
        ly = int(sy + sh//2) - 10
        pygame.draw.rect(surface, (255,200,0), pygame.Rect(lx-7, ly+5, 14, 10), border_radius=2)
        pygame.draw.arc(surface, (255,200,0),  pygame.Rect(lx-6, ly-5, 12, 14), 0, math.pi, 3)

# ─────────────────────────────────────────────
# 7. 플레이어 / 적 / 총알
# ─────────────────────────────────────────────
class Player:
    def __init__(self):
        self.world_x         = rooms[0].world_x + rooms[0].width  // 2
        self.world_y         = rooms[0].world_y + rooms[0].height // 2
        self.speed           = 6
        self.radius          = 20
        self.attack_range    = 600
        self.fire_cooldown   = 200
        self.last_shot_time  = 0
        self.target_enemy    = None
        self.current_room_id = 1

    def update(self, keys, enemies, current_time, bullets):
        dx, dy = 0, 0
        if keys[pygame.K_LEFT]  or keys[pygame.K_a]: dx -= 1
        if keys[pygame.K_RIGHT] or keys[pygame.K_d]: dx += 1
        if keys[pygame.K_UP]    or keys[pygame.K_w]: dy -= 1
        if keys[pygame.K_DOWN]  or keys[pygame.K_s]: dy += 1
        if dx and dy:
            dx *= 0.7071; dy *= 0.7071

        nx, ny = self.world_x + dx*self.speed, self.world_y + dy*self.speed

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

        self.target_enemy = None
        min_dist = self.attack_range
        for enemy in enemies:
            if active_room and active_room.rect.collidepoint(enemy.world_x, enemy.world_y):
                d = math.hypot(enemy.world_x-self.world_x, enemy.world_y-self.world_y)
                if d < min_dist:
                    min_dist = d
                    self.target_enemy = enemy

        if self.target_enemy and (current_time - self.last_shot_time > self.fire_cooldown):
            self.fire(bullets, current_time)

    def fire(self, bullets, current_time):
        angle = math.atan2(self.target_enemy.world_y-self.world_y,
                           self.target_enemy.world_x-self.world_x)
        bullets.append(Bullet(self.world_x, self.world_y, angle))
        self.last_shot_time = current_time


class Enemy:
    def __init__(self, x, y, room_id):
        self.world_x = x; self.world_y = y
        self.radius  = 22; self.room_id = room_id

class Bullet:
    def __init__(self, x, y, angle):
        self.world_x = x; self.world_y = y
        self.angle   = angle; self.speed = 14
        self.radius  = 6
        self.distance_traveled = 0; self.max_range = 800

    def update(self):
        self.world_x += math.cos(self.angle)*self.speed
        self.world_y += math.sin(self.angle)*self.speed
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
            ex = random.randint(room.world_x+100, room.world_x+room.width-100)
            ey = random.randint(room.world_y+100, room.world_y+room.height-100)
            enemies.append(Enemy(ex, ey, room.id))
bullets = []
current_stage_text = "2-5"

# ─────────────────────────────────────────────
# 9. 타이틀 화면
# ─────────────────────────────────────────────
def draw_title_screen(surface, tick):
    surface.fill((10, 10, 15))

    if title_img:
        # 이미지 전체 화면 배경으로 표시
        img_rect = title_img.get_rect(center=(WIDTH//2, HEIGHT//2))
        surface.blit(title_img, img_rect)
        # 반투명 오버레이 (텍스트 가독성 확보)
        overlay = pygame.Surface((WIDTH, HEIGHT), pygame.SRCALPHA)
        overlay.fill((0, 0, 0, 120))
        surface.blit(overlay, (0, 0))
    else:
        # 이미지 없을 때 폴백 배경
        for gx in range(0, WIDTH, 60):
            pygame.draw.line(surface, (20,20,30), (gx,0), (gx,HEIGHT))
        for gy in range(0, HEIGHT, 60):
            pygame.draw.line(surface, (20,20,30), (0,gy), (WIDTH,gy))

    if (tick // 500) % 2 == 0:
        prompt = font_medium.render("PRESS  SPACE  TO  START", True, (220, 220, 60))
        surface.blit(prompt, prompt.get_rect(center=(WIDTH//2, HEIGHT//2 + 80)))

    # 범례
    ly = HEIGHT//2 + 150

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

    # ── 타이틀 ───────────────────────────────
    if game_state == "title":
        draw_title_screen(screen, current_time)
        pygame.display.flip()
        clock.tick(60)
        continue

    # ── 게임 ─────────────────────────────────
    keys = pygame.key.get_pressed()
    player.update(keys, enemies, current_time, bullets)

    for room in rooms:
        if room.has_enemies:
            room.is_cleared = not any(e.room_id == room.id for e in enemies)
        else:
            room.is_cleared = True

    for bullet in bullets[:]:
        bullet.update()
        if bullet.distance_traveled > bullet.max_range:
            bullets.remove(bullet); continue
        for enemy in enemies[:]:
            if math.hypot(bullet.world_x-enemy.world_x, bullet.world_y-enemy.world_y) < enemy.radius:
                if bullet in bullets: bullets.remove(bullet)
                enemies.remove(enemy); break

    camera_x = WIDTH  // 2 - player.world_x
    camera_y = HEIGHT // 2 - player.world_y

    # ── 그리기 ───────────────────────────────
    screen.fill(BG_COLOR)

    # [1] 방 바닥 체크무늬 + 외벽
    for room in rooms:
        draw_checker_floor(screen, room.rect, camera_x, camera_y)
        rr = pygame.Rect(room.world_x+camera_x, room.world_y+camera_y, room.width, room.height)
        pygame.draw.rect(screen, WALL_COLOR, rr, 8)

    # [2] 통로 바닥 (단색, 방보다 약간 어둡게)
    for corr in corridors:
        cr = pygame.Rect(corr.x+camera_x, corr.y+camera_y, corr.width, corr.height)
        pygame.draw.rect(screen, FLOOR_COLOR_A, cr)

    # [3] 문 시각화
    for room in rooms:
        is_locked = room.has_enemies and not room.is_cleared
        for door_dict in room.doors:
            draw_door(screen, door_dict, camera_x, camera_y, is_locked)

    # [4] 적
    for enemy in enemies:
        ex = int(enemy.world_x+camera_x)
        ey = int(enemy.world_y+camera_y)
        pygame.draw.circle(screen, ENEMY_COLOR, (ex,ey), enemy.radius)
        pygame.draw.circle(screen, (255,255,255), (ex-6,ey-5), 5)
        pygame.draw.circle(screen, (255,255,255), (ex+6,ey-5), 5)
        pygame.draw.circle(screen, (0,0,0),       (ex-5,ey-5), 3)
        pygame.draw.circle(screen, (0,0,0),       (ex+7,ey-5), 3)

    # [5] 총알
    for bullet in bullets:
        pygame.draw.circle(screen, BULLET_COLOR,
                           (int(bullet.world_x+camera_x), int(bullet.world_y+camera_y)), bullet.radius)

    # [6] 플레이어
    pygame.draw.circle(screen, PLAYER_COLOR, (WIDTH//2, HEIGHT//2), player.radius)
    gun_angle = math.atan2(player.target_enemy.world_y-player.world_y,
                           player.target_enemy.world_x-player.world_x) if player.target_enemy else 0
    gex = WIDTH //2 + math.cos(gun_angle)*32
    gey = HEIGHT//2 + math.sin(gun_angle)*32
    pygame.draw.line(screen, GUN_COLOR, (WIDTH//2,HEIGHT//2), (int(gex),int(gey)), 7)

    # [7] 미니맵
    mm_box_w, mm_box_h = 170, 180
    mm_x = WIDTH  - mm_box_w - 20
    mm_y = 20
    pygame.draw.rect(screen, MM_BG,     (mm_x,mm_y,mm_box_w,mm_box_h), border_radius=6)
    pygame.draw.rect(screen, (40,40,40),(mm_x,mm_y,mm_box_w,mm_box_h), 2, border_radius=6)

    icon_size    = 20
    grid_spacing = 40
    cx = mm_x + mm_box_w//2
    cy = mm_y + mm_box_h//2 - 10

    for sid, eid in mini_connections:
        r1, r2 = id_map[sid], id_map[eid]
        pygame.draw.line(screen, MM_LINE,
            (cx+r1.grid_pos[0]*grid_spacing, cy+r1.grid_pos[1]*grid_spacing),
            (cx+r2.grid_pos[0]*grid_spacing, cy+r2.grid_pos[1]*grid_spacing), 6)

    for room in rooms:
        rcx = cx + room.grid_pos[0]*grid_spacing
        rcy = cy + room.grid_pos[1]*grid_spacing
        ir = pygame.Rect(rcx-icon_size//2, rcy-icon_size//2, icon_size, icon_size)
        if room.id == player.current_room_id:
            col = MM_CURRENT
        elif room.is_cleared:
            col = (60,180,80)
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