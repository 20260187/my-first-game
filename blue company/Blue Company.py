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
pygame.mixer.init(frequency=44100, size=-16, channels=2, buffer=512)

# ── 1.2배 스케일 적용 ──
SCALE = 1.2

WIDTH, HEIGHT = 1000, 700
screen = pygame.display.set_mode((WIDTH, HEIGHT))
pygame.display.set_caption("Blue Company")
clock = pygame.time.Clock()

# ── 폰트: NanumGothic.ttf 우선 사용, 없으면 시스템 폰트 ──
_nanum_path = os.path.join(ASSETS_DIR, "NanumGothic.ttf")
def _make_font(size, bold=False):
    if os.path.exists(_nanum_path):
        return pygame.font.Font(_nanum_path, size)
    return pygame.font.SysFont("arial", size, bold=bold)

font_medium = _make_font(int(32 * SCALE), bold=True)
font_ui     = _make_font(int(28 * SCALE), bold=True)
font_mini   = _make_font(int(11 * SCALE), bold=True)
font_prompt = _make_font(int(20 * SCALE), bold=True)

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

CHECKER_SIZE = int(100 * SCALE)

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
PLAYER_DRAW_SIZE = int(64 * SCALE)

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
GUN_DRAW_SIZE = int(60 * SCALE)
gun_img_right = None
gun_img_path  = os.path.join(ASSETS_DIR, "hina_gun.png")
if os.path.exists(gun_img_path):
    gun_raw       = load_image_colorkey(gun_img_path)
    gun_img_right = pygame.transform.smoothscale(gun_raw, (GUN_DRAW_SIZE, GUN_DRAW_SIZE))
    gun_img_right.set_colorkey((0, 0, 0))

# 총 회전 이미지 캐시 (1도 단위 사전 계산, 360장)
gun_rotated_cache_r = {}
gun_rotated_cache_l = {}
if gun_img_right:
    gun_img_left = pygame.transform.flip(gun_img_right, False, True)
    gun_img_left.set_colorkey((0, 0, 0))
    for deg in range(360):
        rot_r = pygame.transform.rotate(gun_img_right, -deg)
        rot_r.set_colorkey((0, 0, 0))
        gun_rotated_cache_r[deg] = rot_r

        rot_l = pygame.transform.rotate(gun_img_left, -deg)
        rot_l.set_colorkey((0, 0, 0))
        gun_rotated_cache_l[deg] = rot_l

# ── 총구 화염 이펙트 (shot.png) 320x320 ──────────────────────────
MUZZLE_DRAW_SIZE = int(40 * SCALE)
MUZZLE_VISIBLE_MS = 60

muzzle_flash_cache_r = {}
muzzle_flash_cache_l = {}

shot_img_path = os.path.join(ASSETS_DIR, "shot.png")
if os.path.exists(shot_img_path):
    shot_raw   = pygame.image.load(shot_img_path).convert_alpha()
    shot_scaled = pygame.transform.smoothscale(shot_raw, (MUZZLE_DRAW_SIZE, MUZZLE_DRAW_SIZE))
    for deg in range(360):
        rot_r = pygame.transform.rotate(shot_scaled, -deg)
        muzzle_flash_cache_r[deg] = rot_r
        rot_l = pygame.transform.rotate(pygame.transform.flip(shot_scaled, False, True), -deg)
        muzzle_flash_cache_l[deg] = rot_l
else:
    shot_scaled = None

# ── 총소리 로드 ────────────────────────────────────────────
gun_sound = None
gun_sound_path = os.path.join(ASSETS_DIR, "gun_sound.wav")
if not os.path.exists(gun_sound_path):
    gun_sound_path = os.path.join(ASSETS_DIR, "gun_sound.mp3")
if not os.path.exists(gun_sound_path):
    gun_sound_path = os.path.join(ASSETS_DIR, "gun_sound.ogg")

if os.path.exists(gun_sound_path):
    try:
        gun_sound = pygame.mixer.Sound(gun_sound_path)
        gun_sound.set_volume(0.18)
    except Exception as e:
        print(f"[WARN] gun_sound 로드 실패: {e}")

# ── 피아노 이미지 로드 ──────────────────────────────────────
PIANO_ORIG_W, PIANO_ORIG_H = 521, 446
PIANO_DRAW_W = int(130 * SCALE)
PIANO_DRAW_H = int(112 * SCALE)

piano_img = None
piano_img_path = os.path.join(ASSETS_DIR, "piano.png")
if os.path.exists(piano_img_path):
    try:
        piano_raw = pygame.image.load(piano_img_path).convert_alpha()
        piano_img = pygame.transform.smoothscale(piano_raw, (PIANO_DRAW_W, PIANO_DRAW_H))
    except Exception as e:
        print(f"[WARN] piano 이미지 로드 실패: {e}")

# ── BGM 로드 ────────────────────────────────────────────────
BGM_FILES = [
    os.path.join(ASSETS_DIR, "bgm1.opus"),
    os.path.join(ASSETS_DIR, "bgm2.opus"),
    os.path.join(ASSETS_DIR, "bgm3.opus"),
]
bgm_current_index = 0

def play_bgm(index):
    global bgm_current_index
    bgm_current_index = index % 3
    path = BGM_FILES[bgm_current_index]
    if os.path.exists(path):
        try:
            pygame.mixer.music.load(path)
            pygame.mixer.music.set_volume(0.5)
            pygame.mixer.music.play(-1)
        except Exception as e:
            print(f"[WARN] BGM 로드 실패: {e}")
    else:
        print(f"[WARN] BGM 파일 없음: {path}")

# ─────────────────────────────────────────────
# 3. 방(Room) 설정
# ─────────────────────────────────────────────
ROOM_SIZE  = int(1000 * SCALE)
GRID_STEP  = int((1000 + 300) * SCALE)
CORRIDOR_W = int(200 * SCALE)

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
        self.floor_surf  = None

    def build_doors(self, connected_ids, all_rooms):
        self.doors = []
        id_to_room = {r.id: r for r in all_rooms}
        for oid in connected_ids:
            other = id_to_room[oid]
            dx = other.grid_pos[0] - self.grid_pos[0]
            dy = other.grid_pos[1] - self.grid_pos[1]
            thick = int(24 * SCALE)
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
    room.build_floor()

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
# 피아노 월드 좌표 설정 (시작 방 id=1, 오른쪽 모서리)
# ─────────────────────────────────────────────
start_room = id_map[1]
PIANO_MARGIN = int(80 * SCALE)
PIANO_WORLD_X = start_room.world_x + start_room.width - PIANO_DRAW_W - PIANO_MARGIN
PIANO_WORLD_Y = start_room.world_y + PIANO_MARGIN
PIANO_INTERACT_RADIUS = int(120 * SCALE)

# ─────────────────────────────────────────────
# 5. 문 그리기
# ─────────────────────────────────────────────
def draw_door(surface, door_dict, camera_x, camera_y):
    r  = door_dict['rect']
    sx, sy, sw, sh = r.x + camera_x, r.y + camera_y, r.width, r.height
    fp = int(8 * SCALE)
    pygame.draw.rect(surface, DOOR_FRAME_COLOR,
                     pygame.Rect(sx-fp, sy-fp, sw+fp*2, sh+fp*2), border_radius=4)
    pygame.draw.rect(surface, DOOR_CLOSED_COLOR, pygame.Rect(sx, sy, sw, sh), border_radius=3)
    knob_r = int(6 * SCALE)
    line_w = int(3 * SCALE)
    if door_dict['axis'] == 'v':
        mx = int(sx + sw // 2)
        pygame.draw.line(surface, (255,255,255), (mx, int(sy+6)), (mx, int(sy+sh-6)), line_w)
        pygame.draw.circle(surface, (220,220,220), (mx, int(sy+sh//2)), knob_r)
    else:
        my = int(sy + sh // 2)
        pygame.draw.line(surface, (255,255,255), (int(sx+6), my), (int(sx+sw-6), my), line_w)
        pygame.draw.circle(surface, (220,220,220), (int(sx+sw//2), my), knob_r)
    lx = int(sx + sw // 2)
    ly = int(sy + sh // 2) - int(10 * SCALE)
    lock_w, lock_h = int(14 * SCALE), int(10 * SCALE)
    pygame.draw.rect(surface, (255,200,0), pygame.Rect(lx - lock_w//2, ly + lock_h//2, lock_w, lock_h), border_radius=2)
    pygame.draw.arc(surface, (255,200,0), pygame.Rect(lx - lock_w//2 + 1, ly - lock_h//2, lock_w - 2, lock_h + 4), 0, math.pi, int(3 * SCALE))

# ─────────────────────────────────────────────
# 6. 플레이어
# ─────────────────────────────────────────────
GUN_VISIBLE_MS = 300

BURST_COUNT       = 4
BURST_INTERVAL_MS = 50
BURST_COOLDOWN_MS = 500

class Player:
    def __init__(self):
        self.world_x         = rooms[0].world_x + rooms[0].width  // 2
        self.world_y         = rooms[0].world_y + rooms[0].height // 2
        self.radius          = int(20 * SCALE)

        self.speed          = 6 * SCALE
        self.attack_range   = int(500 * SCALE)
        self.bullet_speed   = 18 * SCALE
        self.bullet_range   = int(800 * SCALE)
        self.bullet_radius  = int(6 * SCALE)

        self.burst_shots_fired = 0
        self.last_shot_time    = -9999
        self.burst_start_time  = -9999

        self.target_enemy    = None
        self.current_room_id = 1

        self.anim_frame    = 0
        self.anim_timer    = 0
        self.anim_interval = 120
        self.facing_right  = True
        self.is_moving     = False
        self.gun_angle     = 0.0

    def _can_fire(self, current_time):
        time_since_last = current_time - self.last_shot_time
        if self.burst_shots_fired < BURST_COUNT:
            return time_since_last >= BURST_INTERVAL_MS
        else:
            if time_since_last >= BURST_COOLDOWN_MS:
                self.burst_shots_fired = 0
                return True
            return False

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

        if self.is_moving and sprite_frames_right:
            if current_time - self.anim_timer > self.anim_interval:
                self.anim_frame = (self.anim_frame + 1) % SPRITE_FRAMES
                self.anim_timer = current_time
        else:
            self.anim_frame = 0

        self.target_enemy = None
        min_dist = self.attack_range
        for enemy in enemies:
            if active_room and active_room.rect.collidepoint(enemy.world_x, enemy.world_y):
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

        if self.target_enemy and self._can_fire(current_time):
            self.fire(bullets, current_time)

    def fire(self, bullets, current_time):
        bullets.append(Bullet(self.world_x, self.world_y, self.gun_angle,
                               self.bullet_speed, self.bullet_radius, self.bullet_range))
        self.last_shot_time   = current_time
        self.burst_shots_fired += 1

        if gun_sound:
            if self.burst_shots_fired == 1:
                gun_sound.set_volume(0.22)
            else:
                gun_sound.set_volume(0.13)
            gun_sound.play()

    def draw(self, surface, screen_cx, screen_cy, current_time):
        half = PLAYER_DRAW_SIZE // 2

        if sprite_frames_right:
            frames = sprite_frames_right if self.facing_right else sprite_frames_left
            surface.blit(frames[self.anim_frame], (screen_cx - half, screen_cy - half))
        else:
            pygame.draw.circle(surface, (50, 150, 255), (screen_cx, screen_cy), self.radius)

        time_since_shot = current_time - self.last_shot_time

        if time_since_shot < GUN_VISIBLE_MS and gun_rotated_cache_r:
            deg = int(math.degrees(self.gun_angle)) % 360

            if 90 < deg < 270:
                rotated = gun_rotated_cache_l[deg]
            else:
                rotated = gun_rotated_cache_r[deg]

            elapsed   = time_since_shot
            recoil_max   = int(8 * SCALE)
            recoil_ratio = max(0.0, 1.0 - elapsed / 120.0)
            recoil    = recoil_max * recoil_ratio
            recoil_dx = -math.cos(self.gun_angle) * recoil
            recoil_dy = -math.sin(self.gun_angle) * recoil

            offset = int(32 * SCALE)
            gun_cx = screen_cx + int(math.cos(self.gun_angle) * offset + recoil_dx)
            gun_cy = screen_cy + int(math.sin(self.gun_angle) * offset + recoil_dy) + int(10 * SCALE)
            surface.blit(rotated, rotated.get_rect(center=(gun_cx, gun_cy)))

            if time_since_shot < MUZZLE_VISIBLE_MS and muzzle_flash_cache_r:
                alpha = int(255 * (1.0 - time_since_shot / MUZZLE_VISIBLE_MS))
                muzzle_offset = offset + GUN_DRAW_SIZE * 0.55
                muzzle_x = screen_cx + int(math.cos(self.gun_angle) * muzzle_offset + recoil_dx)
                muzzle_y = screen_cy + int(math.sin(self.gun_angle) * muzzle_offset + recoil_dy) + int(10 * SCALE)

                if 90 < deg < 270:
                    flash_img = muzzle_flash_cache_l[deg].copy()
                else:
                    flash_img = muzzle_flash_cache_r[deg].copy()
                flash_img.set_alpha(alpha)
                surface.blit(flash_img, flash_img.get_rect(center=(muzzle_x, muzzle_y)))

# ─────────────────────────────────────────────
# 7. 적 / 총알
# ─────────────────────────────────────────────
class Enemy:
    def __init__(self, x, y, room_id):
        self.world_x = x; self.world_y = y
        self.radius  = int(22 * SCALE); self.room_id = room_id

class Bullet:
    def __init__(self, x, y, angle, speed, radius, max_range):
        self.world_x = x; self.world_y = y
        self.angle   = angle
        self.speed   = speed
        self.radius  = radius
        self.dx      = math.cos(angle) * speed
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
margin = int(80 * SCALE)
for room in rooms:
    if room.id != 1:
        room.has_enemies = True
        for _ in range(random.randint(3, 5)):
            ex = random.randint(room.world_x + margin, room.world_x + room.width  - margin)
            ey = random.randint(room.world_y + margin, room.world_y + room.height - margin)
            enemies.append(Enemy(ex, ey, room.id))
bullets = []
current_stage_text = "2-5"

# ─────────────────────────────────────────────
# 9. 미니맵 그리기 함수
# ─────────────────────────────────────────────
START_ROOM_ID = 1

def draw_minimap(surface, rooms, id_map, mini_connections, player_room_id, mm_x, mm_y):
    mm_box_w, mm_box_h = int(180 * SCALE), int(200 * SCALE)

    panel = pygame.Surface((mm_box_w, mm_box_h), pygame.SRCALPHA)
    panel.fill((8, 8, 12, 210))
    pygame.draw.rect(panel, (55, 55, 65, 255), (0, 0, mm_box_w, mm_box_h), 2, border_radius=8)
    surface.blit(panel, (mm_x, mm_y))

    icon_size    = int(22 * SCALE)
    grid_spacing = int(44 * SCALE)
    cx = mm_x + mm_box_w // 2 - int(10 * SCALE)
    cy = mm_y + int(30 * SCALE)

    for sid, eid in mini_connections:
        r1, r2 = id_map[sid], id_map[eid]
        x1 = cx + r1.grid_pos[0] * grid_spacing
        y1 = cy + r1.grid_pos[1] * grid_spacing
        x2 = cx + r2.grid_pos[0] * grid_spacing
        y2 = cy + r2.grid_pos[1] * grid_spacing
        pygame.draw.line(surface, (45, 45, 50), (x1, y1), (x2, y2), 5)

    for room in rooms:
        rcx = cx + room.grid_pos[0] * grid_spacing
        rcy = cy + room.grid_pos[1] * grid_spacing
        ir  = pygame.Rect(rcx - icon_size // 2, rcy - icon_size // 2, icon_size, icon_size)

        if room.id == player_room_id:
            bg_col     = (220, 220, 220)
            border_col = (255, 255, 255)
            border_w   = 2
        elif room.is_cleared:
            bg_col     = (55, 160, 75)
            border_col = (80, 200, 100)
            border_w   = 1
        else:
            bg_col     = (65, 65, 72)
            border_col = (90, 90, 100)
            border_w   = 1

        pygame.draw.rect(surface, bg_col, ir, border_radius=4)

        if room.has_enemies and not room.is_cleared:
            pygame.draw.rect(surface, (210, 50, 50), ir, 2, border_radius=4)
        else:
            pygame.draw.rect(surface, border_col, ir, border_w, border_radius=4)

        if room.id == START_ROOM_ID:
            icon_col = (40, 40, 40) if room.id != player_room_id else (30, 30, 30)
            hx, hy = rcx, rcy
            hs = int(6 * SCALE)
            roof_pts = [(hx - hs, hy - 1), (hx + hs, hy - 1), (hx, hy - hs*1.3)]
            pygame.draw.polygon(surface, icon_col, roof_pts)
            pygame.draw.rect(surface, icon_col, pygame.Rect(hx - hs + 2, hy - 1, (hs-2)*2, int(6*SCALE)))
            pygame.draw.rect(surface, bg_col,   pygame.Rect(hx - 1, hy + 1, int(3*SCALE), int(5*SCALE)))

    stage_surf = font_mini.render(current_stage_text, True, (180, 180, 180))
    surface.blit(stage_surf, stage_surf.get_rect(centerx=mm_x + mm_box_w // 2,
                                                  top=mm_y + mm_box_h - int(18 * SCALE)))

# ─────────────────────────────────────────────
# 피아노 그리기 함수
# ─────────────────────────────────────────────
def draw_piano(surface, camera_x, camera_y, near_piano):
    sx = PIANO_WORLD_X + camera_x
    sy = PIANO_WORLD_Y + camera_y

    if piano_img:
        surface.blit(piano_img, (sx, sy))
    else:
        pygame.draw.rect(surface, (40, 30, 20), pygame.Rect(sx, sy, PIANO_DRAW_W, PIANO_DRAW_H))
        pygame.draw.rect(surface, (80, 60, 40), pygame.Rect(sx, sy, PIANO_DRAW_W, PIANO_DRAW_H), 3)
        piano_label = font_mini.render("PIANO", True, (200, 200, 180))
        surface.blit(piano_label, piano_label.get_rect(center=(sx + PIANO_DRAW_W//2,
                                                                sy + PIANO_DRAW_H//2)))

    if near_piano:
        bgm_names = ["BGM 1", "BGM 2", "BGM 3"]
        next_idx  = (bgm_current_index + 1) % 3
        prompt_text = f"악보 교체하기  [E]  →  {bgm_names[next_idx]}"
        prompt_surf = font_prompt.render(prompt_text, True, (255, 240, 100))
        pad = int(10 * SCALE)
        bg_rect = pygame.Rect(sx + PIANO_DRAW_W//2 - prompt_surf.get_width()//2 - pad,
                               sy - int(42 * SCALE),
                               prompt_surf.get_width() + pad*2,
                               prompt_surf.get_height() + pad)
        bg_surf = pygame.Surface((bg_rect.width, bg_rect.height), pygame.SRCALPHA)
        bg_surf.fill((0, 0, 0, 170))
        surface.blit(bg_surf, (bg_rect.x, bg_rect.y))
        surface.blit(prompt_surf, prompt_surf.get_rect(centerx=sx + PIANO_DRAW_W//2,
                                                        top=sy - int(36 * SCALE)))

# ─────────────────────────────────────────────
# 10. 타이틀 화면
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
# 11. 메인 루프
# ─────────────────────────────────────────────
game_state = "title"
running    = True
bgm_started = False
piano_e_pressed_prev = False

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

    if not bgm_started:
        play_bgm(0)
        bgm_started = True

    keys = pygame.key.get_pressed()
    player.update(keys, enemies, current_time, bullets)

    piano_cx   = PIANO_WORLD_X + PIANO_DRAW_W // 2
    piano_cy   = PIANO_WORLD_Y + PIANO_DRAW_H // 2
    dist_piano = math.hypot(player.world_x - piano_cx, player.world_y - piano_cy)
    near_piano = dist_piano < PIANO_INTERACT_RADIUS

    e_pressed_now = keys[pygame.K_e]
    if near_piano and e_pressed_now and not piano_e_pressed_prev:
        play_bgm(bgm_current_index + 1)
    piano_e_pressed_prev = e_pressed_now

    for room in rooms:
        if room.has_enemies:
            room.is_cleared = not any(e.room_id == room.id for e in enemies)
        else:
            room.is_cleared = True

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

    for room in rooms:
        screen.blit(room.floor_surf, (room.world_x + camera_x, room.world_y + camera_y))
        rr = pygame.Rect(room.world_x+camera_x, room.world_y+camera_y, room.width, room.height)
        pygame.draw.rect(screen, WALL_COLOR, rr, int(8 * SCALE))

    for corr in corridors:
        pygame.draw.rect(screen, FLOOR_COLOR_A,
                         (corr.x+camera_x, corr.y+camera_y, corr.width, corr.height))

    draw_piano(screen, camera_x, camera_y, near_piano)

    active_room_now = next((r for r in rooms if r.rect.collidepoint(player.world_x, player.world_y)), None)
    if active_room_now and active_room_now.has_enemies and not active_room_now.is_cleared:
        for door_dict in active_room_now.doors:
            draw_door(screen, door_dict, camera_x, camera_y)

    for enemy in enemies:
        ex = int(enemy.world_x + camera_x)
        ey = int(enemy.world_y + camera_y)
        er = enemy.radius
        pygame.draw.circle(screen, ENEMY_COLOR, (ex, ey), er)
        eye_off = int(6 * SCALE)
        eye_r1  = int(5 * SCALE)
        eye_r2  = int(3 * SCALE)
        eye_y   = int(5 * SCALE)
        pygame.draw.circle(screen, (255,255,255), (ex-eye_off, ey-eye_y), eye_r1)
        pygame.draw.circle(screen, (255,255,255), (ex+eye_off, ey-eye_y), eye_r1)
        pygame.draw.circle(screen, (0,0,0),       (ex-eye_off+1, ey-eye_y), eye_r2)
        pygame.draw.circle(screen, (0,0,0),       (ex+eye_off+1, ey-eye_y), eye_r2)

    for bullet in bullets:
        pygame.draw.circle(screen, BULLET_COLOR,
                           (int(bullet.world_x+camera_x), int(bullet.world_y+camera_y)), bullet.radius)

    player.draw(screen, WIDTH//2, HEIGHT//2, current_time)

    mm_x = WIDTH  - int(200 * SCALE)
    mm_y = 20
    draw_minimap(screen, rooms, id_map, mini_connections, player.current_room_id, mm_x, mm_y)

    pygame.display.flip()
    clock.tick(60)

pygame.quit()
sys.exit()