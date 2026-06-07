import pygame
import sys
import math
import random
import os

# ─────────────────────────────────────────────
# 경로 설정
# ─────────────────────────────────────────────
BASE_DIR   = os.path.dirname(os.path.abspath(__file__))
ASSETS_DIR = os.path.join(BASE_DIR, "assets")

# ─────────────────────────────────────────────
# 1. 초기화
# ─────────────────────────────────────────────
pygame.init()
pygame.mixer.init(frequency=44100, size=-16, channels=2, buffer=512)

SCALE = 1.2

WIDTH, HEIGHT = 1000, 700
screen = pygame.display.set_mode((WIDTH, HEIGHT))
pygame.display.set_caption("Nocturne Echoes")
clock = pygame.time.Clock()

_nanum_path = os.path.join(ASSETS_DIR, "NanumGothic.ttf")
def _make_font(size, bold=False):
    if os.path.exists(_nanum_path):
        return pygame.font.Font(_nanum_path, size)
    return pygame.font.SysFont("arial", size, bold=bold)

font_medium    = _make_font(int(32 * SCALE), bold=True)
font_ui        = _make_font(int(28 * SCALE), bold=True)
font_mini      = _make_font(int(11 * SCALE), bold=True)
font_prompt    = _make_font(int(20 * SCALE), bold=True)
font_dlg_name  = _make_font(26, bold=True)
font_dlg_affil = _make_font(15)
font_dlg_text  = _make_font(19)
font_dlg_space = _make_font(14, bold=True)
font_narr      = _make_font(21)

# ─────────────────────────────────────────────
# 색상
# ─────────────────────────────────────────────
BG_COLOR          = (15,  15,  18)
WALL_COLOR        = (60,  60,  65)
FLOOR_COLOR_A     = (35,  35,  40)
FLOOR_COLOR_B     = (45,  45,  52)
ENEMY_COLOR       = (255, 80,  80)
BULLET_COLOR      = (200, 100, 255)
DOOR_CLOSED_COLOR = (200, 40,  40)
DOOR_FRAME_COLOR  = (100, 100, 110)

CHECKER_SIZE = int(100 * SCALE)

# ─────────────────────────────────────────────
# 2. 에셋 로드
# ─────────────────────────────────────────────
def load_image_colorkey(path, colorkey=(0, 0, 0)):
    img = pygame.image.load(path).convert()
    img.set_colorkey(colorkey)
    return img

# 타이틀
title_img = None
title_img_path = os.path.join(ASSETS_DIR, "start.png")
if os.path.exists(title_img_path):
    raw = pygame.image.load(title_img_path).convert_alpha()
    img_w, img_h = raw.get_size()
    s = min(WIDTH / img_w, HEIGHT / img_h)
    title_img = pygame.transform.smoothscale(raw, (int(img_w * s), int(img_h * s)))

# ── 히나 방 이미지 (정사각형, 높이에 맞춤) ──
hina_room_img  = None
hina_room_rect = None
hina_room_path = os.path.join(ASSETS_DIR, "hina_room.png")
if os.path.exists(hina_room_path):
    _raw_room  = pygame.image.load(hina_room_path).convert()
    _room_size = min(HEIGHT, WIDTH)
    hina_room_img  = pygame.transform.scale(_raw_room, (_room_size, _room_size))
    hina_room_rect = hina_room_img.get_rect(center=(WIDTH // 2, HEIGHT // 2))

# ── 선도부실 이미지 (정사각형, 히나 방과 동일 사이즈) ──
prefect_room_img  = None
prefect_room_rect = None
prefect_room_path = os.path.join(ASSETS_DIR, "prefect_room.png")
if os.path.exists(prefect_room_path):
    _raw_pr = pygame.image.load(prefect_room_path).convert()
    _room_size_pr = min(HEIGHT, WIDTH)
    prefect_room_img  = pygame.transform.scale(_raw_pr, (_room_size_pr, _room_size_pr))
    prefect_room_rect = prefect_room_img.get_rect(center=(WIDTH // 2, HEIGHT // 2))

# ── aco 캐릭터 이미지 로드 ──
# ★ FIX 1: convert_alpha() + colorkey (0,0,0) 적용해서 검은 배경 제거
# 원본 비율 190(가로) x 250(세로), 히나와 동일한 높이(int(64*SCALE)) 기준으로 가로 맞춤
_AKO_ORIG_W, _AKO_ORIG_H = 190, 250
_AKO_TARGET_H = int(64 * SCALE)
_AKO_TARGET_W = int(_AKO_TARGET_H * _AKO_ORIG_W / _AKO_ORIG_H)
ACO_DRAW_W = _AKO_TARGET_W
ACO_DRAW_H = _AKO_TARGET_H
ACO_DRAW_SIZE = max(ACO_DRAW_W, ACO_DRAW_H)  # 기존 코드와의 호환용

aco_img = None
aco_img_path = os.path.join(ASSETS_DIR, "ako.png")
if os.path.exists(aco_img_path):
    try:
        _aco_raw = pygame.image.load(aco_img_path).convert_alpha()
        _aco_scaled = pygame.transform.scale(_aco_raw, (ACO_DRAW_W, ACO_DRAW_H))
        _aco_scaled.set_colorkey((0, 0, 0))
        aco_img = _aco_scaled
    except Exception as e:
        print(f"[WARN] ako 이미지 로드 실패: {e}")
        # 로드 실패 시 None 유지 → 원(circle)으로 폴백

# aco 선도부실 화면 위치 (책상 앞)
ACO_SCREEN_POS      = (430, 400)
ACO_INTERACT_RADIUS = 100

# ── 히나 방 인터렉션 핫스팟 (화면 좌표) ──
WARDROBE_POS    = (770, 460)
WARDROBE_RADIUS = 80
BED_POS    = (340, 260)
BED_RADIUS = 80

# 스프라이트
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
        sc = pygame.transform.scale(frame_raw, (PLAYER_DRAW_SIZE, PLAYER_DRAW_SIZE))
        sc.set_colorkey((0, 0, 0))
        sprite_frames_right.append(sc)
        fl = pygame.transform.flip(sc, True, False)
        fl.set_colorkey((0, 0, 0))
        sprite_frames_left.append(fl)

# ── 수면복 스프라이트 ──
sleep_frames_right = []
sleep_frames_left  = []
hina_sleep_path = os.path.join(ASSETS_DIR, "hina_sleep_move.png")
if os.path.exists(hina_sleep_path):
    sleep_sheet = load_image_colorkey(hina_sleep_path)
    for i in range(SPRITE_FRAMES):
        frame_raw = sleep_sheet.subsurface(pygame.Rect(i * SPRITE_FRAME_W, 0, SPRITE_FRAME_W, SPRITE_FRAME_H))
        sc = pygame.transform.scale(frame_raw, (PLAYER_DRAW_SIZE, PLAYER_DRAW_SIZE))
        sc.set_colorkey((0, 0, 0))
        sleep_frames_right.append(sc)
        fl = pygame.transform.flip(sc, True, False)
        fl.set_colorkey((0, 0, 0))
        sleep_frames_left.append(fl)

# 총
GUN_DRAW_SIZE = int(60 * SCALE)
gun_img_right = None
gun_img_path  = os.path.join(ASSETS_DIR, "hina_gun.png")
if os.path.exists(gun_img_path):
    gun_raw       = load_image_colorkey(gun_img_path)
    gun_img_right = pygame.transform.scale(gun_raw, (GUN_DRAW_SIZE, GUN_DRAW_SIZE))
    gun_img_right.set_colorkey((0, 0, 0))

gun_rotated_cache_r = {}
gun_rotated_cache_l = {}
if gun_img_right:
    gun_img_left = pygame.transform.flip(gun_img_right, False, True)
    gun_img_left.set_colorkey((0, 0, 0))
    for deg in range(360):
        r = pygame.transform.rotate(gun_img_right, -deg); r.set_colorkey((0,0,0))
        l = pygame.transform.rotate(gun_img_left,  -deg); l.set_colorkey((0,0,0))
        gun_rotated_cache_r[deg] = r
        gun_rotated_cache_l[deg] = l

MUZZLE_DRAW_SIZE  = int(40 * SCALE)
MUZZLE_VISIBLE_MS = 60
muzzle_flash_cache_r = {}
muzzle_flash_cache_l = {}

shot_img_path = os.path.join(ASSETS_DIR, "shot.png")
if os.path.exists(shot_img_path):
    shot_raw    = pygame.image.load(shot_img_path).convert_alpha()
    shot_scaled = pygame.transform.scale(shot_raw, (MUZZLE_DRAW_SIZE, MUZZLE_DRAW_SIZE))
    for deg in range(360):
        muzzle_flash_cache_r[deg] = pygame.transform.rotate(shot_scaled, -deg)
        muzzle_flash_cache_l[deg] = pygame.transform.rotate(
            pygame.transform.flip(shot_scaled, False, True), -deg)

gun_sound = None
_gun_sound_path = os.path.join(ASSETS_DIR, "gun_sound.mp3")
if os.path.exists(_gun_sound_path):
    try:
        gun_sound = pygame.mixer.Sound(_gun_sound_path)
        gun_sound.set_volume(0.18)
    except Exception as e:
        print(f"[WARN] gun_sound 로드 실패: {e}")

PIANO_DRAW_W = int(130 * SCALE)
PIANO_DRAW_H = int(112 * SCALE)
piano_img = None
piano_img_path = os.path.join(ASSETS_DIR, "piano.png")
if os.path.exists(piano_img_path):
    try:
        piano_raw = pygame.image.load(piano_img_path).convert_alpha()
        piano_img = pygame.transform.scale(piano_raw, (PIANO_DRAW_W, PIANO_DRAW_H))
    except Exception as e:
        print(f"[WARN] piano 이미지 로드 실패: {e}")

BGM_FILES = [
    os.path.join(ASSETS_DIR, "bgm0.opus"),
    os.path.join(ASSETS_DIR, "bgm1.opus"),
    os.path.join(ASSETS_DIR, "bgm2.opus"),
    os.path.join(ASSETS_DIR, "bgm3.opus"),
]
FUNKY_ROAD_PATH = os.path.join(ASSETS_DIR, "funky_road.opus")
bgm_current_index = 0

def play_bgm(index):
    global bgm_current_index
    bgm_current_index = index % len(BGM_FILES)
    path = BGM_FILES[bgm_current_index]
    if os.path.exists(path):
        try:
            pygame.mixer.music.load(path)
            pygame.mixer.music.set_volume(0.5)
            pygame.mixer.music.play(-1)
        except Exception as e:
            print(f"[WARN] BGM 로드 실패: {e}")

def play_funky_road():
    path = os.path.join(ASSETS_DIR, "funky_road.opus")
    if os.path.exists(path):
        try:
            pygame.mixer.music.load(path)
            pygame.mixer.music.set_volume(0.5)
            pygame.mixer.music.play(-1)
        except Exception as e:
            print(f"[WARN] funky_road 로드 실패: {e}")
    else:
        print("[WARN] funky_road.opus 파일 없음")

# ─────────────────────────────────────────────
# 히나 방 이동 가능 구역
# ─────────────────────────────────────────────
_HINA_WALK_POLY = [
    (240, 580),
    (240, 320),
    (370, 320),
    (370, 250),
    (710, 250),
    (710, 580),
]

# ─────────────────────────────────────────────
# 선도부실 이동 가능 구역
# ─────────────────────────────────────────────
_PREFECT_WALK_POLY = [
    (280, 600),
    (280, 450),
    (350, 450),
    (350, 190),
    (700, 190),
    (700, 600),
]

# ─────────────────────────────────────────────
# 공용 폴리곤 판정 함수
# ─────────────────────────────────────────────
def _point_in_poly(px, py, poly):
    n = len(poly)
    inside = False
    j = n - 1
    for i in range(n):
        xi, yi = poly[i]
        xj, yj = poly[j]
        if ((yi > py) != (yj > py)) and (px < (xj - xi) * (py - yi) / (yj - yi + 1e-10) + xi):
            inside = not inside
        j = i
    return inside

def _point_in_hina_walkzone(px, py):
    return _point_in_poly(px, py, _HINA_WALK_POLY)

def _point_in_prefect_walkzone(px, py):
    return _point_in_poly(px, py, _PREFECT_WALK_POLY)

# ─────────────────────────────────────────────
# 3. 전투 맵 워크존 (이미지 좌표 기준, 1000x700 화면)
# ─────────────────────────────────────────────
# 이미지를 1000x700으로 스케일한 기준 좌표
# 수정하려면 아래 폴리곤 꼭짓점을 조정하세요
# 디버그 모드(F10 → 전투맵)에서 초록 폴리곤으로 표시됩니다

# ── 배틀맵 스케일 상수 (여기서 배율 조정) ──
BATTLE_MAP_SCALE = 2.5        # 이미지 원본 대비 배율 (변경 시 이 숫자만 수정)
BATTLE_MAP_W = int(WIDTH  * BATTLE_MAP_SCALE)   # 월드 가로 (2500)
BATTLE_MAP_H = int(HEIGHT * BATTLE_MAP_SCALE)   # 월드 세로 (1750)

# ── 전투 배경 이미지 ──
battle_bg_img  = None
battle_bg_path = os.path.join(ASSETS_DIR, "gehenna.png")
if os.path.exists(battle_bg_path):
    try:
        _bbg_raw      = pygame.image.load(battle_bg_path).convert()
        battle_bg_img = pygame.transform.scale(_bbg_raw, (BATTLE_MAP_W, BATTLE_MAP_H))
    except Exception as e:
        print(f"[WARN] battle_map 로드 실패: {e}")

_S = BATTLE_MAP_SCALE  # 좌표 곱셈용 단축 변수

# 전체 이동 가능 구역 — 원본 이미지 좌표 × _S
# 수정 시 숫자는 1000x700 기준 원본 좌표, _S 곱해서 실제 월드 좌표가 됩니다
def _si(v): return int(v * _S)  # 스케일 곱하고 int 변환 헬퍼

_BATTLE_WALK_POLYS = [
    # 중앙 홀 (메인 통로)
    [(_si(310), _si(28)),  (_si(740), _si(28)),  (_si(740), _si(672)), (_si(310), _si(672))],
    # 좌상 교실
    [(_si(28),  _si(28)),  (_si(285), _si(28)),  (_si(285), _si(262)), (_si(28),  _si(262))],
    # 우상 휴게실
    [(_si(757), _si(28)),  (_si(980), _si(28)),  (_si(980), _si(262)), (_si(757), _si(262))],
    # 좌중 창고
    [(_si(28),  _si(283)), (_si(285), _si(283)), (_si(285), _si(465)), (_si(28),  _si(465))],
    # 우중 교무실
    [(_si(757), _si(283)), (_si(980), _si(283)), (_si(980), _si(465)), (_si(757), _si(465))],
    # 좌하 식당
    [(_si(28),  _si(487)), (_si(285), _si(487)), (_si(285), _si(672)), (_si(28),  _si(672))],
    # 우하 입구 (히나 시작 위치)
    [(_si(757), _si(487)), (_si(980), _si(487)), (_si(980), _si(672)), (_si(757), _si(672))],
]

# 각 방 ↔ 중앙 홀 연결 통로
_BATTLE_CORRIDOR_RECTS = [
    pygame.Rect(_si(285), _si(80),  _si(30), _si(120)),   # 좌상
    pygame.Rect(_si(740), _si(80),  _si(30), _si(120)),   # 우상
    pygame.Rect(_si(285), _si(310), _si(30), _si(100)),   # 좌중
    pygame.Rect(_si(740), _si(310), _si(30), _si(100)),   # 우중
    pygame.Rect(_si(285), _si(530), _si(30), _si(100)),   # 좌하
    pygame.Rect(_si(740), _si(530), _si(30), _si(100)),   # 우하
]

def _point_in_battle_walkzone(px, py):
    for poly in _BATTLE_WALK_POLYS:
        if _point_in_poly(px, py, poly):
            return True
    for rect in _BATTLE_CORRIDOR_RECTS:
        if rect.collidepoint(int(px), int(py)):
            return True
    return False

# 히나 전투맵 시작 위치 (우하단 문 앞)
BATTLE_START_X = 870.0 * BATTLE_MAP_SCALE
BATTLE_START_Y = 620.0 * BATTLE_MAP_SCALE

# 미니맵용 더미 (draw_minimap 호환 유지)
rooms            = []
id_map           = {}
corridors        = []
mini_connections = []

# ─────────────────────────────────────────────
# 4. 방·통로 생성  ← 전투맵 이미지로 대체되어 비워둠
# ─────────────────────────────────────────────
# (기존 Room/corridor 시스템 제거)

# ─────────────────────────────────────────────
# 5. 문 그리기  ← 전투맵에서는 사용 안 함
# ─────────────────────────────────────────────

# ─────────────────────────────────────────────
# 6. 플레이어
# ─────────────────────────────────────────────
GUN_VISIBLE_MS    = 300
BURST_COUNT       = 4
BURST_INTERVAL_MS = 50
BURST_COOLDOWN_MS = 700

class Player:
    def __init__(self):
        self.world_x = BATTLE_START_X
        self.world_y = BATTLE_START_Y
        self.radius  = int(20 * SCALE)

        self.speed         = 5 * SCALE
        self.attack_range  = int(300 * SCALE)
        self.bullet_speed  = 14 * SCALE
        self.bullet_range  = int(500 * SCALE)
        self.bullet_radius = int(5 * SCALE)

        self.burst_shots_fired = 0
        self.last_shot_time    = -9999

        self.target_enemy    = None
        self.current_room_id = 1

        self.anim_frame    = 0
        self.anim_timer    = 0
        self.anim_interval = 120
        self.facing_right  = True
        self.is_moving     = False
        self.gun_angle     = 0.0

        self.hina_sx = float(WIDTH  // 2)
        self.hina_sy = float(HEIGHT // 2)
        self.costume = "uniform"

    def _can_fire(self, current_time):
        dt = current_time - self.last_shot_time
        if self.burst_shots_fired < BURST_COUNT:
            return dt >= BURST_INTERVAL_MS
        else:
            if dt >= BURST_COOLDOWN_MS:
                self.burst_shots_fired = 0
                return True
            return False

    def update_hina_room(self, keys, current_time):
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

        walk_speed = self.speed * 0.5
        nx = self.hina_sx + dx * walk_speed
        ny = self.hina_sy + dy * walk_speed

        if _point_in_hina_walkzone(nx, ny):
            self.hina_sx, self.hina_sy = nx, ny
        else:
            if _point_in_hina_walkzone(nx, self.hina_sy):
                self.hina_sx = nx
            elif _point_in_hina_walkzone(self.hina_sx, ny):
                self.hina_sy = ny

        if self.is_moving and sprite_frames_right:
            if current_time - self.anim_timer > self.anim_interval:
                self.anim_frame = (self.anim_frame + 1) % SPRITE_FRAMES
                self.anim_timer = current_time
        else:
            self.anim_frame = 0

    def update_prefect_room(self, keys, current_time):
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

        walk_speed = self.speed * 0.5
        nx = self.hina_sx + dx * walk_speed
        ny = self.hina_sy + dy * walk_speed

        if _point_in_prefect_walkzone(nx, ny):
            self.hina_sx, self.hina_sy = nx, ny
        else:
            if _point_in_prefect_walkzone(nx, self.hina_sy):
                self.hina_sx = nx
            elif _point_in_prefect_walkzone(self.hina_sx, ny):
                self.hina_sy = ny

        if self.is_moving and sprite_frames_right:
            if current_time - self.anim_timer > self.anim_interval:
                self.anim_frame = (self.anim_frame + 1) % SPRITE_FRAMES
                self.anim_timer = current_time
        else:
            self.anim_frame = 0

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

        nx = self.world_x + dx * self.speed
        ny = self.world_y + dy * self.speed

        # 전투 워크존 기반 이동 (카메라 오프셋 없음 — world == screen)
        if _point_in_battle_walkzone(nx, ny):
            self.world_x, self.world_y = nx, ny
        else:
            if _point_in_battle_walkzone(nx, self.world_y):
                self.world_x = nx
            elif _point_in_battle_walkzone(self.world_x, ny):
                self.world_y = ny

        if self.is_moving and sprite_frames_right:
            if current_time - self.anim_timer > self.anim_interval:
                self.anim_frame = (self.anim_frame + 1) % SPRITE_FRAMES
                self.anim_timer = current_time
        else:
            self.anim_frame = 0

        self.target_enemy = None
        min_dist = self.attack_range
        for enemy in enemies:
            ddx = enemy.world_x - self.world_x
            ddy = enemy.world_y - self.world_y
            d_sq = ddx*ddx + ddy*ddy
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
        self.last_shot_time    = current_time
        self.burst_shots_fired += 1
        if gun_sound:
            gun_sound.set_volume(0.22 if self.burst_shots_fired == 1 else 0.13)
            gun_sound.play()

    def draw(self, surface, screen_cx, screen_cy, current_time):
        half = PLAYER_DRAW_SIZE // 2
        if self.costume == "sleep" and sleep_frames_right:
            frames = sleep_frames_right if self.facing_right else sleep_frames_left
        elif sprite_frames_right:
            frames = sprite_frames_right if self.facing_right else sprite_frames_left
        else:
            frames = None

        if frames:
            surface.blit(frames[self.anim_frame], (screen_cx - half, screen_cy - half))
        else:
            pygame.draw.circle(surface, (50,150,255), (screen_cx, screen_cy), self.radius)

        time_since_shot = current_time - self.last_shot_time
        if time_since_shot < GUN_VISIBLE_MS and gun_rotated_cache_r:
            deg = int(math.degrees(self.gun_angle)) % 360
            rotated = gun_rotated_cache_l[deg] if 90 < deg < 270 else gun_rotated_cache_r[deg]

            recoil    = int(8 * SCALE) * max(0.0, 1.0 - time_since_shot / 120.0)
            recoil_dx = -math.cos(self.gun_angle) * recoil
            recoil_dy = -math.sin(self.gun_angle) * recoil
            offset    = int(32 * SCALE)
            gun_cx = screen_cx + int(math.cos(self.gun_angle) * offset + recoil_dx)
            gun_cy = screen_cy + int(math.sin(self.gun_angle) * offset + recoil_dy) + int(10*SCALE)
            surface.blit(rotated, rotated.get_rect(center=(gun_cx, gun_cy)))

            if time_since_shot < MUZZLE_VISIBLE_MS and muzzle_flash_cache_r:
                alpha = int(255 * (1.0 - time_since_shot / MUZZLE_VISIBLE_MS))
                mo    = offset + GUN_DRAW_SIZE * 0.55
                mx2   = screen_cx + int(math.cos(self.gun_angle) * mo + recoil_dx)
                my2   = screen_cy + int(math.sin(self.gun_angle) * mo + recoil_dy) + int(10*SCALE)
                cache = muzzle_flash_cache_l if 90 < deg < 270 else muzzle_flash_cache_r
                fi    = cache[deg].copy()
                fi.set_alpha(alpha)
                surface.blit(fi, fi.get_rect(center=(mx2, my2)))

# ─────────────────────────────────────────────
# 7. 적 / 총알
# ─────────────────────────────────────────────
class Enemy:
    def __init__(self, x, y, room_id):
        self.world_x = x; self.world_y = y
        self.radius  = int(22 * SCALE)
        self.room_id = room_id

class Bullet:
    def __init__(self, x, y, angle, speed, radius, max_range):
        self.world_x = x; self.world_y = y
        self.dx = math.cos(angle) * speed
        self.dy = math.sin(angle) * speed
        self.radius = radius
        self.distance_traveled = 0
        self.max_range = max_range

    def update(self):
        self.world_x += self.dx
        self.world_y += self.dy
        self.distance_traveled += math.hypot(self.dx, self.dy)

# ─────────────────────────────────────────────
# 8. 객체 생성 및 적 배치
# ─────────────────────────────────────────────
player  = Player()
player.world_x = BATTLE_START_X
player.world_y = BATTLE_START_Y

# 전투맵 적 배치 — 각 방 안에 랜덤 배치
enemies = []
_s = BATTLE_MAP_SCALE
_BATTLE_ENEMY_ZONES = [
    (int(28*_s),  int(28*_s),  int(285*_s), int(262*_s)),   # 좌상 교실
    (int(757*_s), int(28*_s),  int(980*_s), int(262*_s)),   # 우상 휴게실
    (int(28*_s),  int(283*_s), int(285*_s), int(465*_s)),   # 좌중 창고
    (int(757*_s), int(283*_s), int(980*_s), int(465*_s)),   # 우중 교무실
    (int(28*_s),  int(487*_s), int(285*_s), int(672*_s)),   # 좌하 식당
]
_mg = int(30 * BATTLE_MAP_SCALE)
for (x1, y1, x2, y2) in _BATTLE_ENEMY_ZONES:
    for _ in range(random.randint(2, 4)):
        ex = random.randint(x1 + _mg, x2 - _mg)
        ey = random.randint(y1 + _mg, y2 - _mg)
        enemies.append(Enemy(ex, ey, 0))
bullets = []
current_stage_text = "2-5"

# ─────────────────────────────────────────────
# 9. 미니맵
# ─────────────────────────────────────────────
START_ROOM_ID = 1

def draw_minimap(surface, rooms, id_map, mini_connections, player_room_id, mm_x, mm_y):
    mm_box_w = int(180 * SCALE)
    mm_box_h = int(200 * SCALE)
    panel = pygame.Surface((mm_box_w, mm_box_h), pygame.SRCALPHA)
    panel.fill((8, 8, 12, 210))
    pygame.draw.rect(panel, (55,55,65,255), (0,0,mm_box_w,mm_box_h), 2, border_radius=8)
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
        pygame.draw.line(surface, (45,45,50), (x1,y1), (x2,y2), 5)

    for room in rooms:
        rcx = cx + room.grid_pos[0] * grid_spacing
        rcy = cy + room.grid_pos[1] * grid_spacing
        ir  = pygame.Rect(rcx - icon_size//2, rcy - icon_size//2, icon_size, icon_size)

        if room.id == player_room_id:
            bg_col, border_col, border_w = (220,220,220), (255,255,255), 2
        elif room.is_cleared:
            bg_col, border_col, border_w = (55,160,75), (80,200,100), 1
        else:
            bg_col, border_col, border_w = (65,65,72), (90,90,100), 1

        pygame.draw.rect(surface, bg_col, ir, border_radius=4)
        if room.has_enemies and not room.is_cleared:
            pygame.draw.rect(surface, (210,50,50), ir, 2, border_radius=4)
        else:
            pygame.draw.rect(surface, border_col, ir, border_w, border_radius=4)

        if room.id == START_ROOM_ID:
            icon_col = (40,40,40) if room.id != player_room_id else (30,30,30)
            hx, hy = rcx, rcy
            hs = int(6 * SCALE)
            pygame.draw.polygon(surface, icon_col,
                                 [(hx-hs, hy-1), (hx+hs, hy-1), (hx, hy-int(hs*1.3))])
            pygame.draw.rect(surface, icon_col,
                             pygame.Rect(hx-hs+2, hy-1, (hs-2)*2, int(6*SCALE)))
            pygame.draw.rect(surface, bg_col,
                             pygame.Rect(hx-1, hy+1, int(3*SCALE), int(5*SCALE)))

    ss = font_mini.render(current_stage_text, True, (180,180,180))
    surface.blit(ss, ss.get_rect(centerx=mm_x+mm_box_w//2, top=mm_y+mm_box_h-int(18*SCALE)))

# ─────────────────────────────────────────────
# 피아노
# ─────────────────────────────────────────────
def draw_piano(surface, camera_x, camera_y, near_piano):
    sx = PIANO_WORLD_X + camera_x
    sy = PIANO_WORLD_Y + camera_y
    if piano_img:
        surface.blit(piano_img, (sx, sy))
    else:
        pygame.draw.rect(surface, (40,30,20), pygame.Rect(sx, sy, PIANO_DRAW_W, PIANO_DRAW_H))
        pygame.draw.rect(surface, (80,60,40), pygame.Rect(sx, sy, PIANO_DRAW_W, PIANO_DRAW_H), 3)
        lbl = font_mini.render("PIANO", True, (200,200,180))
        surface.blit(lbl, lbl.get_rect(center=(sx+PIANO_DRAW_W//2, sy+PIANO_DRAW_H//2)))
    if near_piano:
        bgm_names = ["BGM 1", "BGM 2", "BGM 3"]
        next_idx  = (bgm_current_index + 1) % 3
        ps = font_prompt.render(f"악보 교체하기  [E]  →  {bgm_names[next_idx]}", True, (255,240,100))
        pad = int(10 * SCALE)
        bgs = pygame.Surface((ps.get_width()+pad*2, ps.get_height()+pad), pygame.SRCALPHA)
        bgs.fill((0,0,0,170))
        surface.blit(bgs, (sx+PIANO_DRAW_W//2-bgs.get_width()//2, sy-int(42*SCALE)))
        surface.blit(ps, ps.get_rect(centerx=sx+PIANO_DRAW_W//2, top=sy-int(36*SCALE)))

# ─────────────────────────────────────────────
# 오프닝 나레이션
# ─────────────────────────────────────────────
OPENING_LINES = [
    "총성과 소동이 끊이지 않는 무질서의 학원 게헨나.",
    "그들을 단속하는 선도부장 히나조차, 연주회 직후 몰려든 과도한 업무에 골머리를 앓고 있었다.",
    "산더미 같은 업무를 마치고 방으로 돌아와 잠을 청하려던 그날 밤.",
]

# ─────────────────────────────────────────────
# 대화 데이터
# ─────────────────────────────────────────────
HINA_ROOM_DIALOG = [
    ("", "", "(하아…… 드디어 끝났군.)"),
    ("", "", "(연주회가 끝나면 잠시 숨 좀 돌릴 수 있을 줄 알았는데…….)"),
    ("", "", "(그새를 못 참고 만마전에서 소동을 벌이다니.)"),
    ("", "", "(정말이지, 잠시도 방심할 수가 없군.)"),
    ("", "", "(……일단 옷부터 갈아입고 자야겠어.)"),
    ("", "", "(아무리 피곤해도 제복 차림으로 침대에 눕고 싶진 않으니까.)"),
]

BED_UNIFORM_DIALOG = [
    ("", "", "(……아무리 피곤해도 제복을 입은 채로 침대에 누울 수는 없어.)"),
    ("", "", "(귀찮더라도 잠옷으로 갈아입고 자야겠어.)"),
]

BED_SLEEP_DIALOG = [
    ("???", "", "정해진 악보에서 벗어난 선율이여……."),
    ("???", "", "이제 마지막 장을 넘길 시간이다."),

    ("히나", "선도부", "……!?"),

    ("", "", "(불쾌한 목소리에 황급히 주위를 둘러보았지만, 그곳에는 아무도 없었다.)"),

    ("히나", "선도부", "……누구지?"),

    ("", "", "(설마, 과로 때문에 환청이라도 들리는 건가…….)"),
    ("", "", "(환청까지 들리다니…….)"),
    ("", "", "(확실히 무리한 모양이군.)"),

    ("", "", "(……지금은 신경 쓸 여유가 없어.)"),
    ("", "", "(우선 자도록 하자.)"),
]

ACO_DIALOG = [
    ("히나", "선도부", "...아코."),
    ("아코", "선도부", "아, 히나 선도부장님. 오셨군요."),
    ("히나", "선도부", "무슨 일이지?"),
    ("아코", "선도부", "최근 여러 학원에서 심상치 않은 사건들이 발생하고 있습니다."),
    ("히나", "선도부", "심상치 않은 사건?"),
    ("아코", "선도부", "네. 타 학원 학생이 다른 학원에 나타나 소란을 일으키는 사건입니다."),
    ("히나", "선도부", "..."),
    ("아코", "선도부", "트리니티 학생이 밀레니엄에서 난동을 부리거나, 밀레니엄 학생이 붉은겨울에서 문제를 일으키는 식입니다."),
    ("히나", "선도부", "우연은 아닌 것 같군."),
    ("아코", "선도부", "저도 그렇게 판단하고 있습니다."),
    ("아코", "선도부", "이미 여러 학원에서 항의와 문의가 들어오고 있는 상황입니다."),
    ("히나", "선도부", "피해는?"),
    ("아코", "선도부", "다행히 중상자는 없습니다만, 학원 간 갈등이 심화되고 있습니다."),
    ("히나", "선도부", "원인은 밝혀졌나?"),
    ("아코", "선도부", "아직입니다."),
    ("아코", "선도부", "특이한 점은 사건 당사자들이 모두 사건 직전의 기억을 잃어버렸다는 것입니다."),
    ("히나", "선도부", "기억을?"),
    ("아코", "선도부", "네. 왜 그 장소에 있었는지조차 설명하지 못하고 있습니다."),
    ("히나", "선도부", "...수상하군."),
    ("아코", "선도부", "선도부 인원들을 투입해 조사했지만 별다른 성과는 없었습니다."),
    ("히나", "선도부", "그래서 내가 필요한 건가."),
    ("아코", "선도부", "예."),
    ("아코", "선도부", "이 정도 규모의 사건을 맡길 수 있는 사람은 선도부장님뿐입니다."),
    ("히나", "선도부", "...하아."),
    ("아코", "선도부", "죄송합니다."),
    ("히나", "선도부", "됐어. 자료는?"),
    ("아코", "선도부", "이미 준비해 두었습니다."),
    ("아코", "선도부", "최근 일주일 동안 보고된 사건들을 정리한 문서입니다."),
    ("히나", "선도부", "...많군."),
    ("아코", "선도부", "생각보다 상황이 심각합니다."),
    ("히나", "선도부", "알겠다."),
    ("히나", "선도부", "문제 학생들을 처리하러 간다."),
    ("아코", "선도부", "예, 조심히 다녀오십시오.")
]

MISSION_HINA_ROOM = "제복을 갈아입기."
MISSION_SLEEP     = "침대에 눕기."
MISSION_PREFECT   = "아코에게 말을 걸기."

# ─────────────────────────────────────────────
# 오프닝 나레이션 시스템
# ─────────────────────────────────────────────
class OpeningNarration:
    CHAR_INTERVAL = 40

    def __init__(self, lines):
        self.lines      = lines
        self.line_idx   = 0
        self.char_idx   = 0
        self.last_char  = 0
        self.finished   = False

    @property
    def _cur(self):
        return self.lines[self.line_idx]

    @property
    def _typing_done(self):
        return self.char_idx >= len(self._cur)

    def update(self, current_time):
        if self.finished or self._typing_done:
            return
        if current_time - self.last_char >= self.CHAR_INTERVAL:
            self.char_idx += 1
            self.last_char = current_time

    def on_space(self):
        if not self._typing_done:
            self.char_idx = len(self._cur)
        else:
            self.line_idx += 1
            if self.line_idx >= len(self.lines):
                self.finished = True
            else:
                self.char_idx  = 0
                self.last_char = 0

    def draw(self, surface, current_time):
        if self.finished:
            return
        surface.fill((0, 0, 0))
        text = self._cur[:self.char_idx]
        surf = font_narr.render(text, True, (220, 215, 200))
        surface.blit(surf, surf.get_rect(center=(WIDTH // 2, HEIGHT // 2)))

        if self._typing_done:
            bounce = int(math.sin(current_time / 300) * 3)
            btn_w, btn_h = 84, 30
            btn_x = WIDTH  - btn_w - 18
            btn_y = HEIGHT - btn_h - 14 - bounce

            btn_surf = pygame.Surface((btn_w, btn_h), pygame.SRCALPHA)
            btn_surf.fill((255, 255, 255, 22))
            pygame.draw.rect(btn_surf, (200, 215, 240, 180),
                             (0, 0, btn_w, btn_h), 2, border_radius=4)
            surface.blit(btn_surf, (btn_x, btn_y))

            sp_surf = font_dlg_space.render("Space", True, (210, 225, 250))
            surface.blit(sp_surf, sp_surf.get_rect(center=(btn_x + btn_w // 2,
                                                            btn_y + btn_h // 2 - 1)))
            ax = btn_x + btn_w // 2
            ay = btn_y + btn_h + 3 - bounce
            pygame.draw.polygon(surface, (170, 195, 230),
                                 [(ax - 7, ay), (ax + 7, ay), (ax, ay + 7)])


# ─────────────────────────────────────────────
# 대화창 시스템
# ─────────────────────────────────────────────
class DialogSystem:
    CHAR_INTERVAL  = 38

    def __init__(self, lines):
        self.lines    = lines
        self.idx      = 0
        self.char_idx = 0
        self.last_char = 0
        self.finished  = False

    @property
    def _cur(self):
        return self.lines[self.idx]

    @property
    def _typing_done(self):
        return self.char_idx >= len(self._cur[2])

    def update(self, current_time):
        if self.finished or self._typing_done:
            return
        if current_time - self.last_char >= self.CHAR_INTERVAL:
            self.char_idx += 1
            self.last_char = current_time

    def on_space(self):
        if not self._typing_done:
            self.char_idx = len(self._cur[2])
        else:
            self.idx += 1
            if self.idx >= len(self.lines):
                self.finished = True
            else:
                self.char_idx  = 0
                self.last_char = 0

    def draw(self, surface, current_time):
        if self.finished:
            return
        name, affil, text = self._cur

        PANEL_H    = 170
        PAD_X      = 28
        PAD_Y      = 18
        NAME_H     = 52

        panel_y = HEIGHT - PANEL_H
        panel_w = WIDTH

        panel_surf = pygame.Surface((panel_w, PANEL_H), pygame.SRCALPHA)
        panel_surf.fill((6, 12, 24, 228))
        surface.blit(panel_surf, (0, panel_y))

        if name:
            name_surf = font_dlg_name.render(name, True, (240, 245, 255))
        else:
            name_surf = font_dlg_name.render("", True, (240, 245, 255))

        if affil:
            affil_surf = font_dlg_affil.render(affil, True, (94, 196, 255))
        else:
            affil_surf = None

        name_x = PAD_X
        name_y = panel_y + (NAME_H - name_surf.get_height()) // 2
        if name:
            surface.blit(name_surf, (name_x, name_y))
        if affil_surf:
            affil_x = name_x + name_surf.get_width() + 12
            affil_y = name_y + name_surf.get_height() - affil_surf.get_height() - 2
            surface.blit(affil_surf, (affil_x, affil_y))

        line_y = panel_y + NAME_H
        pygame.draw.line(surface, (255, 255, 255, 60),
                         (0, line_y), (panel_w, line_y), 1)

        text_top = line_y + PAD_Y

        display_text = text[:self.char_idx]
        max_w = panel_w - PAD_X * 2
        self._draw_wrapped(surface, display_text, font_dlg_text,
                           (230, 236, 248), PAD_X, text_top, max_w)

        if not self._typing_done and (current_time // 500) % 2 == 0:
            wrapped = self._wrap_lines(display_text, font_dlg_text, max_w)
            last_line_w = font_dlg_text.size(wrapped[-1])[0]
            cur_x = PAD_X + last_line_w + 2
            cur_y = text_top + (len(wrapped) - 1) * font_dlg_text.get_linesize() + 3
            pygame.draw.rect(surface, (94, 196, 255),
                             pygame.Rect(cur_x, cur_y, 2, font_dlg_text.get_height() - 5))

        if self._typing_done:
            bounce = int(math.sin(current_time / 300) * 3)

            btn_w, btn_h = 84, 30
            btn_x = WIDTH  - btn_w - 18
            btn_y = HEIGHT - btn_h - 14 - bounce

            btn_surf = pygame.Surface((btn_w, btn_h), pygame.SRCALPHA)
            btn_surf.fill((255, 255, 255, 22))
            pygame.draw.rect(btn_surf, (200, 215, 240, 180),
                             (0, 0, btn_w, btn_h), 2, border_radius=4)
            surface.blit(btn_surf, (btn_x, btn_y))

            sp_surf = font_dlg_space.render("Space", True, (210, 225, 250))
            surface.blit(sp_surf, sp_surf.get_rect(center=(btn_x + btn_w // 2,
                                                            btn_y + btn_h // 2 - 1)))

            ax = btn_x + btn_w // 2
            ay = btn_y + btn_h + 3 - bounce
            pygame.draw.polygon(surface, (170, 195, 230),
                                 [(ax - 7, ay), (ax + 7, ay), (ax, ay + 7)])

    @staticmethod
    def _wrap_lines(text, font, max_w):
        lines = []
        for paragraph in text.split('\n'):
            if not paragraph:
                lines.append('')
                continue
            words = list(paragraph)
            cur = ''
            for ch in words:
                test = cur + ch
                if font.size(test)[0] > max_w:
                    lines.append(cur)
                    cur = ch
                else:
                    cur = test
            lines.append(cur)
        return lines if lines else ['']

    def _draw_wrapped(self, surface, text, font, color, x, y, max_w):
        lines = self._wrap_lines(text, font, max_w)
        ls = font.get_linesize()
        for i, line in enumerate(lines):
            surf = font.render(line, True, color)
            surface.blit(surf, (x, y + i * ls))


# ─────────────────────────────────────────────
# 10. 타이틀 화면
# ─────────────────────────────────────────────
def draw_title_screen(surface, tick):
    surface.fill((10, 10, 15))
    if title_img:
        surface.blit(title_img, title_img.get_rect(center=(WIDTH//2, HEIGHT//2)))
        ov = pygame.Surface((WIDTH, HEIGHT), pygame.SRCALPHA)
        ov.fill((0, 0, 0, 120))
        surface.blit(ov, (0, 0))
    else:
        for gx in range(0, WIDTH, 60):
            pygame.draw.line(surface, (20,20,30), (gx,0), (gx,HEIGHT))
        for gy in range(0, HEIGHT, 60):
            pygame.draw.line(surface, (20,20,30), (0,gy), (WIDTH,gy))
    if (tick // 500) % 2 == 0:
        prompt = font_medium.render("PRESS  SPACE  TO  START", True, (220,220,60))
        surface.blit(prompt, prompt.get_rect(center=(WIDTH//2, HEIGHT-80)))

# ─────────────────────────────────────────────
# 미션 UI
# ─────────────────────────────────────────────
font_mission = _make_font(14)

def draw_mission(surface, text):
    pad = 8
    surf = font_mission.render(f"▶  {text}", True, (210, 220, 255))
    bg = pygame.Surface((surf.get_width() + pad * 2, surf.get_height() + pad), pygame.SRCALPHA)
    bg.fill((10, 15, 30, 180))
    surface.blit(bg, (12, 12))
    surface.blit(surf, (12 + pad, 12 + pad // 2))

# ─────────────────────────────────────────────
# 상호작용 프롬프트
# ─────────────────────────────────────────────
font_interact = _make_font(16, bold=True)

def draw_interact_prompt(surface, text, cx, cy):
    pad_x, pad_y = 10, 6
    surf = font_interact.render(text, True, (255, 240, 120))
    bw = surf.get_width() + pad_x * 2
    bh = surf.get_height() + pad_y * 2
    bg = pygame.Surface((bw, bh), pygame.SRCALPHA)
    bg.fill((0, 0, 0, 170))
    pygame.draw.rect(bg, (255, 230, 80, 160), (0, 0, bw, bh), 1, border_radius=4)
    bx = cx - bw // 2
    by = cy - bh - 14
    surface.blit(bg, (bx, by))
    surface.blit(surf, (bx + pad_x, by + pad_y))

# ─────────────────────────────────────────────
# 페이드 아웃 헬퍼
# ─────────────────────────────────────────────
def draw_fadeout(surface, alpha):
    ov = pygame.Surface((WIDTH, HEIGHT))
    ov.fill((0, 0, 0))
    ov.set_alpha(int(alpha))
    surface.blit(ov, (0, 0))

# ─────────────────────────────────────────────
# 히나 방 씬
# ─────────────────────────────────────────────
def draw_hina_room(surface, player, current_time,
                   near_wardrobe=False, near_bed=False, mission=None):
    surface.fill((0, 0, 0))
    if hina_room_img:
        surface.blit(hina_room_img, hina_room_rect)
    else:
        rs = min(WIDTH, HEIGHT)
        rx, ry = (WIDTH-rs)//2, (HEIGHT-rs)//2
        pygame.draw.rect(surface, (50,45,55), (rx, ry, rs, rs))
        pygame.draw.rect(surface, (80,75,85), (rx, ry, rs, rs), 4)
    player.draw(surface, int(player.hina_sx), int(player.hina_sy), current_time)

    if near_wardrobe:
        draw_interact_prompt(surface, "갈아입기  [E]", WARDROBE_POS[0], WARDROBE_POS[1])
    if near_bed:
        draw_interact_prompt(surface, "잠에 들기  [E]", BED_POS[0], BED_POS[1])

    if mission:
        draw_mission(surface, mission)

    if len(_HINA_WALK_POLY) >= 2:
        pygame.draw.polygon(surface, (255, 0, 0), _HINA_WALK_POLY, 2)
        for pt in _HINA_WALK_POLY:
            pygame.draw.circle(surface, (255, 255, 0), pt, 5)

# ─────────────────────────────────────────────
# 선도부실 씬
# ─────────────────────────────────────────────
def draw_prefect_room(surface, player, current_time,
                      near_aco=False, mission=None):
    surface.fill((0, 0, 0))
    if prefect_room_img:
        surface.blit(prefect_room_img, prefect_room_rect)
    else:
        rs = min(WIDTH, HEIGHT)
        rx, ry = (WIDTH-rs)//2, (HEIGHT-rs)//2
        pygame.draw.rect(surface, (30, 35, 45), (rx, ry, rs, rs))
        pygame.draw.rect(surface, (60, 65, 80), (rx, ry, rs, rs), 4)
        lbl = font_mission.render("선도부실", True, (180, 180, 200))
        surface.blit(lbl, lbl.get_rect(center=(WIDTH//2, HEIGHT//2)))

    # ── aco 캐릭터 그리기 ──
    if aco_img:
        ax = ACO_SCREEN_POS[0] - ACO_DRAW_W // 2
        ay = ACO_SCREEN_POS[1] - ACO_DRAW_H // 2
        surface.blit(aco_img, (ax, ay))
    else:
        # 폴백: 보라색 원 + "ACO" 텍스트
        pygame.draw.circle(surface, (180, 120, 220), ACO_SCREEN_POS, 28)
        lbl = font_mini.render("ACO", True, (255, 255, 255))
        surface.blit(lbl, lbl.get_rect(center=ACO_SCREEN_POS))

    if near_aco:
        draw_interact_prompt(surface, "말 걸기  [E]",
                             ACO_SCREEN_POS[0], ACO_SCREEN_POS[1])

    player.draw(surface, int(player.hina_sx), int(player.hina_sy), current_time)

    if mission:
        draw_mission(surface, mission)

    if len(_PREFECT_WALK_POLY) >= 2:
        pygame.draw.polygon(surface, (0, 200, 255), _PREFECT_WALK_POLY, 2)
        for pt in _PREFECT_WALK_POLY:
            pygame.draw.circle(surface, (0, 255, 200), pt, 5)
    mx, my = pygame.mouse.get_pos()
    dbg = font_mini.render(f"mouse: ({mx}, {my})", True, (255, 255, 0))
    surface.blit(dbg, (10, 40))

# ─────────────────────────────────────────────
# 11. 메인 루프
# ─────────────────────────────────────────────
game_state           = "title"
running              = True
hina_bgm_started     = False
battle_bgm_started   = False
piano_e_pressed_prev = False

opening  = OpeningNarration(OPENING_LINES)
hina_dlg = DialogSystem(HINA_ROOM_DIALOG)

mid_dlg: DialogSystem | None = None
aco_dlg: DialogSystem | None = None
aco_talked   = False
bed_used     = False

fadeout_start    = 0
FADEOUT_DURATION = 1200

# ★ FIX 3: 아코 대화 완료 후 전투맵 전환용 페이드
prefect_fadeout_start    = 0
PREFECT_FADEOUT_DURATION = 1200

e_prev = False

# ─────────────────────────────────────────────
# F10 디버그 메뉴
# ─────────────────────────────────────────────
DEBUG_STAGES = [
    ("1. 타이틀",          "title"),
    ("2. 오프닝 나레이션",  "intro"),
    ("3. 히나 방 대화",    "hina_dialog"),
    ("4. 히나 방 (자유)",  "hina_room"),
    ("5. 선도부실",        "prefect_room"),
    ("6. 전투 맵",         "battle"),
]
debug_menu_open  = False
debug_cursor     = 0
font_debug       = _make_font(18, bold=True)
font_debug_title = _make_font(22, bold=True)

def _jump_to_stage(target_state):
    global game_state, hina_bgm_started, battle_bgm_started
    global bed_used, aco_talked, mid_dlg, aco_dlg
    global fadeout_start, prefect_fadeout_start

    game_state = target_state

    if target_state == "title":
        pygame.mixer.music.stop()
        hina_bgm_started   = False
        battle_bgm_started = False

    elif target_state == "intro":
        pygame.mixer.music.stop()
        hina_bgm_started   = False
        battle_bgm_started = False
        opening.line_idx  = 0
        opening.char_idx  = 0
        opening.last_char = 0
        opening.finished  = False

    elif target_state == "hina_dialog":
        if not hina_bgm_started:
            play_bgm(0)
            hina_bgm_started = True
        hina_dlg.idx       = 0
        hina_dlg.char_idx  = 0
        hina_dlg.last_char = 0
        hina_dlg.finished  = False

    elif target_state == "hina_room":
        if not hina_bgm_started:
            play_bgm(0)
            hina_bgm_started = True
        player.hina_sx = 500.0
        player.hina_sy = 560.0
        player.costume = "uniform"
        bed_used = False
        mid_dlg  = None

    elif target_state == "prefect_room":
        play_funky_road()
        player.hina_sx = 500.0
        player.hina_sy = 560.0
        player.costume = "uniform"
        aco_talked = False
        aco_dlg    = None

    elif target_state == "battle":
        if not battle_bgm_started:
            play_bgm(1)
            battle_bgm_started = True
        player.world_x = BATTLE_START_X
        player.world_y = BATTLE_START_Y
        player.costume = "uniform"

def _draw_debug_menu(surface, cursor):
    ov = pygame.Surface((WIDTH, HEIGHT), pygame.SRCALPHA)
    ov.fill((0, 0, 0, 190))
    surface.blit(ov, (0, 0))

    panel_w = 380
    panel_h = 60 + len(DEBUG_STAGES) * 44 + 20
    px = WIDTH  // 2 - panel_w // 2
    py = HEIGHT // 2 - panel_h // 2

    panel = pygame.Surface((panel_w, panel_h), pygame.SRCALPHA)
    panel.fill((12, 18, 35, 240))
    pygame.draw.rect(panel, (80, 120, 200, 200), (0, 0, panel_w, panel_h), 2, border_radius=8)
    surface.blit(panel, (px, py))

    title_s = font_debug_title.render("[ DEBUG  —  STAGE SELECT ]", True, (130, 180, 255))
    surface.blit(title_s, title_s.get_rect(centerx=px + panel_w // 2, top=py + 14))

    for i, (label, _) in enumerate(DEBUG_STAGES):
        item_y = py + 52 + i * 44
        is_sel = (i == cursor)
        if is_sel:
            sel_rect = pygame.Rect(px + 10, item_y - 4, panel_w - 20, 36)
            pygame.draw.rect(surface, (50, 90, 200, 180), sel_rect, border_radius=5)
            pygame.draw.rect(surface, (100, 160, 255, 220), sel_rect, 1, border_radius=5)
        color  = (255, 240, 100) if is_sel else (190, 200, 220)
        prefix = "▶  " if is_sel else "    "
        txt = font_debug.render(prefix + label, True, color)
        surface.blit(txt, (px + 22, item_y))

    hint = font_debug.render("↑↓ 이동   Enter 선택   F10 닫기", True, (100, 120, 160))
    surface.blit(hint, hint.get_rect(centerx=px + panel_w // 2, top=py + panel_h - 26))

while running:
    current_time = pygame.time.get_ticks()

    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running = False
        if event.type == pygame.KEYDOWN:
            if event.key == pygame.K_ESCAPE:
                if debug_menu_open:
                    debug_menu_open = False
                else:
                    running = False

            # ── F10: 디버그 메뉴 토글 ──
            if event.key == pygame.K_F10:
                debug_menu_open = not debug_menu_open
                debug_cursor    = 0

            # ── 디버그 메뉴가 열려 있으면 다른 키 입력 가로챔 ──
            if debug_menu_open:
                if event.key == pygame.K_UP:
                    debug_cursor = (debug_cursor - 1) % len(DEBUG_STAGES)
                elif event.key == pygame.K_DOWN:
                    debug_cursor = (debug_cursor + 1) % len(DEBUG_STAGES)
                elif event.key in (pygame.K_RETURN, pygame.K_KP_ENTER):
                    _jump_to_stage(DEBUG_STAGES[debug_cursor][1])
                    debug_menu_open = False
                # 메뉴 열린 동안 Space 등 다른 입력은 아래로 흘러가지 않도록 continue
                continue

            if event.key == pygame.K_SPACE and game_state == "title":
                game_state = "intro"

            elif event.key == pygame.K_SPACE and game_state == "intro":
                opening.on_space()
                if opening.finished:
                    game_state = "hina_dialog"
                    if not hina_bgm_started:
                        play_bgm(0)
                        hina_bgm_started = True

            elif event.key == pygame.K_SPACE and game_state == "hina_dialog":
                hina_dlg.on_space()
                if hina_dlg.finished:
                    game_state = "hina_room"
                    player.hina_sx = 500.0
                    player.hina_sy = 560.0

            elif event.key == pygame.K_SPACE and game_state == "hina_mid_dlg":
                if mid_dlg:
                    mid_dlg.on_space()
                    if mid_dlg.finished:
                        if mid_dlg.lines is BED_SLEEP_DIALOG:
                            bed_used      = True
                            game_state    = "fadeout"
                            fadeout_start = current_time
                        else:
                            game_state = "hina_room"
                            mid_dlg    = None

            elif event.key == pygame.K_SPACE and game_state == "prefect_aco_dlg":
                if aco_dlg:
                    aco_dlg.on_space()
                    if aco_dlg.finished:
                        # ★ FIX 3: 대화 완료 → 페이드 아웃 후 전투맵으로
                        aco_talked              = True
                        game_state              = "prefect_fadeout"
                        prefect_fadeout_start   = current_time
                        aco_dlg                 = None

    # ── 타이틀 ──
    if game_state == "title":
        draw_title_screen(screen, current_time)
        if debug_menu_open:
            _draw_debug_menu(screen, debug_cursor)
        pygame.display.flip()
        clock.tick(60)
        continue

    # ── 오프닝 나레이션 ──
    if game_state == "intro":
        opening.update(current_time)
        opening.draw(screen, current_time)
        if debug_menu_open:
            _draw_debug_menu(screen, debug_cursor)
        pygame.display.flip()
        clock.tick(60)
        continue

    # ── 히나 방 입장 대화 ──
    if game_state == "hina_dialog":
        hina_dlg.update(current_time)
        screen.fill((0, 0, 0))
        if hina_room_img:
            screen.blit(hina_room_img, hina_room_rect)
        hina_dlg.draw(screen, current_time)
        if debug_menu_open:
            _draw_debug_menu(screen, debug_cursor)
        pygame.display.flip()
        clock.tick(60)
        continue

    # ── 히나 방 자유 이동 ──
    if game_state == "hina_room":
        keys = pygame.key.get_pressed()
        player.update_hina_room(keys, current_time)
        e_now = keys[pygame.K_e]

        dist_wardrobe = math.hypot(player.hina_sx - WARDROBE_POS[0],
                                   player.hina_sy - WARDROBE_POS[1])
        dist_bed      = math.hypot(player.hina_sx - BED_POS[0],
                                   player.hina_sy - BED_POS[1])

        # 옷장: 제복 상태일 때만
        near_wardrobe = (dist_wardrobe < WARDROBE_RADIUS) and (player.costume == "uniform")

        # ★ FIX 2: 침대는 항상 가까이 가면 반응 (bed_used 아직 안 됐을 때)
        # 제복 상태 → BED_UNIFORM_DIALOG, 수면복 상태 → BED_SLEEP_DIALOG
        near_bed = (dist_bed < BED_RADIUS) and not bed_used

        # 미션 결정
        if player.costume == "uniform":
            mission_txt = MISSION_HINA_ROOM
        elif not bed_used:
            mission_txt = MISSION_SLEEP
        else:
            mission_txt = None

        if e_now and not e_prev:
            if near_wardrobe:
                player.costume = "sleep"
            elif near_bed:
                if player.costume == "uniform":
                    mid_dlg    = DialogSystem(BED_UNIFORM_DIALOG)
                    game_state = "hina_mid_dlg"
                else:
                    mid_dlg    = DialogSystem(BED_SLEEP_DIALOG)
                    game_state = "hina_mid_dlg"

        e_prev = e_now

        draw_hina_room(screen, player, current_time,
                       near_wardrobe=near_wardrobe,
                       near_bed=near_bed,
                       mission=mission_txt)
        mx, my = pygame.mouse.get_pos()
        dbg = font_mini.render(f"mouse: ({mx}, {my})", True, (255, 255, 0))
        screen.blit(dbg, (10, 40))

        if debug_menu_open:
            _draw_debug_menu(screen, debug_cursor)
        pygame.display.flip()
        clock.tick(60)
        continue

    # ── 히나 방 중간 대화 ──
    if game_state == "hina_mid_dlg":
        if mid_dlg:
            mid_dlg.update(current_time)
        screen.fill((0, 0, 0))
        if hina_room_img:
            screen.blit(hina_room_img, hina_room_rect)
        player.draw(screen, int(player.hina_sx), int(player.hina_sy), current_time)
        if mid_dlg:
            mid_dlg.draw(screen, current_time)
        if debug_menu_open:
            _draw_debug_menu(screen, debug_cursor)
        pygame.display.flip()
        clock.tick(60)
        continue

    # ── 히나 방 → 선도부실 페이드 아웃 ──
    if game_state == "fadeout":
        elapsed = current_time - fadeout_start
        alpha   = min(255, int(255 * elapsed / FADEOUT_DURATION))
        screen.fill((0, 0, 0))
        if hina_room_img:
            screen.blit(hina_room_img, hina_room_rect)
        player.draw(screen, int(player.hina_sx), int(player.hina_sy), current_time)
        draw_fadeout(screen, alpha)
        if elapsed >= FADEOUT_DURATION:
            game_state = "prefect_room"
            player.hina_sx  = 500.0
            player.hina_sy  = 560.0
            player.costume  = "uniform"
            play_funky_road()
        if debug_menu_open:
            _draw_debug_menu(screen, debug_cursor)
        pygame.display.flip()
        clock.tick(60)
        continue

    # ── 선도부실 ──
    if game_state == "prefect_room":
        keys = pygame.key.get_pressed()
        player.update_prefect_room(keys, current_time)
        e_now = keys[pygame.K_e]

        dist_aco = math.hypot(player.hina_sx - ACO_SCREEN_POS[0],
                              player.hina_sy - ACO_SCREEN_POS[1])
        near_aco = dist_aco < ACO_INTERACT_RADIUS and not aco_talked

        if e_now and not e_prev and near_aco:
            aco_dlg    = DialogSystem(ACO_DIALOG)
            game_state = "prefect_aco_dlg"

        e_prev = e_now

        mission_txt = None if aco_talked else MISSION_PREFECT

        draw_prefect_room(screen, player, current_time,
                          near_aco=near_aco,
                          mission=mission_txt)
        if debug_menu_open:
            _draw_debug_menu(screen, debug_cursor)
        pygame.display.flip()
        clock.tick(60)
        continue

    # ── 선도부실 아코 대화 ──
    if game_state == "prefect_aco_dlg":
        if aco_dlg:
            aco_dlg.update(current_time)
        screen.fill((0, 0, 0))
        if prefect_room_img:
            screen.blit(prefect_room_img, prefect_room_rect)
        if aco_img:
            ax = ACO_SCREEN_POS[0] - ACO_DRAW_W // 2
            ay = ACO_SCREEN_POS[1] - ACO_DRAW_H // 2
            screen.blit(aco_img, (ax, ay))
        else:
            pygame.draw.circle(screen, (180, 120, 220), ACO_SCREEN_POS, 28)
        player.draw(screen, int(player.hina_sx), int(player.hina_sy), current_time)
        if aco_dlg:
            aco_dlg.draw(screen, current_time)
        if debug_menu_open:
            _draw_debug_menu(screen, debug_cursor)
        pygame.display.flip()
        clock.tick(60)
        continue

    # ★ FIX 3: 선도부실 → 전투맵 페이드 아웃
    if game_state == "prefect_fadeout":
        elapsed = current_time - prefect_fadeout_start
        alpha   = min(255, int(255 * elapsed / PREFECT_FADEOUT_DURATION))
        screen.fill((0, 0, 0))
        if prefect_room_img:
            screen.blit(prefect_room_img, prefect_room_rect)
        if aco_img:
            ax = ACO_SCREEN_POS[0] - ACO_DRAW_W // 2
            ay = ACO_SCREEN_POS[1] - ACO_DRAW_H // 2
            screen.blit(aco_img, (ax, ay))
        player.draw(screen, int(player.hina_sx), int(player.hina_sy), current_time)
        draw_fadeout(screen, alpha)
        if elapsed >= PREFECT_FADEOUT_DURATION:
            # 전투맵으로 전환 — 플레이어 월드 좌표를 방 1 중앙으로 초기화
            game_state = "battle"
            player.world_x = BATTLE_START_X
            player.world_y = BATTLE_START_Y
            player.costume = "uniform"
            play_bgm(1)
            battle_bgm_started = True
        if debug_menu_open:
            _draw_debug_menu(screen, debug_cursor)
        pygame.display.flip()
        clock.tick(60)
        continue

    # ── 전투 맵 ──
    if game_state != "battle":
        # 혹시 모를 미정의 상태면 battle로 강제 이동
        game_state = "battle"

    if not battle_bgm_started:
        play_bgm(1)
        battle_bgm_started = True

    keys = pygame.key.get_pressed()
    player.update(keys, enemies, current_time, bullets)

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

    # ── 전투맵: 카메라가 플레이어 중심 추적 ──
    # 카메라: 플레이어를 화면 중앙에 두되, 맵 경계에서 클램프
    cam_x = int(player.world_x) - WIDTH  // 2
    cam_y = int(player.world_y) - HEIGHT // 2
    cam_x = max(0, min(cam_x, BATTLE_MAP_W - WIDTH))
    cam_y = max(0, min(cam_y, BATTLE_MAP_H - HEIGHT))

    screen.fill(BG_COLOR)

    # 배경 이미지 (카메라 오프셋 적용)
    if battle_bg_img:
        screen.blit(battle_bg_img, (-cam_x, -cam_y))

    # 디버그: 워크존 폴리곤 표시 (카메라 오프셋 적용, 초록)
    if debug_menu_open is False:
        for poly in _BATTLE_WALK_POLYS:
            sp = [(x - cam_x, y - cam_y) for x, y in poly]
            pygame.draw.polygon(screen, (0, 220, 80), sp, 2)
            for pt in sp:
                pygame.draw.circle(screen, (0, 255, 100), pt, 4)
        for rect in _BATTLE_CORRIDOR_RECTS:
            sr = pygame.Rect(rect.x - cam_x, rect.y - cam_y, rect.width, rect.height)
            pygame.draw.rect(screen, (80, 180, 255), sr, 2)

    # 적 (카메라 오프셋)
    for enemy in enemies:
        ex = int(enemy.world_x) - cam_x
        ey = int(enemy.world_y) - cam_y
        er = enemy.radius
        pygame.draw.circle(screen, ENEMY_COLOR, (ex, ey), er)
        eo = int(6*SCALE); er1 = int(5*SCALE); er2 = int(3*SCALE); ey2 = int(5*SCALE)
        pygame.draw.circle(screen, (255,255,255), (ex-eo, ey-ey2), er1)
        pygame.draw.circle(screen, (255,255,255), (ex+eo, ey-ey2), er1)
        pygame.draw.circle(screen, (0,0,0),       (ex-eo+1, ey-ey2), er2)
        pygame.draw.circle(screen, (0,0,0),       (ex+eo+1, ey-ey2), er2)

    # 총알 (카메라 오프셋)
    for bullet in bullets:
        pygame.draw.circle(screen, BULLET_COLOR,
                           (int(bullet.world_x) - cam_x, int(bullet.world_y) - cam_y),
                           bullet.radius)

    # 플레이어 (항상 화면 중앙, 단 맵 경계에서는 카메라 클램프로 치우침)
    px_screen = int(player.world_x) - cam_x
    py_screen = int(player.world_y) - cam_y
    player.draw(screen, px_screen, py_screen, current_time)

    # 마우스 → 월드 좌표 표시 (워크존 조정용)
    mx, my = pygame.mouse.get_pos()
    wx, wy = mx + cam_x, my + cam_y
    dbg = font_mini.render(f"world: ({wx}, {wy})  screen: ({mx}, {my})", True, (255, 255, 0))
    screen.blit(dbg, (10, HEIGHT - 22))

    if debug_menu_open:
        _draw_debug_menu(screen, debug_cursor)
    pygame.display.flip()
    clock.tick(60)

pygame.quit()
sys.exit()