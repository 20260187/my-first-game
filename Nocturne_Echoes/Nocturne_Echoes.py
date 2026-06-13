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

# ── 히나 방 이미지 ──
hina_room_img  = None
hina_room_rect = None
hina_room_path = os.path.join(ASSETS_DIR, "hina_room.png")
if os.path.exists(hina_room_path):
    _raw_room  = pygame.image.load(hina_room_path).convert()
    _room_size = min(HEIGHT, WIDTH)
    hina_room_img  = pygame.transform.scale(_raw_room, (_room_size, _room_size))
    hina_room_rect = hina_room_img.get_rect(center=(WIDTH // 2, HEIGHT // 2))

# ── 선도부실 이미지 ──
prefect_room_img  = None
prefect_room_rect = None
prefect_room_path = os.path.join(ASSETS_DIR, "prefect_room.png")
if os.path.exists(prefect_room_path):
    _raw_pr = pygame.image.load(prefect_room_path).convert()
    _room_size_pr = min(HEIGHT, WIDTH)
    prefect_room_img  = pygame.transform.scale(_raw_pr, (_room_size_pr, _room_size_pr))
    prefect_room_rect = prefect_room_img.get_rect(center=(WIDTH // 2, HEIGHT // 2))

# ── 피아노 방 이미지 ──
piano_room_img  = None
piano_room_rect = None
piano_room_path = os.path.join(ASSETS_DIR, "piano_room.png")
if os.path.exists(piano_room_path):
    try:
        _raw_pr2 = pygame.image.load(piano_room_path).convert()
        _room_size_pr2 = min(HEIGHT, WIDTH)
        piano_room_img  = pygame.transform.scale(_raw_pr2, (_room_size_pr2, _room_size_pr2))
        piano_room_rect = piano_room_img.get_rect(center=(WIDTH // 2, HEIGHT // 2))
    except Exception as e:
        print(f"[WARN] piano_room.png 로드 실패: {e}")

# ── ml_room 이미지 (게헨나처럼 크게 — 스크롤 맵 사이즈) ──
ML_MAP_W = 2200
ML_MAP_H = 1540
ml_room_img  = None
ml_room_path = os.path.join(ASSETS_DIR, "ml_room.png")
if os.path.exists(ml_room_path):
    try:
        _raw_ml     = pygame.image.load(ml_room_path).convert()
        ml_room_img = pygame.transform.scale(_raw_ml, (ML_MAP_W, ML_MAP_H))
    except Exception as e:
        print(f"[WARN] ml_room.png 로드 실패: {e}")

# ── mon 이미지 ──
mon_img     = None
mon_map_img = None
mon_room_img = None  # 히나 방 안에서 표시용 (플레이어 크기와 비슷)
mon_img_path = os.path.join(ASSETS_DIR, "mon.png")
if os.path.exists(mon_img_path):
    try:
        _mon_raw = pygame.image.load(mon_img_path).convert_alpha()

        # 오른쪽 모서리 표시용 (기존, 약 30% 크기) — 이제는 사용 안 함
        mon_corner_w = int(WIDTH * 0.30)
        mon_corner_h = int(mon_corner_w * _mon_raw.get_height() / _mon_raw.get_width())
        mon_img = pygame.transform.scale(_mon_raw, (mon_corner_w, mon_corner_h))

        # 맵 중간 표시용
        mon_map_w = int(110 * SCALE)
        mon_map_h = int(mon_map_w * _mon_raw.get_height() / _mon_raw.get_width())
        mon_map_img = pygame.transform.scale(_mon_raw, (mon_map_w, mon_map_h))

        # 히나 방 안 표시용: 플레이어(PLAYER_DRAW_SIZE=~77px)와 비슷한 크기
        _PLAYER_DRAW_SIZE = int(64 * SCALE)  # forward ref 대비
        mon_room_w = int(_PLAYER_DRAW_SIZE * 1.1)
        mon_room_h = int(mon_room_w * _mon_raw.get_height() / _mon_raw.get_width())
        mon_room_img = pygame.transform.scale(_mon_raw, (mon_room_w, mon_room_h))

    except Exception as e:
        print(f"[WARN] mon.png 로드 실패: {e}")

# ── aco 캐릭터 이미지 ──
_AKO_ORIG_W, _AKO_ORIG_H = 190, 250
_AKO_TARGET_H = int(80 * SCALE)
_AKO_TARGET_W = int(_AKO_TARGET_H * _AKO_ORIG_W / _AKO_ORIG_H)
ACO_DRAW_W = _AKO_TARGET_W
ACO_DRAW_H = _AKO_TARGET_H
ACO_DRAW_SIZE = max(ACO_DRAW_W, ACO_DRAW_H)

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

ACO_SCREEN_POS      = (430, 400)
ACO_INTERACT_RADIUS = 100

WARDROBE_POS    = (770, 460)
WARDROBE_RADIUS = 80
BED_POS    = (340, 260)
BED_RADIUS = 80

# ─────────────────────────────────────────────
# ── 적 스프라이트 로드 (en1, en2 — 2프레임 시트) ──
# ─────────────────────────────────────────────
ENEMY_DRAW_W = int(90 * SCALE)
ENEMY_DRAW_H = int(108 * SCALE)
ENEMY_ANIM_INTERVAL = 400

ST_DRAW_W = int(180 * SCALE)
ST_DRAW_H = int(70 * SCALE)

def _load_enemy_sprite(name, frame_count=2):
    path = os.path.join(ASSETS_DIR, f"{name}.png")
    frames = []
    if os.path.exists(path):
        try:
            raw = pygame.image.load(path).convert_alpha()
            raw_w, raw_h = raw.get_size()
            frame_w = raw_w // frame_count
            for i in range(frame_count):
                fr = raw.subsurface(pygame.Rect(i * frame_w, 0, frame_w, raw_h))
                sc = pygame.transform.scale(fr, (ENEMY_DRAW_W, ENEMY_DRAW_H))
                sc.set_colorkey((0, 0, 0))
                frames.append(sc)
        except Exception as e:
            print(f"[WARN] {name}.png 로드 실패: {e}")
    return frames

def _load_st_image(name):
    path = os.path.join(ASSETS_DIR, f"{name}.png")
    if os.path.exists(path):
        try:
            raw = pygame.image.load(path).convert_alpha()
            sc  = pygame.transform.scale(raw, (ST_DRAW_W, ST_DRAW_H))
            sc.set_colorkey((0, 0, 0))
            return sc
        except Exception as e:
            print(f"[WARN] {name}.png 로드 실패: {e}")
    return None

en1_frames = _load_enemy_sprite("en1")
en2_frames = _load_enemy_sprite("en2")
st1_img    = _load_st_image("st1")
st2_img    = _load_st_image("st2")

# ─────────────────────────────────────────────
# 스프라이트
# ─────────────────────────────────────────────
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

BGM_FILES = [
    os.path.join(ASSETS_DIR, "bgm0.opus"),
    os.path.join(ASSETS_DIR, "bgm1.opus"),
]
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

# ─────────────────────────────────────────────
# 워크존
# ─────────────────────────────────────────────
_HINA_WALK_POLY = [
    (240, 580), (240, 320), (370, 320), (370, 250),
    (710, 250), (710, 580),
]

_PREFECT_WALK_POLY = [
    (280, 600), (280, 450), (350, 450), (350, 190),
    (700, 190), (700, 600),
]

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

def _point_in_piano_walkzone(px, py):
    return _point_in_poly(px, py, _PIANO_WALK_POLY)

# ─────────────────────────────────────────────
# 전투 맵 설정
# ─────────────────────────────────────────────
BATTLE_MAP_W = 2500
BATTLE_MAP_H = 1750

battle_bg_img  = None
battle_bg_path = os.path.join(ASSETS_DIR, "gehenna.png")
if os.path.exists(battle_bg_path):
    try:
        _bbg_raw      = pygame.image.load(battle_bg_path).convert()
        battle_bg_img = pygame.transform.scale(_bbg_raw, (BATTLE_MAP_W, BATTLE_MAP_H))
    except Exception as e:
        print(f"[WARN] battle_map 로드 실패: {e}")

_BATTLE_WALK_POLYS = [
    [(775,  70),  (1850, 70),  (1850, 1680), (775,  1680)],
    [(70,   70),  (712,  70),  (712,  655),  (70,   655)],
    [(1892, 70),  (2450, 70),  (2450, 655),  (1892, 655)],
    [(70,   707), (712,  707), (712,  1162), (70,   1162)],
    [(1892, 707), (2450, 707), (2450, 1162), (1892, 1162)],
    [(70,   1217),(712,  1217),(712,  1680), (70,   1680)],
    [(1892, 1217),(2450, 1217),(2450, 1680), (1892, 1680)],
]

_BATTLE_CORRIDOR_RECTS = [
    pygame.Rect(712,  200,  75, 300),
    pygame.Rect(1850, 200,  75, 300),
    pygame.Rect(712,  775,  75, 250),
    pygame.Rect(1850, 775,  75, 250),
    pygame.Rect(712,  1325, 75, 250),
    pygame.Rect(1850, 1325, 75, 250),
]

def _point_in_battle_walkzone(px, py):
    for poly in _BATTLE_WALK_POLYS:
        if _point_in_poly(px, py, poly):
            return True
    for rect in _BATTLE_CORRIDOR_RECTS:
        if rect.collidepoint(int(px), int(py)):
            return True
    return False

BATTLE_START_X = 2175.0
BATTLE_START_Y = 1550.0

# 맵 중앙 (mon 출현 위치)
MON_WORLD_X = BATTLE_MAP_W // 2
MON_WORLD_Y = BATTLE_MAP_H // 2
# 2회차 전투맵에서 mon 접근 반경
MON_INTERACT_RADIUS = int(200 * SCALE)

rooms            = []
id_map           = {}
corridors        = []
mini_connections = []

# ─────────────────────────────────────────────
# 플레이어
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

    def update_piano_room(self, keys, current_time):
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

        if _point_in_piano_walkzone(nx, ny):
            self.hina_sx, self.hina_sy = nx, ny
        else:
            if _point_in_piano_walkzone(nx, self.hina_sy):
                self.hina_sx = nx
            elif _point_in_piano_walkzone(self.hina_sx, ny):
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
            if enemy.is_dead:
                continue
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
# 적 클래스
# ─────────────────────────────────────────────
ENEMY_MAX_HP = 3

class Enemy:
    def __init__(self, x, y, room_id, enemy_type=1):
        self.world_x    = x
        self.world_y    = y
        self.radius     = int(22 * SCALE)
        self.room_id    = room_id
        self.enemy_type = enemy_type

        self.hp         = ENEMY_MAX_HP
        self.is_dead    = False

        self.anim_frame = 0
        self.anim_timer = 0

    def take_hit(self):
        if self.is_dead:
            return
        self.hp -= 1
        if self.hp <= 0:
            self.is_dead = True

    def update_anim(self, current_time):
        if self.is_dead:
            return
        frames = en1_frames if self.enemy_type == 1 else en2_frames
        if len(frames) < 2:
            return
        if current_time - self.anim_timer >= ENEMY_ANIM_INTERVAL:
            self.anim_frame = (self.anim_frame + 1) % len(frames)
            self.anim_timer = current_time

    def draw(self, surface, sx, sy, current_time):
        self.update_anim(current_time)

        if self.is_dead:
            st_img = st1_img if self.enemy_type == 1 else st2_img
            if st_img:
                surface.blit(st_img, st_img.get_rect(center=(sx, sy)))
            else:
                pygame.draw.ellipse(surface, (120, 80, 80),
                                    pygame.Rect(sx - ST_DRAW_W//2, sy - ST_DRAW_H//4,
                                                ST_DRAW_W, ST_DRAW_H//2))
        else:
            frames = en1_frames if self.enemy_type == 1 else en2_frames
            if frames:
                img = frames[self.anim_frame % len(frames)]
                surface.blit(img, img.get_rect(center=(sx, sy)))
            else:
                pygame.draw.circle(surface, ENEMY_COLOR, (sx, sy), self.radius)
                eo = int(6*SCALE); er1 = int(5*SCALE); er2 = int(3*SCALE); ey2 = int(5*SCALE)
                pygame.draw.circle(surface, (255,255,255), (sx-eo, sy-ey2), er1)
                pygame.draw.circle(surface, (255,255,255), (sx+eo, sy-ey2), er1)
                pygame.draw.circle(surface, (0,0,0),       (sx-eo+1, sy-ey2), er2)
                pygame.draw.circle(surface, (0,0,0),       (sx+eo+1, sy-ey2), er2)

# ─────────────────────────────────────────────
# 총알
# ─────────────────────────────────────────────
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
# 객체 생성
# ─────────────────────────────────────────────
player  = Player()
player.world_x = BATTLE_START_X
player.world_y = BATTLE_START_Y

enemies = []
_BATTLE_ENEMY_ZONES = [
    (70,   70,   712,  655),
    (1892, 70,   2450, 655),
    (70,   707,  712,  1162),
]
_mg = 75

def spawn_enemies():
    enemies.clear()
    for zone_idx, (x1, y1, x2, y2) in enumerate(_BATTLE_ENEMY_ZONES):
        for _ in range(random.randint(1, 2)):
            ex = random.randint(x1 + _mg, x2 - _mg)
            ey = random.randint(y1 + _mg, y2 - _mg)
            etype = random.choice([1, 2])
            enemies.append(Enemy(ex, ey, 0, etype))

spawn_enemies()

bullets = []
current_stage_text = "2-5"

# ─────────────────────────────────────────────
# 미니맵
# ─────────────────────────────────────────────
START_ROOM_ID = 1

def draw_minimap(surface, rooms, id_map, mini_connections, player_room_id, mm_x, mm_y):
    mm_box_w = int(180 * SCALE)
    mm_box_h = int(200 * SCALE)
    panel = pygame.Surface((mm_box_w, mm_box_h), pygame.SRCALPHA)
    panel.fill((8, 8, 12, 210))
    pygame.draw.rect(panel, (55,55,65,255), (0,0,mm_box_w,mm_box_h), 2, border_radius=8)
    surface.blit(panel, (mm_x, mm_y))
    ss = font_mini.render(current_stage_text, True, (180,180,180))
    surface.blit(ss, ss.get_rect(centerx=mm_x+mm_box_w//2, top=mm_y+mm_box_h-int(18*SCALE)))

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

# 2회차 침대 대화 (mon 이미지 등장 후)
BED_SLEEP_DIALOG_2 = [
    ("", "", "(……또 그 목소리인가.)"),
    ("???", "", "아직도 보이지 않는가……. 눈을 떠라."),
    ("히나", "선도부", "……!"),
    ("", "", "(이번에는 분명히 들렸다. 하지만 역시 아무것도 없다.)"),
    ("히나", "선도부", "(……기분 탓이 아닌 것 같군.)"),
    ("", "", "(일단 다시 자도록 하자. 내일 확인하면 된다.)"),
]

ACO_DIALOG = [
    ("히나", "선도부", "...아코."),
    ("아코", "선도부", "아, 히나 선도부장님. 오셨군요."),
    ("히나", "선도부", "무슨 일이지?"),
    ("아코", "선도부", "최근 여러 학원에서 심상치 않은 사건들이 발생하고 있습니다."),
    ("히나", "선도부", "심상치 않은 사건?"),
    ("아코", "선도부", "네. 타 학원 학생이 다른 학원에 나타나 소란을 일으키는 사건입니다."),
    ("히나", "선도부", "..."),
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
    ("아코", "선도부", "보고된 사건들을 정리한 문서입니다."),
    ("히나", "선도부", "....많네."),
    ("아코", "선도부", "생각보다 상황이 심각합니다."),
    ("히나", "선도부", "다녀올게."),
    ("아코", "선도부", "예, 조심히 다녀오십시오.")
]

ACO_DIALOG_2 = [
    ("히나", "선도부", "...아코."),
    ("아코", "선도부", "선도부장님, 다시 오셨군요. 또 발생했습니다."),
    ("히나", "선도부", "...또?"),
    ("아코", "선도부", "네. 이번엔 동시다발적으로 세 학원에서 한꺼번에 터졌습니다."),
    ("히나", "선도부", "패턴이 바뀌었군."),
    ("아코", "선도부", "예. 처음엔 산발적이었는데 이번엔 동시에."),
    ("히나", "선도부", "...의도적이야."),
    ("아코", "선도부", "저도 그렇게 생각합니다. 단순 우연이 아닌 것 같습니다."),
    ("히나", "선도부", "피해 학원은?"),
    ("아코", "선도부", "밀레니엄, 트리니티, 아비도스입니다."),
    ("히나", "선도부", "...범위가 넓군."),
    ("아코", "선도부", "공통점을 찾아봤는데... 전부 어제 밤 늦게 발생했습니다."),
    ("히나", "선도부", "심야에."),
    ("아코", "선도부", "예. 당사자들은 역시 기억이 없다고 합니다."),
    ("히나", "선도부", "...가보지."),
    ("아코", "선도부", "예. 조심히 다녀오십시오, 선도부장님."),
]

ACO_CLEAR_DIALOG = [
    ("아코", "선도부", "선도부장님, 수고하셨습니다."),
    ("히나", "선도부", "... 별다른 단서는 없었어."),
    ("아코", "선도부", "이번 소란을 이렇게 빨리 진정시킨 건 선도부장님뿐입니다."),
    ("아코", "선도부", "학생들도 안정을 되찾고 있으니 너무 자책하지 않으셔도 됩니다."),
    ("히나", "선도부", "오늘은 이만 들어가 볼게. 조금 피곤하네."),
    ("아코", "선도부", "예, 충분히 쉬세요 선도부장님."),
]

# 2회차 클리어 후: mon 접근 시 대화
MON_APPROACH_DIALOG_2 = [
    ("히나", "선도부", "...뭐지, 저건."),
    ("???", "", "……드디어 왔군."),
    ("히나", "선도부", "누구야. 지금까지의 사건들은 네가 꾸민 거냐?"),
    ("???", "", "질문은 나중에. 지금은……따라와라."),
    ("히나", "선도부", "……!"),
]

# 3회차 전투 후 대화 (허탕 + mon 발견)
ACO_CLEAR_DIALOG_3_PRE = [
    ("히나", "선도부", "...이번에도 허탕인가."),
    ("아코", "선도부", "선도부장님?"),
    ("히나", "선도부", "학생들 제압은 했는데, 아무것도 안 나왔어. 배후도, 단서도."),
    ("히나", "선도부", "뭔가 이상해. 마치 누군가가 의도적으로 학생들을 보내는 것 같은 느낌이——"),
]

# 3회차 mon 등장 대화
ACO_CLEAR_DIALOG_3_MON = [
    ("히나", "선도부", "...저게 뭐지?"),
    ("아코", "선도부", "선도부장님, 맵 중앙에 뭔가 나타났습니다!"),
    ("히나", "선도부", "처음 보는 존재군."),
    ("아코", "선도부", "관측 데이터가 일치하지 않습니다. 학원 학생이 아닙니다."),
    ("히나", "선도부", "...그렇다면 이번 사건의 배후인가."),
    ("아코", "선도부", "조심하십시오, 선도부장님."),
]

MISSION_HINA_ROOM    = "제복을 갈아입기."
MISSION_SLEEP        = "침대에 눕기."
MISSION_PREFECT      = "아코에게 말을 걸기."
MISSION_BATTLE       = "모든 학생들 제압하기."
MISSION_AFTER_BATTLE = "아코에게 말을 걸기."
MISSION_MON_APPROACH = "이상현상 파악하기."
MISSION_PIANO_ROOM   = "장소 조사하기."

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
# 타이틀 화면
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
# 페이드 아웃
# ─────────────────────────────────────────────
def draw_fadeout(surface, alpha):
    ov = pygame.Surface((WIDTH, HEIGHT))
    ov.fill((0, 0, 0))
    ov.set_alpha(int(alpha))
    surface.blit(ov, (0, 0))

# ─────────────────────────────────────────────
# ── 1회차 수면 시 히나 방에서 mon 표시 ──
# 페이드아웃 중 오른쪽에 플레이어 크기로 mon 표시 (3초)
# ─────────────────────────────────────────────
MON_ROOM_SHOW_START  = 400    # 페이드아웃 시작 후 이 ms 뒤 등장
MON_ROOM_FADE_IN_MS  = 300    # 페이드인 시간
MON_ROOM_HOLD_MS     = 3000   # 총 표시 유지 시간 (3초)
MON_ROOM_FADE_OUT_MS = 400    # 페이드아웃 시간

def draw_mon_in_room(surface, elapsed_since_fadeout, current_time):
    """1회차 수면 페이드아웃 중 오른쪽에 플레이어 크기 mon 표시"""
    if mon_room_img is None:
        return
    if elapsed_since_fadeout < MON_ROOM_SHOW_START:
        return

    t = elapsed_since_fadeout - MON_ROOM_SHOW_START
    total_visible = MON_ROOM_HOLD_MS + MON_ROOM_FADE_IN_MS + MON_ROOM_FADE_OUT_MS

    if t > total_visible:
        return

    # 페이드인
    if t < MON_ROOM_FADE_IN_MS:
        alpha_ratio = t / MON_ROOM_FADE_IN_MS
    # 유지
    elif t < MON_ROOM_FADE_IN_MS + MON_ROOM_HOLD_MS:
        alpha_ratio = 1.0
    # 페이드아웃
    else:
        alpha_ratio = 1.0 - (t - MON_ROOM_FADE_IN_MS - MON_ROOM_HOLD_MS) / MON_ROOM_FADE_OUT_MS
        alpha_ratio = max(0.0, alpha_ratio)

    # 깜빡임 (초반 0.3초)
    if t < 300:
        if (current_time // 80) % 2 == 0:
            return

    # 맥동
    pulse = 0.88 + 0.12 * math.sin(current_time / 110.0)
    alpha = int(255 * alpha_ratio * pulse)

    mon_copy = mon_room_img.copy()
    mon_copy.set_alpha(alpha)

    # 오른쪽 중앙, 약간 위아래로 떠오르는 효과
    float_y = int(6 * math.sin(current_time / 350.0))
    rx = WIDTH - mon_room_img.get_width() - int(300 * SCALE)
    ry = HEIGHT // 2 - 100 - mon_room_img.get_height() // 2 + float_y
    surface.blit(mon_copy, (rx, ry))

    # 붉은 글로우 테두리
    if alpha > 80:
        glow_alpha = int(70 * alpha_ratio * pulse)
        gs = pygame.Surface((mon_room_img.get_width() + 24, mon_room_img.get_height() + 24), pygame.SRCALPHA)
        pygame.draw.rect(gs, (180, 20, 20, glow_alpha), gs.get_rect(), 3, border_radius=5)
        surface.blit(gs, (rx - 12, ry - 12))

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

    if aco_img:
        ax = ACO_SCREEN_POS[0] - ACO_DRAW_W // 2
        ay = ACO_SCREEN_POS[1] - ACO_DRAW_H // 2
        surface.blit(aco_img, (ax, ay))
    else:
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
# 피아노 방 씬
# ─────────────────────────────────────────────
def draw_piano_room(surface, current_time):
    surface.fill((0, 0, 0))
    if piano_room_img:
        surface.blit(piano_room_img, piano_room_rect)
    else:
        surface.fill((15, 10, 25))
        lbl = font_medium.render("피아노 방", True, (200, 180, 255))
        surface.blit(lbl, lbl.get_rect(center=(WIDTH//2, HEIGHT//2)))

# ─────────────────────────────────────────────
# 메인 루프 변수
# ─────────────────────────────────────────────
game_state           = "title"
running              = True
hina_bgm_started     = False
battle_bgm_started   = False

opening  = OpeningNarration(OPENING_LINES)
hina_dlg = DialogSystem(HINA_ROOM_DIALOG)

mid_dlg: DialogSystem | None = None
aco_dlg: DialogSystem | None = None
aco_talked   = False
bed_used     = False

fadeout_start    = 0
FADEOUT_DURATION = 1200
# 1회차 수면 페이드는 더 길게 (mon 표시 3초 + 여유)
SLEEP_FADEOUT_DURATION = 4200  # 페이드인400 + 유지3000 + 페이드아웃400 + 여유400

prefect_fadeout_start    = 0
PREFECT_FADEOUT_DURATION = 1200

battle_clear_fadeout_start   = 0
BATTLE_CLEAR_FADEOUT_DURATION = 1400
battle_cleared = False

aco_clear_dlg: DialogSystem | None = None
aco_clear_talked = False

# ── 회차 관리 ──
cycle = 1

# 2회차 히나 방
bed_used_2      = False
aco_talked_2    = False

# 2회차 전투: mon 출현 및 접근 관련
battle_2_mon_appeared  = False   # 적 전멸 후 mon 출현
battle_2_mon_approached = False  # mon에 접근 완료
mon_approach_dlg: DialogSystem | None = None  # 접근 시 대화
# 2회차 mon 출현 시 카메라 고정 여부
battle_2_cam_locked = False
battle_2_cam_x = 0
battle_2_cam_y = 0
# 2회차 mon 페이드인 + 카메라 복귀
battle_2_mon_appear_start = 0
BATTLE_2_MON_APPEAR_MS    = 1000   # mon 페이드인 시간
BATTLE_2_CAM_SHOW_MS      = 2500   # 페이드인 후 mon 보여주는 시간
BATTLE_2_CAM_RETURN_MS    = 1200   # 카메라 복귀 시간
battle_2_cam_returning    = False
battle_2_cam_return_start = 0
battle_2_player_cam_x     = 0
battle_2_player_cam_y     = 0

# 3회차
bed_used_3      = False
aco_talked_3    = False
aco_clear_dlg_3_pre: DialogSystem | None = None
aco_clear_dlg_3_mon: DialogSystem | None = None
aco_pre_done_3  = False

# 3회차 카메라 이동 + mon 출현 효과
cam_cinematic_start   = 0
CAM_CINEMATIC_DURATION = 2500
mon_revealed          = False

e_prev = False

# piano_room 페이드인
piano_room_fadeout_start = 0
PIANO_ROOM_FADEIN_DURATION = 1200

# 피아노 방 워크존 (이미지 1254x1254 → 700x700 스케일 기준, 중앙 정렬)
# 이미지 중앙 기준으로 대략적인 걷기 가능 영역
_PIANO_WALK_POLY = [
    (190, 620), (190, 290), (280, 290), (280, 210),
    (780, 210), (780, 620),
]

# 피아노 상호작용 위치 (이미지상 피아노 중심부)
PIANO_INTERACT_POS    = (580, 450)
PIANO_INTERACT_RADIUS = 90

# 피아노 방 입장 시 히나 대사
PIANO_ROOM_ENTER_DIALOG = [
    ("히나", "선도부", "...여기는."),
    ("히나", "선도부", "피아노가 있군. 그런데..."),
    ("히나", "선도부", "(방치된 지 꽤 됐군. 악보가 바닥에 흩어져 있고, 식물도 자라고 있어.)"),
    ("히나", "선도부", "(그런데 왜 여기로 이끌린 거지.)"),
]

# 피아노 상호작용 후 히나 대사
PIANO_INTERACT_DIALOG = [
    ("히나", "선도부", "(악보를 펼쳤다. 빼곡하게 적힌 음표들——)"),
    ("히나", "선도부", "(이 곡은... 연주회에서 들었던 그 선율이군.)"),
    ("히나", "선도부", "...설마."),
    ("히나", "선도부", "(모든 사건이 이 음악과 연결된 건가.)"),
]

# ml_room 씬 상태
ml_room_cam_x    = 0
ml_room_cam_y    = 0
ml_room_fadeout_start = 0
ML_ROOM_FADEIN_MS     = 1200

# 챕터 타이틀 연출
# phase: "black"→완전검정 잠깐, "ch1_in"→1장 게헨나 페이드인, "ch1_hold"→유지,
#        "ch1_out"→페이드아웃, "ch2_in"→2장 밀레니엄 페이드인, "ch2_hold"→유지,
#        "to_title"→타이틀로 페이드
chapter_title_phase      = "black"
chapter_title_phase_start = 0
CH_BLACK_MS   = 800
CH_FADE_IN_MS = 900
CH_HOLD_MS    = 1800
CH_FADE_OUT_MS= 700
CH_GAP_MS     = 400   # ch1 사라진 뒤 ch2 뜨기 전 간격
CH_TO_TITLE_FADEIN_MS = 1200

# 피아노 방 상태 변수
piano_enter_dlg: DialogSystem | None = None
piano_enter_done = False
piano_interacted = False
piano_interact_dlg: DialogSystem | None = None

# ─────────────────────────────────────────────
# F10 디버그 메뉴
# ─────────────────────────────────────────────
DEBUG_STAGES = [
    ("1. 타이틀",                   "title"),
    ("2. 오프닝 나레이션",           "intro"),
    ("3. 히나 방 대화",             "hina_dialog"),
    ("4. 히나 방 (자유)",           "hina_room"),
    ("5. 선도부실",                 "prefect_room"),
    ("6. 전투 맵",                  "battle"),
    ("7. 클리어 후 선도부실 1",      "post_battle_prefect"),
    ("8. 히나 방 2회차",            "hina_room_2"),
    ("9. 선도부실 2회차",           "prefect_room_2"),
    ("10. 전투 맵 2회차",           "battle_2"),
    ("11. 2회차 mon 접근 씬",       "battle_2_mon_scene"),
    ("12. 피아노 방",               "piano_room"),
    ("13. 히나 방 3회차",           "hina_room_3"),
    ("14. 선도부실 3회차",          "prefect_room_3"),
    ("15. 전투 맵 3회차",           "battle_3"),
    ("16. 3회차 클리어 씬",         "battle_3_clear_scene"),
]
debug_menu_open  = False
debug_cursor     = 0
font_debug       = _make_font(18, bold=True)
font_debug_title = _make_font(22, bold=True)

def _jump_to_stage(target_state):
    global game_state, hina_bgm_started, battle_bgm_started
    global bed_used, aco_talked, mid_dlg, aco_dlg
    global fadeout_start, prefect_fadeout_start
    global battle_cleared, aco_clear_dlg, aco_clear_talked
    global battle_clear_fadeout_start
    global cycle
    global bed_used_2, aco_talked_2
    global battle_2_mon_appeared, battle_2_mon_approached, mon_approach_dlg
    global battle_2_cam_locked, battle_2_cam_x, battle_2_cam_y, battle_2_mon_appear_start
    global battle_2_cam_returning, battle_2_cam_return_start, battle_2_player_cam_x, battle_2_player_cam_y
    global battle_2_cam_locked, battle_2_cam_x, battle_2_cam_y, battle_2_mon_appear_start
    global bed_used_3, aco_talked_3, aco_clear_dlg_3_pre, aco_clear_dlg_3_mon
    global aco_pre_done_3, cam_cinematic_start, mon_revealed
    global piano_room_fadeout_start
    global piano_enter_dlg, piano_enter_done, piano_interacted, piano_interact_dlg
    global ml_room_cam_x, ml_room_cam_y, ml_room_fadeout_start
    global chapter_title_phase, chapter_title_phase_start

    game_state = target_state

    if target_state == "title":
        pygame.mixer.music.stop()
        hina_bgm_started   = False
        battle_bgm_started = False
        cycle = 1

    elif target_state == "intro":
        pygame.mixer.music.stop()
        hina_bgm_started   = False
        battle_bgm_started = False
        opening.line_idx  = 0; opening.char_idx  = 0
        opening.last_char = 0; opening.finished  = False

    elif target_state == "hina_dialog":
        if not hina_bgm_started:
            play_bgm(0); hina_bgm_started = True
        hina_dlg.idx = 0; hina_dlg.char_idx = 0
        hina_dlg.last_char = 0; hina_dlg.finished = False

    elif target_state == "hina_room":
        cycle = 1
        if not hina_bgm_started:
            play_bgm(0); hina_bgm_started = True
        player.hina_sx = 500.0; player.hina_sy = 560.0
        player.costume = "uniform"
        bed_used = False; mid_dlg = None

    elif target_state == "prefect_room":
        cycle = 1
        play_funky_road()
        player.hina_sx = 500.0; player.hina_sy = 560.0
        player.costume = "uniform"
        aco_talked = False; aco_dlg = None

    elif target_state == "battle":
        cycle = 1
        if not battle_bgm_started:
            play_bgm(1); battle_bgm_started = True
        player.world_x = BATTLE_START_X; player.world_y = BATTLE_START_Y
        player.costume = "uniform"
        spawn_enemies(); bullets.clear()

    elif target_state == "post_battle_prefect":
        cycle = 1
        play_funky_road()
        player.hina_sx = 500.0; player.hina_sy = 560.0
        player.costume = "uniform"
        battle_cleared = True
        aco_clear_talked = False; aco_clear_dlg = None

    elif target_state == "hina_room_2":
        cycle = 2
        play_bgm(0); hina_bgm_started = True
        player.hina_sx = 500.0; player.hina_sy = 560.0
        player.costume = "uniform"
        bed_used_2 = False; mid_dlg = None

    elif target_state == "prefect_room_2":
        cycle = 2
        play_funky_road()
        player.hina_sx = 500.0; player.hina_sy = 560.0
        player.costume = "uniform"
        aco_talked_2 = False; aco_dlg = None

    elif target_state == "battle_2":
        cycle = 2
        play_bgm(1); battle_bgm_started = True
        player.world_x = BATTLE_START_X; player.world_y = BATTLE_START_Y
        player.costume = "uniform"
        spawn_enemies(); bullets.clear()
        battle_2_mon_appeared   = False
        battle_2_mon_approached = False
        battle_2_cam_locked     = False
        mon_approach_dlg        = None

    elif target_state == "battle_2_mon_scene":
        cycle = 2
        play_bgm(1)
        player.world_x = BATTLE_START_X; player.world_y = BATTLE_START_Y
        enemies.clear(); bullets.clear()
        battle_2_mon_appeared   = True
        battle_2_mon_approached = False
        battle_2_cam_locked     = True
        battle_2_cam_returning  = False
        battle_2_mon_appear_start = pygame.time.get_ticks()
        battle_2_cam_x = max(0, min(MON_WORLD_X - WIDTH//2,  BATTLE_MAP_W - WIDTH))
        battle_2_cam_y = max(0, min(MON_WORLD_Y - HEIGHT//2, BATTLE_MAP_H - HEIGHT))
        mon_approach_dlg = None
        game_state = "battle_2"  # 전투 루프가 처리

    elif target_state == "piano_room":
        cycle = 2
        pygame.mixer.music.stop()
        piano_room_fadeout_start = pygame.time.get_ticks()
        player.hina_sx = 490.0; player.hina_sy = 580.0
        player.costume = "uniform"
        piano_enter_dlg   = None
        piano_enter_done  = False
        piano_interacted  = False
        piano_interact_dlg = None

    elif target_state == "hina_room_3":
        cycle = 3
        play_bgm(0); hina_bgm_started = True
        player.hina_sx = 500.0; player.hina_sy = 560.0
        player.costume = "uniform"
        bed_used_3 = False; mid_dlg = None

    elif target_state == "prefect_room_3":
        cycle = 3
        play_funky_road()
        player.hina_sx = 500.0; player.hina_sy = 560.0
        player.costume = "uniform"
        aco_talked_3 = False; aco_dlg = None

    elif target_state == "battle_3":
        cycle = 3
        play_bgm(1); battle_bgm_started = True
        player.world_x = BATTLE_START_X; player.world_y = BATTLE_START_Y
        player.costume = "uniform"
        spawn_enemies(); bullets.clear()
        mon_revealed = False

    elif target_state == "battle_3_clear_scene":
        cycle = 3
        play_bgm(1)
        player.world_x = BATTLE_START_X; player.world_y = BATTLE_START_Y
        enemies.clear(); bullets.clear()
        aco_clear_dlg_3_pre = DialogSystem(ACO_CLEAR_DIALOG_3_PRE)
        aco_pre_done_3 = False
        mon_revealed = False
        cam_cinematic_start = pygame.time.get_ticks()


def _draw_debug_menu(surface, cursor):
    ov = pygame.Surface((WIDTH, HEIGHT), pygame.SRCALPHA)
    ov.fill((0, 0, 0, 190))
    surface.blit(ov, (0, 0))

    panel_w = 460
    panel_h = 60 + len(DEBUG_STAGES) * 40 + 20
    px = WIDTH  // 2 - panel_w // 2
    py = max(10, HEIGHT // 2 - panel_h // 2)

    panel = pygame.Surface((panel_w, panel_h), pygame.SRCALPHA)
    panel.fill((12, 18, 35, 240))
    pygame.draw.rect(panel, (80, 120, 200, 200), (0, 0, panel_w, panel_h), 2, border_radius=8)
    surface.blit(panel, (px, py))

    title_s = font_debug_title.render("[ DEBUG  —  STAGE SELECT ]", True, (130, 180, 255))
    surface.blit(title_s, title_s.get_rect(centerx=px + panel_w // 2, top=py + 10))

    for i, (label, _) in enumerate(DEBUG_STAGES):
        item_y = py + 50 + i * 40
        is_sel = (i == cursor)
        if is_sel:
            sel_rect = pygame.Rect(px + 10, item_y - 4, panel_w - 20, 32)
            pygame.draw.rect(surface, (50, 90, 200, 180), sel_rect, border_radius=5)
            pygame.draw.rect(surface, (100, 160, 255, 220), sel_rect, 1, border_radius=5)
        color  = (255, 240, 100) if is_sel else (190, 200, 220)
        prefix = "▶  " if is_sel else "    "
        txt = font_debug.render(prefix + label, True, color)
        surface.blit(txt, (px + 22, item_y))

    hint = font_debug.render("↑↓ 이동   Enter 선택   F10 닫기", True, (100, 120, 160))
    surface.blit(hint, hint.get_rect(centerx=px + panel_w // 2, top=py + panel_h - 26))

# ─────────────────────────────────────────────
# 전투 씬 공통 렌더러
# ─────────────────────────────────────────────
def render_battle_scene(surface, cam_x, cam_y, show_debug_overlay=True, show_player=True):
    surface.fill(BG_COLOR)
    if battle_bg_img:
        surface.blit(battle_bg_img, (-cam_x, -cam_y))

    if show_debug_overlay and not debug_menu_open:
        for poly in _BATTLE_WALK_POLYS:
            sp = [(x - cam_x, y - cam_y) for x, y in poly]
            pygame.draw.polygon(surface, (0, 220, 80), sp, 2)
        for rect in _BATTLE_CORRIDOR_RECTS:
            sr = pygame.Rect(rect.x - cam_x, rect.y - cam_y, rect.width, rect.height)
            pygame.draw.rect(surface, (80, 180, 255), sr, 2)

    for enemy in enemies:
        ex = int(enemy.world_x) - cam_x
        ey = int(enemy.world_y) - cam_y
        enemy.draw(surface, ex, ey, current_time)

    for bullet in bullets:
        pygame.draw.circle(surface, BULLET_COLOR,
                           (int(bullet.world_x) - cam_x, int(bullet.world_y) - cam_y),
                           bullet.radius)

    if show_player:
        px_s = int(player.world_x) - cam_x
        py_s = int(player.world_y) - cam_y
        player.draw(surface, px_s, py_s, current_time)

def _draw_mon_on_battle(surface, cam_x, cam_y, alpha_override=None):
    """전투 맵 위에 mon 표시 (크기 고정, 단순 알파)"""
    if mon_map_img is None:
        return
    a = 255 if alpha_override is None else int(alpha_override)
    a = max(0, min(255, a))
    mon_copy = mon_map_img.copy()
    mon_copy.set_alpha(a)
    mon_sx = MON_WORLD_X - cam_x
    mon_sy = MON_WORLD_Y - cam_y
    surface.blit(mon_copy, mon_copy.get_rect(center=(mon_sx, mon_sy)))

def _draw_vignette(surface, alpha=100):
    vign = pygame.Surface((WIDTH, HEIGHT), pygame.SRCALPHA)
    for i in range(4):
        thick = 60 - i * 14
        pygame.draw.rect(vign, (150, 10, 10, max(0, alpha - i * 20)),
                         (0, 0, WIDTH, HEIGHT), thick)
    surface.blit(vign, (0, 0))

# ─────────────────────────────────────────────
# 메인 루프
# ─────────────────────────────────────────────
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

            if event.key == pygame.K_F10:
                debug_menu_open = not debug_menu_open
                debug_cursor    = 0

            if debug_menu_open:
                if event.key == pygame.K_UP:
                    debug_cursor = (debug_cursor - 1) % len(DEBUG_STAGES)
                elif event.key == pygame.K_DOWN:
                    debug_cursor = (debug_cursor + 1) % len(DEBUG_STAGES)
                elif event.key in (pygame.K_RETURN, pygame.K_KP_ENTER):
                    _jump_to_stage(DEBUG_STAGES[debug_cursor][1])
                    debug_menu_open = False
                continue

            # ── 타이틀
            if event.key == pygame.K_SPACE and game_state == "title":
                game_state = "intro"

            # ── 오프닝
            elif event.key == pygame.K_SPACE and game_state == "intro":
                opening.on_space()
                if opening.finished:
                    game_state = "hina_dialog"
                    if not hina_bgm_started:
                        play_bgm(0); hina_bgm_started = True

            # ── 히나 방 입장 대화
            elif event.key == pygame.K_SPACE and game_state == "hina_dialog":
                hina_dlg.on_space()
                if hina_dlg.finished:
                    game_state = "hina_room"
                    player.hina_sx = 500.0; player.hina_sy = 560.0

            # ── 히나 방 중간 대화
            elif event.key == pygame.K_SPACE and game_state == "hina_mid_dlg":
                if mid_dlg:
                    mid_dlg.on_space()
                    if mid_dlg.finished:
                        if mid_dlg.lines is BED_SLEEP_DIALOG:
                            # 1회차 수면 → sleep_fadeout (mon 방 안에 표시)
                            bed_used      = True
                            game_state    = "sleep_fadeout"
                            fadeout_start = current_time
                        elif mid_dlg.lines is BED_SLEEP_DIALOG_2:
                            if cycle == 2:
                                bed_used_2    = True
                                game_state    = "fadeout_2"
                                fadeout_start = current_time
                            else:
                                bed_used_3    = True
                                game_state    = "fadeout_3"
                                fadeout_start = current_time
                        elif mid_dlg.lines is BED_UNIFORM_DIALOG:
                            game_state = "hina_room" if cycle == 1 else (
                                         "hina_room_2" if cycle == 2 else "hina_room_3")
                            mid_dlg    = None

            # ── 선도부실 아코 대화 (공통)
            elif event.key == pygame.K_SPACE and game_state == "prefect_aco_dlg":
                if aco_dlg:
                    aco_dlg.on_space()
                    if aco_dlg.finished:
                        if cycle == 1:
                            aco_talked = True
                            game_state = "prefect_fadeout"
                            prefect_fadeout_start = current_time
                        elif cycle == 2:
                            aco_talked_2 = True
                            game_state   = "prefect_fadeout_2"
                            prefect_fadeout_start = current_time
                        elif cycle == 3:
                            aco_talked_3 = True
                            game_state   = "prefect_fadeout_3"
                            prefect_fadeout_start = current_time
                        aco_dlg = None

            # ── 1회차 클리어 후 아코 대화
            elif event.key == pygame.K_SPACE and game_state == "post_battle_aco_dlg":
                if aco_clear_dlg:
                    aco_clear_dlg.on_space()
                    if aco_clear_dlg.finished:
                        aco_clear_talked = True
                        aco_clear_dlg    = None
                        game_state    = "to_hina_2_fadeout"
                        fadeout_start = current_time

            # ── 2회차 mon 접근 대화
            elif event.key == pygame.K_SPACE and game_state == "battle_2_mon_dlg":
                if mon_approach_dlg:
                    mon_approach_dlg.on_space()
                    if mon_approach_dlg.finished:
                        mon_approach_dlg = None
                        # → 피아노 방 페이드인
                        game_state = "to_piano_fadeout"
                        fadeout_start = current_time

            # ── 3회차 "허탕" 대화
            elif event.key == pygame.K_SPACE and game_state == "battle_3_pre_dlg":
                if aco_clear_dlg_3_pre:
                    aco_clear_dlg_3_pre.on_space()
                    if aco_clear_dlg_3_pre.finished:
                        aco_pre_done_3 = True
                        game_state = "battle_3_cam_cinematic"
                        cam_cinematic_start = current_time
                        aco_clear_dlg_3_pre = None

            # ── 3회차 mon 등장 대화
            elif event.key == pygame.K_SPACE and game_state == "battle_3_mon_dlg":
                if aco_clear_dlg_3_mon:
                    aco_clear_dlg_3_mon.on_space()
                    if aco_clear_dlg_3_mon.finished:
                        aco_clear_dlg_3_mon = None
                        game_state = "battle_3_mon_dlg_done"

            elif event.key == pygame.K_SPACE and game_state == "piano_enter_dlg":
                if piano_enter_dlg:
                    piano_enter_dlg.on_space()
                    if piano_enter_dlg.finished:
                        piano_enter_done = True
                        piano_enter_dlg  = None
                        game_state = "piano_room"

            elif event.key == pygame.K_SPACE and game_state == "piano_interact_dlg":
                if piano_interact_dlg:
                    piano_interact_dlg.on_space()
                    if piano_interact_dlg.finished:
                        piano_interact_dlg = None
                        # ml_room 씬으로
                        game_state = "to_ml_room_fadeout"
                        ml_room_fadeout_start = current_time
                        ml_room_cam_x = 0
                        ml_room_cam_y = 0

    # ══════════════════════════════════════════
    # 상태 렌더링
    # ══════════════════════════════════════════

    if game_state == "title":
        draw_title_screen(screen, current_time)
        if debug_menu_open: _draw_debug_menu(screen, debug_cursor)
        pygame.display.flip(); clock.tick(60); continue

    if game_state == "intro":
        opening.update(current_time)
        opening.draw(screen, current_time)
        if debug_menu_open: _draw_debug_menu(screen, debug_cursor)
        pygame.display.flip(); clock.tick(60); continue

    if game_state == "hina_dialog":
        hina_dlg.update(current_time)
        screen.fill((0, 0, 0))
        if hina_room_img: screen.blit(hina_room_img, hina_room_rect)
        hina_dlg.draw(screen, current_time)
        if debug_menu_open: _draw_debug_menu(screen, debug_cursor)
        pygame.display.flip(); clock.tick(60); continue

    # ─── 히나 방 공통 (1/2/3회차) ───
    if game_state in ("hina_room", "hina_room_2", "hina_room_3"):
        keys = pygame.key.get_pressed()
        player.update_hina_room(keys, current_time)
        e_now = keys[pygame.K_e]

        dist_wardrobe = math.hypot(player.hina_sx - WARDROBE_POS[0], player.hina_sy - WARDROBE_POS[1])
        dist_bed      = math.hypot(player.hina_sx - BED_POS[0],      player.hina_sy - BED_POS[1])

        _bed_used = (bed_used if cycle == 1 else bed_used_2 if cycle == 2 else bed_used_3)
        near_wardrobe = (dist_wardrobe < WARDROBE_RADIUS) and (player.costume == "uniform")
        near_bed      = (dist_bed < BED_RADIUS) and not _bed_used

        if player.costume == "uniform":
            mission_txt = MISSION_HINA_ROOM
        elif not _bed_used:
            mission_txt = MISSION_SLEEP
        else:
            mission_txt = None

        if e_now and not e_prev:
            if near_wardrobe:
                player.costume = "sleep"
            elif near_bed:
                if player.costume == "uniform":
                    mid_dlg = DialogSystem(BED_UNIFORM_DIALOG)
                    game_state = "hina_mid_dlg"
                else:
                    if cycle == 1:
                        mid_dlg = DialogSystem(BED_SLEEP_DIALOG)
                    else:
                        mid_dlg = DialogSystem(BED_SLEEP_DIALOG_2)
                    game_state = "hina_mid_dlg"

        e_prev = e_now

        draw_hina_room(screen, player, current_time,
                       near_wardrobe=near_wardrobe, near_bed=near_bed, mission=mission_txt)
        mx, my = pygame.mouse.get_pos()
        dbg = font_mini.render(f"mouse: ({mx}, {my})", True, (255, 255, 0))
        screen.blit(dbg, (10, 40))
        if debug_menu_open: _draw_debug_menu(screen, debug_cursor)
        pygame.display.flip(); clock.tick(60); continue

    if game_state == "hina_mid_dlg":
        if mid_dlg: mid_dlg.update(current_time)
        screen.fill((0, 0, 0))
        if hina_room_img: screen.blit(hina_room_img, hina_room_rect)
        player.draw(screen, int(player.hina_sx), int(player.hina_sy), current_time)
        if mid_dlg: mid_dlg.draw(screen, current_time)
        if debug_menu_open: _draw_debug_menu(screen, debug_cursor)
        pygame.display.flip(); clock.tick(60); continue

    # ─────────────────────────────────────────
    # ── 1회차 수면 페이드아웃 (mon이 방 오른쪽에 등장) ──
    # ─────────────────────────────────────────
    if game_state == "sleep_fadeout":
        elapsed = current_time - fadeout_start
        alpha   = min(255, int(255 * elapsed / SLEEP_FADEOUT_DURATION))
        screen.fill((0, 0, 0))
        if hina_room_img: screen.blit(hina_room_img, hina_room_rect)
        player.draw(screen, int(player.hina_sx), int(player.hina_sy), current_time)
        draw_fadeout(screen, alpha)
        if elapsed >= SLEEP_FADEOUT_DURATION:
            cycle = 1
            game_state = "prefect_room"
            player.hina_sx = 500.0; player.hina_sy = 560.0
            player.costume = "uniform"
            play_funky_road()
        if debug_menu_open: _draw_debug_menu(screen, debug_cursor)
        pygame.display.flip(); clock.tick(60); continue

    # ── 2회차 수면 페이드 → 선도부실 2
    # ── 2회차 수면 페이드 → 선도부실 2 (mon 오른쪽에 등장)
    if game_state == "fadeout_2":
        elapsed = current_time - fadeout_start
        alpha   = min(255, int(255 * elapsed / SLEEP_FADEOUT_DURATION))
        screen.fill((0, 0, 0))
        if hina_room_img: screen.blit(hina_room_img, hina_room_rect)
        player.draw(screen, int(player.hina_sx), int(player.hina_sy), current_time)
        draw_fadeout(screen, alpha)
        draw_mon_in_room(screen, elapsed, current_time)
        if elapsed >= SLEEP_FADEOUT_DURATION:
            cycle = 2
            game_state = "prefect_room_2"
            player.hina_sx = 500.0; player.hina_sy = 560.0
            player.costume = "uniform"
            play_funky_road()
        if debug_menu_open: _draw_debug_menu(screen, debug_cursor)
        pygame.display.flip(); clock.tick(60); continue

    # ── 3회차 수면 페이드 → 선도부실 3
    if game_state == "fadeout_3":
        elapsed = current_time - fadeout_start
        alpha   = min(255, int(255 * elapsed / FADEOUT_DURATION))
        screen.fill((0, 0, 0))
        if hina_room_img: screen.blit(hina_room_img, hina_room_rect)
        player.draw(screen, int(player.hina_sx), int(player.hina_sy), current_time)
        draw_fadeout(screen, alpha)
        if elapsed >= FADEOUT_DURATION:
            cycle = 3
            game_state = "prefect_room_3"
            player.hina_sx = 500.0; player.hina_sy = 560.0
            player.costume = "uniform"
            play_funky_road()
        if debug_menu_open: _draw_debug_menu(screen, debug_cursor)
        pygame.display.flip(); clock.tick(60); continue

    # ── 1회차 클리어 후 → 히나 방 2회차
    if game_state == "to_hina_2_fadeout":
        elapsed = current_time - fadeout_start
        alpha   = min(255, int(255 * elapsed / FADEOUT_DURATION))
        screen.fill((0, 0, 0))
        if prefect_room_img: screen.blit(prefect_room_img, prefect_room_rect)
        if aco_img:
            screen.blit(aco_img, (ACO_SCREEN_POS[0]-ACO_DRAW_W//2, ACO_SCREEN_POS[1]-ACO_DRAW_H//2))
        player.draw(screen, int(player.hina_sx), int(player.hina_sy), current_time)
        draw_fadeout(screen, alpha)
        if elapsed >= FADEOUT_DURATION:
            game_state = "hina_room_2"
            cycle = 2
            player.hina_sx = 500.0; player.hina_sy = 560.0
            player.costume = "uniform"
            bed_used_2 = False
            play_bgm(0)
        if debug_menu_open: _draw_debug_menu(screen, debug_cursor)
        pygame.display.flip(); clock.tick(60); continue

    # ── 2회차 mon 접근 후 → 피아노 방 페이드
    if game_state == "to_piano_fadeout":
        elapsed = current_time - fadeout_start
        alpha   = min(255, int(255 * elapsed / FADEOUT_DURATION))
        # 전투맵 배경 유지
        target_cam_x = max(0, min(MON_WORLD_X - WIDTH//2,  BATTLE_MAP_W - WIDTH))
        target_cam_y = max(0, min(MON_WORLD_Y - HEIGHT//2, BATTLE_MAP_H - HEIGHT))
        render_battle_scene(screen, target_cam_x, target_cam_y, show_player=True)
        _draw_mon_on_battle(screen, target_cam_x, target_cam_y)
        draw_fadeout(screen, alpha)
        if elapsed >= FADEOUT_DURATION:
            game_state = "piano_room"
            piano_room_fadeout_start = current_time
            pygame.mixer.music.stop()
            player.hina_sx = 490.0; player.hina_sy = 580.0
            player.costume = "uniform"
            piano_enter_dlg   = DialogSystem(PIANO_ROOM_ENTER_DIALOG)
            piano_enter_done  = False
            piano_interacted  = False
            piano_interact_dlg = None
        if debug_menu_open: _draw_debug_menu(screen, debug_cursor)
        pygame.display.flip(); clock.tick(60); continue

    # ─────────────────────────────────────────
    # ── 선도부실 공통 (1/2/3회차) ──
    # ─────────────────────────────────────────
    if game_state in ("prefect_room", "prefect_room_2", "prefect_room_3"):
        keys = pygame.key.get_pressed()
        player.update_prefect_room(keys, current_time)
        e_now = keys[pygame.K_e]

        dist_aco = math.hypot(player.hina_sx - ACO_SCREEN_POS[0], player.hina_sy - ACO_SCREEN_POS[1])
        _aco_t = (aco_talked if cycle == 1 else aco_talked_2 if cycle == 2 else aco_talked_3)
        near_aco = dist_aco < ACO_INTERACT_RADIUS and not _aco_t

        if e_now and not e_prev and near_aco:
            aco_dlg    = DialogSystem(ACO_DIALOG_2 if cycle == 2 else ACO_DIALOG)
            game_state = "prefect_aco_dlg"

        e_prev = e_now
        mission_txt = None if _aco_t else MISSION_PREFECT
        draw_prefect_room(screen, player, current_time, near_aco=near_aco, mission=mission_txt)
        if debug_menu_open: _draw_debug_menu(screen, debug_cursor)
        pygame.display.flip(); clock.tick(60); continue

    if game_state == "prefect_aco_dlg":
        if aco_dlg: aco_dlg.update(current_time)
        screen.fill((0, 0, 0))
        if prefect_room_img: screen.blit(prefect_room_img, prefect_room_rect)
        if aco_img:
            screen.blit(aco_img, (ACO_SCREEN_POS[0]-ACO_DRAW_W//2, ACO_SCREEN_POS[1]-ACO_DRAW_H//2))
        else:
            pygame.draw.circle(screen, (180, 120, 220), ACO_SCREEN_POS, 28)
        player.draw(screen, int(player.hina_sx), int(player.hina_sy), current_time)
        if aco_dlg: aco_dlg.draw(screen, current_time)
        if debug_menu_open: _draw_debug_menu(screen, debug_cursor)
        pygame.display.flip(); clock.tick(60); continue

    # ── 선도부실 → 전투 페이드 (1/2/3회차 공통) ──
    for _pf_state, _next_battle, _next_cycle in [
        ("prefect_fadeout",   "battle",   1),
        ("prefect_fadeout_2", "battle_2", 2),
        ("prefect_fadeout_3", "battle_3", 3),
    ]:
        if game_state == _pf_state:
            elapsed = current_time - prefect_fadeout_start
            alpha   = min(255, int(255 * elapsed / PREFECT_FADEOUT_DURATION))
            screen.fill((0, 0, 0))
            if prefect_room_img: screen.blit(prefect_room_img, prefect_room_rect)
            if aco_img:
                screen.blit(aco_img, (ACO_SCREEN_POS[0]-ACO_DRAW_W//2, ACO_SCREEN_POS[1]-ACO_DRAW_H//2))
            player.draw(screen, int(player.hina_sx), int(player.hina_sy), current_time)
            draw_fadeout(screen, alpha)
            if elapsed >= PREFECT_FADEOUT_DURATION:
                game_state = _next_battle
                cycle      = _next_cycle
                player.world_x = BATTLE_START_X; player.world_y = BATTLE_START_Y
                player.costume = "uniform"
                play_bgm(1); battle_bgm_started = True
                spawn_enemies(); bullets.clear()
                mon_revealed = False
                if _next_cycle == 2:
                    battle_2_mon_appeared   = False
                    battle_2_mon_approached = False
                    battle_2_cam_locked     = False
                    mon_approach_dlg        = None
            if debug_menu_open: _draw_debug_menu(screen, debug_cursor)
            pygame.display.flip(); clock.tick(60)
            break
    else:
        pass
    if game_state in ("prefect_fadeout", "prefect_fadeout_2", "prefect_fadeout_3"):
        continue

    # ─────────────────────────────────────────
    # ── 전투 맵 (1/2/3회차) ──
    # ─────────────────────────────────────────
    if game_state in ("battle", "battle_2", "battle_3"):
        keys = pygame.key.get_pressed()

        # 2회차 mon 출현 후 카메라가 mon 중앙 고정 → 플레이어만 자유 이동
        if game_state == "battle_2" and battle_2_mon_appeared and not battle_2_mon_approached:
            player.update(keys, [], current_time, [])  # 전투 없음, 이동만
        else:
            player.update(keys, enemies, current_time, bullets)

        # 총알 처리 (mon 출현 전에만)
        if not (game_state == "battle_2" and battle_2_mon_appeared):
            for bullet in bullets[:]:
                bullet.update()
                if bullet.distance_traveled > bullet.max_range:
                    bullets.remove(bullet); continue
                hit = False
                for enemy in enemies:
                    if enemy.is_dead: continue
                    ddx = bullet.world_x - enemy.world_x
                    ddy = bullet.world_y - enemy.world_y
                    if ddx*ddx + ddy*ddy < enemy.radius * enemy.radius:
                        enemy.take_hit(); hit = True; break
                if hit and bullet in bullets:
                    bullets.remove(bullet)

        alive_count = sum(1 for e in enemies if not e.is_dead)

        # ── 적 전멸 처리 ──
        if alive_count == 0 and len(enemies) > 0 and not (game_state == "battle_2" and battle_2_mon_appeared):
            bullets.clear()
            if game_state == "battle":
                game_state = "battle_clear_fadeout"
                battle_clear_fadeout_start = current_time
                battle_cleared = True
            elif game_state == "battle_2":
                # 2회차: 선도부실 안 가고 mon 출현 + BGM 정지
                enemies.clear()
                pygame.mixer.music.stop()
                battle_bgm_started      = False
                battle_2_mon_appeared   = True
                battle_2_mon_appear_start = current_time
                # 카메라를 mon 위치로 잠금
                battle_2_cam_locked    = True
                battle_2_cam_returning = False
                battle_2_cam_x = max(0, min(MON_WORLD_X - WIDTH//2,  BATTLE_MAP_W - WIDTH))
                battle_2_cam_y = max(0, min(MON_WORLD_Y - HEIGHT//2, BATTLE_MAP_H - HEIGHT))
            elif game_state == "battle_3":
                game_state = "battle_3_pre_dlg"
                aco_clear_dlg_3_pre = DialogSystem(ACO_CLEAR_DIALOG_3_PRE)
                aco_pre_done_3 = False

        # ── 카메라 ──
        if game_state == "battle_2" and battle_2_mon_appeared:
            elapsed_mon = current_time - battle_2_mon_appear_start
            total_lock = BATTLE_2_MON_APPEAR_MS + BATTLE_2_CAM_SHOW_MS

            if not battle_2_cam_returning and elapsed_mon >= total_lock:
                # 카메라 복귀 시작
                battle_2_cam_returning    = True
                battle_2_cam_return_start = current_time
                battle_2_player_cam_x = max(0, min(int(player.world_x) - WIDTH//2,  BATTLE_MAP_W - WIDTH))
                battle_2_player_cam_y = max(0, min(int(player.world_y) - HEIGHT//2, BATTLE_MAP_H - HEIGHT))

            if battle_2_cam_returning:
                rt = min(1.0, (current_time - battle_2_cam_return_start) / BATTLE_2_CAM_RETURN_MS)
                rt_ease = rt * rt * (3 - 2 * rt)
                cam_x = int(battle_2_cam_x + (battle_2_player_cam_x - battle_2_cam_x) * rt_ease)
                cam_y = int(battle_2_cam_y + (battle_2_player_cam_y - battle_2_cam_y) * rt_ease)
                # 복귀 완료 후에는 플레이어 추종
                if rt >= 1.0:
                    battle_2_cam_locked = False
                    cam_x = battle_2_player_cam_x
                    cam_y = battle_2_player_cam_y
            else:
                cam_x = battle_2_cam_x
                cam_y = battle_2_cam_y
        else:
            cam_x = int(player.world_x) - WIDTH  // 2
            cam_y = int(player.world_y) - HEIGHT // 2
            cam_x = max(0, min(cam_x, BATTLE_MAP_W - WIDTH))
            cam_y = max(0, min(cam_y, BATTLE_MAP_H - HEIGHT))

        # 카메라 잠금 해제 후에는 플레이어 기준으로 갱신
        if game_state == "battle_2" and battle_2_mon_appeared and not battle_2_cam_locked:
            cam_x = max(0, min(int(player.world_x) - WIDTH//2,  BATTLE_MAP_W - WIDTH))
            cam_y = max(0, min(int(player.world_y) - HEIGHT//2, BATTLE_MAP_H - HEIGHT))

        render_battle_scene(screen, cam_x, cam_y)

        # ── 2회차 mon 출현 처리 ──
        if game_state == "battle_2" and battle_2_mon_appeared:
            elapsed_mon = current_time - battle_2_mon_appear_start
            mon_alpha = min(255, int(255 * elapsed_mon / BATTLE_2_MON_APPEAR_MS))

            # 카메라 복귀 중/완료 시 mon 서서히 사라짐
            if battle_2_cam_returning:
                rt = min(1.0, (current_time - battle_2_cam_return_start) / BATTLE_2_CAM_RETURN_MS)
                mon_alpha = int(255 * (1.0 - rt))
            elif not battle_2_cam_locked:
                mon_alpha = 0

            if mon_alpha > 0:
                _draw_mon_on_battle(screen, cam_x, cam_y, alpha_override=mon_alpha)

            # 카메라 복귀 완료 후: 플레이어가 mon 월드 위치에 접근하면 프롬프트
            dist_mon = math.hypot(player.world_x - MON_WORLD_X, player.world_y - MON_WORLD_Y)
            mon_sx_screen = MON_WORLD_X - cam_x
            mon_sy_screen = MON_WORLD_Y - cam_y

            if not battle_2_cam_locked and not battle_2_mon_approached:
                if dist_mon < MON_INTERACT_RADIUS:
                    draw_interact_prompt(screen, "이상현상 파악하기  [E]", mon_sx_screen, mon_sy_screen)
                draw_mission(screen, MISSION_MON_APPROACH)

                e_now_b = pygame.key.get_pressed()[pygame.K_e]
                if e_now_b and not e_prev and dist_mon < MON_INTERACT_RADIUS:
                    battle_2_mon_approached = True
                    mon_approach_dlg = DialogSystem(MON_APPROACH_DIALOG_2)
                    game_state = "battle_2_mon_dlg"
                e_prev = pygame.key.get_pressed()[pygame.K_e]
        else:
            remaining = sum(1 for e in enemies if not e.is_dead)
            draw_mission(screen, f"{MISSION_BATTLE}  ({remaining}명 남음)")

        mx, my = pygame.mouse.get_pos()
        wx, wy = mx + cam_x, my + cam_y
        dbg = font_mini.render(f"world: ({wx}, {wy})  screen: ({mx}, {my})", True, (255, 255, 0))
        screen.blit(dbg, (10, HEIGHT - 22))

        if debug_menu_open: _draw_debug_menu(screen, debug_cursor)
        pygame.display.flip(); clock.tick(60); continue

    # ── 2회차 mon 접근 대화 ──
    if game_state == "battle_2_mon_dlg":
        if mon_approach_dlg: mon_approach_dlg.update(current_time)

        target_cam_x = max(0, min(MON_WORLD_X - WIDTH//2,  BATTLE_MAP_W - WIDTH))
        target_cam_y = max(0, min(MON_WORLD_Y - HEIGHT//2, BATTLE_MAP_H - HEIGHT))
        render_battle_scene(screen, target_cam_x, target_cam_y, show_player=True)
        _draw_mon_on_battle(screen, target_cam_x, target_cam_y)

        if mon_approach_dlg: mon_approach_dlg.draw(screen, current_time)
        if debug_menu_open: _draw_debug_menu(screen, debug_cursor)
        pygame.display.flip(); clock.tick(60); continue

    # ── 1회차 전투 클리어 페이드 ──
    if game_state == "battle_clear_fadeout":
        elapsed = current_time - battle_clear_fadeout_start
        alpha   = min(255, int(255 * elapsed / BATTLE_CLEAR_FADEOUT_DURATION))
        cam_x = max(0, min(int(player.world_x)-WIDTH//2,  BATTLE_MAP_W-WIDTH))
        cam_y = max(0, min(int(player.world_y)-HEIGHT//2, BATTLE_MAP_H-HEIGHT))
        render_battle_scene(screen, cam_x, cam_y)
        draw_fadeout(screen, alpha)
        if elapsed >= BATTLE_CLEAR_FADEOUT_DURATION:
            game_state = "post_battle_prefect"
            player.hina_sx = 500.0; player.hina_sy = 560.0
            player.costume = "uniform"
            aco_clear_talked = False; aco_clear_dlg = None
            play_funky_road()
        if debug_menu_open: _draw_debug_menu(screen, debug_cursor)
        pygame.display.flip(); clock.tick(60); continue

    # ── 1회차 클리어 후 선도부실 ──
    if game_state == "post_battle_prefect":
        keys = pygame.key.get_pressed()
        player.update_prefect_room(keys, current_time)
        e_now = keys[pygame.K_e]
        dist_aco = math.hypot(player.hina_sx-ACO_SCREEN_POS[0], player.hina_sy-ACO_SCREEN_POS[1])
        near_aco = dist_aco < ACO_INTERACT_RADIUS and not aco_clear_talked
        if e_now and not e_prev and near_aco:
            aco_clear_dlg = DialogSystem(ACO_CLEAR_DIALOG)
            game_state    = "post_battle_aco_dlg"
        e_prev = e_now
        mission_txt = None if aco_clear_talked else MISSION_AFTER_BATTLE
        draw_prefect_room(screen, player, current_time, near_aco=near_aco, mission=mission_txt)
        if debug_menu_open: _draw_debug_menu(screen, debug_cursor)
        pygame.display.flip(); clock.tick(60); continue

    if game_state == "post_battle_aco_dlg":
        if aco_clear_dlg: aco_clear_dlg.update(current_time)
        screen.fill((0, 0, 0))
        if prefect_room_img: screen.blit(prefect_room_img, prefect_room_rect)
        if aco_img:
            screen.blit(aco_img, (ACO_SCREEN_POS[0]-ACO_DRAW_W//2, ACO_SCREEN_POS[1]-ACO_DRAW_H//2))
        else:
            pygame.draw.circle(screen, (180, 120, 220), ACO_SCREEN_POS, 28)
        player.draw(screen, int(player.hina_sx), int(player.hina_sy), current_time)
        if aco_clear_dlg: aco_clear_dlg.draw(screen, current_time)
        if debug_menu_open: _draw_debug_menu(screen, debug_cursor)
        pygame.display.flip(); clock.tick(60); continue

    # ─────────────────────────────────────────
    # ── 피아노 방 ──
    # ─────────────────────────────────────────
    if game_state in ("piano_room", "piano_enter_dlg", "piano_interact_dlg"):
        elapsed = current_time - piano_room_fadeout_start

        # ── 이동은 대화 여부와 상관없이 항상 처리 ──
        keys = pygame.key.get_pressed()
        if game_state == "piano_room":
            player.update_piano_room(keys, current_time)
            e_now = keys[pygame.K_e]
            dist_piano = math.hypot(player.hina_sx - PIANO_INTERACT_POS[0],
                                    player.hina_sy - PIANO_INTERACT_POS[1])
            near_piano = dist_piano < PIANO_INTERACT_RADIUS and not piano_interacted and piano_enter_done
            if e_now and not e_prev and near_piano:
                piano_interacted   = True
                piano_interact_dlg = DialogSystem(PIANO_INTERACT_DIALOG)
                game_state = "piano_interact_dlg"
            e_prev = e_now
        else:
            e_prev = False

        # ── 페이드인이 끝나면 입장 대화 시작 (한 번만) ──
        if game_state == "piano_room" and not piano_enter_done and piano_enter_dlg is None:
            if elapsed >= PIANO_ROOM_FADEIN_DURATION:
                piano_enter_dlg = DialogSystem(PIANO_ROOM_ENTER_DIALOG)
                game_state = "piano_enter_dlg"

        # ── 배경 + 히나 ──
        screen.fill((0, 0, 0))
        if piano_room_img:
            screen.blit(piano_room_img, piano_room_rect)
        else:
            screen.fill((15, 10, 25))
            lbl = font_medium.render("피아노 방", True, (200, 180, 255))
            screen.blit(lbl, lbl.get_rect(center=(WIDTH//2, HEIGHT//2)))

        player.draw(screen, int(player.hina_sx), int(player.hina_sy), current_time)

        # ── 피아노 근처 프롬프트 + 미션 ──
        if game_state == "piano_room" and piano_enter_done and not piano_interacted:
            dist_piano = math.hypot(player.hina_sx - PIANO_INTERACT_POS[0],
                                    player.hina_sy - PIANO_INTERACT_POS[1])
            if dist_piano < PIANO_INTERACT_RADIUS:
                draw_interact_prompt(screen, "악보를 넘기기  [E]",
                                     PIANO_INTERACT_POS[0], PIANO_INTERACT_POS[1])
            draw_mission(screen, MISSION_PIANO_ROOM)

        # ── 워크존 디버그 ──
        if len(_PIANO_WALK_POLY) >= 2:
            pygame.draw.polygon(screen, (255, 100, 0), _PIANO_WALK_POLY, 2)
            for pt in _PIANO_WALK_POLY:
                pygame.draw.circle(screen, (255, 200, 0), pt, 5)

        # ── 페이드인 ──
        if elapsed < PIANO_ROOM_FADEIN_DURATION:
            fade_alpha = int(255 * (1.0 - elapsed / PIANO_ROOM_FADEIN_DURATION))
            draw_fadeout(screen, fade_alpha)

        # ── 대화창 ──
        if game_state == "piano_enter_dlg":
            if piano_enter_dlg: piano_enter_dlg.update(current_time)
            if piano_enter_dlg: piano_enter_dlg.draw(screen, current_time)
        elif game_state == "piano_interact_dlg":
            if piano_interact_dlg: piano_interact_dlg.update(current_time)
            if piano_interact_dlg: piano_interact_dlg.draw(screen, current_time)

        mx, my = pygame.mouse.get_pos()
        dbg = font_mini.render(f"mouse: ({mx}, {my})", True, (255, 255, 0))
        screen.blit(dbg, (10, 40))

        if debug_menu_open: _draw_debug_menu(screen, debug_cursor)
        pygame.display.flip(); clock.tick(60); continue

    # ─────────────────────────────────────────
    # ── 피아노 방 → ml_room 페이드아웃 ──
    # ─────────────────────────────────────────
    if game_state == "to_ml_room_fadeout":
        elapsed = current_time - ml_room_fadeout_start
        alpha   = min(255, int(255 * elapsed / FADEOUT_DURATION))
        # 피아노 방 배경 유지
        screen.fill((0, 0, 0))
        if piano_room_img:
            screen.blit(piano_room_img, piano_room_rect)
        player.draw(screen, int(player.hina_sx), int(player.hina_sy), current_time)
        draw_fadeout(screen, alpha)
        if elapsed >= FADEOUT_DURATION:
            game_state = "ml_room"
            ml_room_fadeout_start = current_time
            ml_room_cam_x = 0
            ml_room_cam_y = 0
        if debug_menu_open: _draw_debug_menu(screen, debug_cursor)
        pygame.display.flip(); clock.tick(60); continue

    # ─────────────────────────────────────────
    # ── ml_room 씬 ──
    # 검정 → 이미지 페이드인 → 챕터 타이틀 연출 → 타이틀로
    # ─────────────────────────────────────────
    if game_state == "ml_room":
        elapsed = current_time - ml_room_fadeout_start

        # 배경 그리기
        screen.fill((0, 0, 0))
        if ml_room_img:
            screen.blit(ml_room_img, (-ml_room_cam_x, -ml_room_cam_y))
        else:
            # 폴백: 어두운 파란 화면
            screen.fill((8, 12, 30))
            lbl = font_medium.render("MILLENNIUM", True, (100, 160, 255))
            screen.blit(lbl, lbl.get_rect(center=(WIDTH//2, HEIGHT//2)))

        # 페이드인
        if elapsed < ML_ROOM_FADEIN_MS:
            fade_alpha = int(255 * (1.0 - elapsed / ML_ROOM_FADEIN_MS))
            draw_fadeout(screen, fade_alpha)

        # 페이드인 끝나면 챕터 타이틀 연출 시작
        if elapsed >= ML_ROOM_FADEIN_MS and chapter_title_phase == "black":
            chapter_title_phase       = "ch1_in"
            chapter_title_phase_start = current_time

        # ── 챕터 타이틀 그리기 ──
        font_chapter = _make_font(52, bold=True)
        font_chapter_sub = _make_font(28)

        def _draw_chapter_title(txt_main, txt_sub, alpha_val):
            """챕터 제목 + 부제 중앙에 그리기"""
            s_main = font_chapter.render(txt_main, True, (230, 215, 180))
            s_sub  = font_chapter_sub.render(txt_sub,  True, (180, 170, 140))
            s_main.set_alpha(alpha_val)
            s_sub.set_alpha(alpha_val)
            cy = HEIGHT // 2
            screen.blit(s_main, s_main.get_rect(center=(WIDTH//2, cy - 28)))
            screen.blit(s_sub,  s_sub.get_rect( center=(WIDTH//2, cy + 32)))

        t_phase = current_time - chapter_title_phase_start

        if chapter_title_phase == "ch1_in":
            a = int(255 * min(1.0, t_phase / CH_FADE_IN_MS))
            _draw_chapter_title("1장", "게헨나", a)
            if t_phase >= CH_FADE_IN_MS:
                chapter_title_phase       = "ch1_hold"
                chapter_title_phase_start = current_time

        elif chapter_title_phase == "ch1_hold":
            _draw_chapter_title("1장", "게헨나", 255)
            if t_phase >= CH_HOLD_MS:
                chapter_title_phase       = "ch1_out"
                chapter_title_phase_start = current_time

        elif chapter_title_phase == "ch1_out":
            a = int(255 * max(0.0, 1.0 - t_phase / CH_FADE_OUT_MS))
            _draw_chapter_title("1장", "게헨나", a)
            if t_phase >= CH_FADE_OUT_MS:
                chapter_title_phase       = "ch1_gap"
                chapter_title_phase_start = current_time

        elif chapter_title_phase == "ch1_gap":
            # 아무것도 안 그림 (잠깐 공백)
            if t_phase >= CH_GAP_MS:
                chapter_title_phase       = "ch2_in"
                chapter_title_phase_start = current_time

        elif chapter_title_phase == "ch2_in":
            a = int(255 * min(1.0, t_phase / CH_FADE_IN_MS))
            _draw_chapter_title("2장", "밀레니엄", a)
            if t_phase >= CH_FADE_IN_MS:
                chapter_title_phase       = "ch2_hold"
                chapter_title_phase_start = current_time

        elif chapter_title_phase == "ch2_hold":
            _draw_chapter_title("2장", "밀레니엄", 255)
            if t_phase >= CH_HOLD_MS:
                chapter_title_phase       = "to_title"
                chapter_title_phase_start = current_time

        elif chapter_title_phase == "to_title":
            # 2장 타이틀 페이드아웃 + 화면 전체 검정으로
            a_title = int(255 * max(0.0, 1.0 - t_phase / CH_FADE_OUT_MS))
            _draw_chapter_title("2장", "밀레니엄", a_title)
            # 화면 전체 페이드아웃
            fade_a = int(255 * min(1.0, t_phase / (CH_FADE_OUT_MS + CH_TO_TITLE_FADEIN_MS)))
            draw_fadeout(screen, fade_a)
            if t_phase >= CH_FADE_OUT_MS + CH_TO_TITLE_FADEIN_MS:
                # 타이틀로 복귀 — 전체 상태 리셋
                game_state = "title"
                pygame.mixer.music.stop()
                hina_bgm_started   = False
                battle_bgm_started = False
                cycle = 1
                # 챕터 phase 초기화 (다음 플레이 대비)
                chapter_title_phase = "black"

        if debug_menu_open: _draw_debug_menu(screen, debug_cursor)
        pygame.display.flip(); clock.tick(60); continue


    # ─────────────────────────────────────────
    if game_state == "battle_3_pre_dlg":
        if aco_clear_dlg_3_pre: aco_clear_dlg_3_pre.update(current_time)
        cam_x = max(0, min(int(player.world_x)-WIDTH//2,  BATTLE_MAP_W-WIDTH))
        cam_y = max(0, min(int(player.world_y)-HEIGHT//2, BATTLE_MAP_H-HEIGHT))
        render_battle_scene(screen, cam_x, cam_y)
        if aco_clear_dlg_3_pre: aco_clear_dlg_3_pre.draw(screen, current_time)
        if debug_menu_open: _draw_debug_menu(screen, debug_cursor)
        pygame.display.flip(); clock.tick(60); continue

    # ─────────────────────────────────────────
    # ── 3회차 카메라 시네마틱 + mon 출현 ──
    # ─────────────────────────────────────────
    if game_state == "battle_3_cam_cinematic":
        elapsed = current_time - cam_cinematic_start
        t = min(1.0, elapsed / CAM_CINEMATIC_DURATION)
        t_ease = t * t * (3 - 2 * t)

        start_cam_x = max(0, min(int(player.world_x)-WIDTH//2,  BATTLE_MAP_W-WIDTH))
        start_cam_y = max(0, min(int(player.world_y)-HEIGHT//2, BATTLE_MAP_H-HEIGHT))
        target_cam_x = max(0, min(MON_WORLD_X - WIDTH//2,  BATTLE_MAP_W-WIDTH))
        target_cam_y = max(0, min(MON_WORLD_Y - HEIGHT//2, BATTLE_MAP_H-HEIGHT))

        cam_x = int(start_cam_x + (target_cam_x - start_cam_x) * t_ease)
        cam_y = int(start_cam_y + (target_cam_y - start_cam_y) * t_ease)

        render_battle_scene(screen, cam_x, cam_y, show_player=True)

        if t_ease > 0.6 and mon_map_img:
            mon_alpha = int(255 * min(1.0, (t_ease - 0.6) / 0.4))
            _draw_mon_on_battle(screen, cam_x, cam_y, alpha_override=mon_alpha)

        vign_alpha = int(120 * t_ease)
        vign = pygame.Surface((WIDTH, HEIGHT), pygame.SRCALPHA)
        for i in range(4):
            thick = 60 - i * 14
            a = max(0, vign_alpha - i * 25)
            pygame.draw.rect(vign, (150, 10, 10, a), (0, 0, WIDTH, HEIGHT), thick)
        screen.blit(vign, (0, 0))

        if t >= 1.0:
            game_state = "battle_3_mon_dlg"
            aco_clear_dlg_3_mon = DialogSystem(ACO_CLEAR_DIALOG_3_MON)
            mon_revealed = True

        if debug_menu_open: _draw_debug_menu(screen, debug_cursor)
        pygame.display.flip(); clock.tick(60); continue

    # ─────────────────────────────────────────
    # ── 3회차 mon 등장 대화 ──
    # ─────────────────────────────────────────
    if game_state == "battle_3_mon_dlg":
        if aco_clear_dlg_3_mon: aco_clear_dlg_3_mon.update(current_time)
        target_cam_x = max(0, min(MON_WORLD_X - WIDTH//2,  BATTLE_MAP_W-WIDTH))
        target_cam_y = max(0, min(MON_WORLD_Y - HEIGHT//2, BATTLE_MAP_H-HEIGHT))
        render_battle_scene(screen, target_cam_x, target_cam_y, show_player=True)
        _draw_mon_on_battle(screen, target_cam_x, target_cam_y)
        _draw_vignette(screen, 100)
        if aco_clear_dlg_3_mon: aco_clear_dlg_3_mon.draw(screen, current_time)
        if debug_menu_open: _draw_debug_menu(screen, debug_cursor)
        pygame.display.flip(); clock.tick(60); continue

    if game_state == "battle_3_mon_dlg_done":
        target_cam_x = max(0, min(MON_WORLD_X - WIDTH//2,  BATTLE_MAP_W-WIDTH))
        target_cam_y = max(0, min(MON_WORLD_Y - HEIGHT//2, BATTLE_MAP_H-HEIGHT))
        render_battle_scene(screen, target_cam_x, target_cam_y)
        _draw_mon_on_battle(screen, target_cam_x, target_cam_y)
        _draw_vignette(screen, 100)

        tbc_font = _make_font(36, bold=True)
        tbc_surf = tbc_font.render("— TO BE CONTINUED —", True, (220, 200, 150))
        tbc_alpha = int(128 + 64 * math.sin(current_time / 600.0))
        tbc_surf.set_alpha(tbc_alpha)
        screen.blit(tbc_surf, tbc_surf.get_rect(center=(WIDTH//2, HEIGHT//2 + 220)))

        if debug_menu_open: _draw_debug_menu(screen, debug_cursor)
        pygame.display.flip(); clock.tick(60); continue

    # 미정의 상태 폴백
    game_state = "battle"

pygame.quit()
sys.exit()