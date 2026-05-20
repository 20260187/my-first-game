import pygame
import random
import sys
import os

# --- 초기화 ---
pygame.init()
pygame.mixer.init()

# --- 상대 경로 및 소리 설정 ---
BASE_PATH = os.path.dirname(__file__)
SOUND_PATH = os.path.join(BASE_PATH, "eat_sound.mp3")
eat_sound = pygame.mixer.Sound(SOUND_PATH) if os.path.exists(SOUND_PATH) else None

def play_eat_sound():
    if eat_sound: eat_sound.play()

# --- 화면 크기 설정 ---
WIDTH, HEIGHT = 910, 700 
screen = pygame.display.set_mode((WIDTH, HEIGHT))
pygame.display.set_caption("MORE APPLES")
clock = pygame.time.Clock()

# 폰트
font_num = pygame.font.SysFont("arial", 22, bold=True)
font_ui = pygame.font.SysFont("malgungothic", 25, bold=True)
font_big = pygame.font.SysFont("malgungothic", 65, bold=True)

# 영역 정의
UPPER_HEIGHT = 380
UPPER_RECT = pygame.Rect(0, 0, WIDTH, UPPER_HEIGHT) 
LOWER_RECT = pygame.Rect(0, UPPER_HEIGHT, WIDTH, HEIGHT - UPPER_HEIGHT)

# 색상
BLACK, WHITE = (15, 15, 15), (250, 250, 250)
RED, GREEN = (230, 50, 50), (50, 230, 80)
GRAY = (100, 100, 100)
YELLOW = (255, 220, 0)
BG_COLOR1 = (170, 215, 81)
BG_COLOR2 = (162, 209, 73)
SNAKE_BLUE = (66, 133, 244)
EYE_WHITE = (255, 255, 255)
EYE_BLACK = (0, 0, 0)

# 전역 변수
CELL = 20 
apples = []        
lower_apple = None 
snake = []
direction = (CELL, 0)
next_direction = (CELL, 0) 
growth_queue = 0
total_score = 0 
game_over = False
game_started = False
GAME_FPS = 10 
frame_count = 0 

# 사과 그리기 함수 (아래 스네이크 게임용)
def draw_apple_shape(rect):
    center = rect.center
    radius = rect.width // 2 - 2
    pygame.draw.circle(screen, RED, center, radius)
    leaf_rect = pygame.Rect(center[0] - 2, rect.top + 2, 6, 6)
    pygame.draw.rect(screen, GREEN, leaf_rect, border_radius=2)

def spawn_lower_apple():
    global lower_apple
    cols = WIDTH // CELL
    rows = LOWER_RECT.height // CELL
    x = random.randrange(0, cols) * CELL
    y = (random.randrange(0, rows) + (LOWER_RECT.top // CELL)) * CELL
    lower_apple = pygame.Rect(x, y, CELL, CELL)

def reset_game():
    global apples, snake, direction, next_direction, growth_queue, total_score, game_over, game_started, frame_count
    apples = []
    apple_size = 45

    # ★ 수정: 상단 영역(UPPER_HEIGHT) 전체를 균등하게 사용하도록 패딩 적용
    pad_x = (WIDTH % apple_size) // 2
    pad_y = (UPPER_HEIGHT % apple_size) // 2
    cols = WIDTH // apple_size
    rows = UPPER_HEIGHT // apple_size
    for r in range(rows):
        for c in range(cols):
            apples.append({
                "rect": pygame.Rect(pad_x + c*apple_size + 5, pad_y + r*apple_size + 5, apple_size-10, apple_size-10),
                "num": random.randint(1, 9),
                "alive": True
            })

    start_x = (WIDTH // 2 // CELL) * CELL
    start_y = ((LOWER_RECT.top + 100) // CELL) * CELL
    snake = [pygame.Rect(start_x, start_y, CELL, CELL)]
    direction = (CELL, 0); next_direction = (CELL, 0)
    growth_queue = 0; total_score = 0; game_over = False; game_started = False 
    frame_count = 0
    spawn_lower_apple()

# ★ 수정: 이파리 추가된 상단 숫자 사과 그리기
def draw_number_apple(a):
    rect = a["rect"]
    cx = rect.centerx

    # 줄기
    pygame.draw.line(screen, (80, 160, 40), (cx, rect.top + 4), (cx, rect.top - 2), 2)
    # 이파리 (타원)
    leaf_rect = pygame.Rect(cx - 1, rect.top - 6, 10, 7)
    pygame.draw.ellipse(screen, BG_COLOR2, leaf_rect)

    # 사과 본체
    pygame.draw.rect(screen, RED, rect, border_radius=8)

    # 숫자
    num_surf = font_num.render(str(a["num"]), True, WHITE)
    screen.blit(num_surf, (rect.centerx - 7, rect.centery - 10))

def draw_start_screen():
    screen.fill(BLACK)
    title = font_big.render("MORE APPLES", True, GREEN)
    subtitle = font_ui.render("SELECT DIFFICULTY", True, WHITE)
    mode1 = font_ui.render("1. NORMAL (Speed x1)", True, WHITE)
    mode2 = font_ui.render("2. HARD (Speed x2)", True, RED)
    tip = font_ui.render("Press the Number Key to Start", True, YELLOW)
    screen.blit(title, (WIDTH//2 - title.get_width()//2, 160))
    screen.blit(subtitle, (WIDTH//2 - subtitle.get_width()//2, 300))
    screen.blit(mode1, (WIDTH//2 - mode1.get_width()//2, 380))
    screen.blit(mode2, (WIDTH//2 - mode2.get_width()//2, 440))
    screen.blit(tip, (WIDTH//2 - tip.get_width()//2, 580))

def draw_lower_background():
    for row in range(LOWER_RECT.height // CELL):
        for col in range(WIDTH // CELL):
            color = BG_COLOR1 if (row + col) % 2 == 0 else BG_COLOR2
            pygame.draw.rect(screen, color, (col * CELL, LOWER_RECT.top + row * CELL, CELL, CELL))

reset_game()
dragging = False
drag_start, drag_end = (0, 0), (0, 0)

while True:
    if not game_started:
        clock.tick(60); draw_start_screen()
        for e in pygame.event.get():
            if e.type == pygame.QUIT: pygame.quit(); sys.exit()
            if e.type == pygame.KEYDOWN:
                if e.key in [pygame.K_1, pygame.K_2]:
                    GAME_FPS = 10 if e.key == pygame.K_1 else 20
                    game_started = True
        pygame.display.flip(); continue

    if not game_over: 
        clock.tick(GAME_FPS); frame_count += 1
    else: clock.tick(60)

    screen.fill(BLACK)
    draw_lower_background()

    for e in pygame.event.get():
        if e.type == pygame.QUIT: pygame.quit(); sys.exit()
        if not game_over:
            if e.type == pygame.MOUSEBUTTONDOWN and UPPER_RECT.collidepoint(e.pos):
                dragging, drag_start = True, e.pos
            if e.type == pygame.MOUSEBUTTONUP and dragging:
                drag_rect = pygame.Rect(min(drag_start[0], drag_end[0]), min(drag_start[1], drag_end[1]), 
                                        abs(drag_start[0] - drag_end[0]), abs(drag_start[1] - drag_end[1]))
                selected = [a for a in apples if a["alive"] and drag_rect.colliderect(a["rect"])]
                if sum(a["num"] for a in selected) == 10:
                    for a in selected: a["alive"] = False
                    total_score += len(selected); growth_queue += len(selected)
                    play_eat_sound()
                dragging = False
            if e.type == pygame.MOUSEMOTION and dragging: drag_end = e.pos
            if e.type == pygame.KEYDOWN:
                if e.key == pygame.K_w and direction != (0, CELL): next_direction = (0, -CELL)
                if e.key == pygame.K_s and direction != (0, -CELL): next_direction = (0, CELL)
                if e.key == pygame.K_a and direction != (CELL, 0): next_direction = (-CELL, 0)
                if e.key == pygame.K_d and direction != (-CELL, 0): next_direction = (CELL, 0)
        else:
            if e.type == pygame.KEYDOWN:
                if e.key == pygame.K_r: reset_game()
                if e.key == pygame.K_q: pygame.quit(); sys.exit()

    if not game_over:
        direction = next_direction; new_head = snake[0].copy()
        new_head.x += direction[0]; new_head.y += direction[1]
        if not LOWER_RECT.contains(new_head) or any(s.colliderect(new_head) for s in snake):
            game_over = True
        else:
            snake.insert(0, new_head)
            if new_head.colliderect(lower_apple):
                total_score += 1; growth_queue += 1; spawn_lower_apple()
                play_eat_sound()
            if growth_queue > 0: growth_queue -= 1
            else: snake.pop()

    # 상단 숫자 사과 그리기
    for a in apples:
        if a["alive"]: draw_number_apple(a)

    if dragging:
        curr_rect = pygame.Rect(min(drag_start[0], drag_end[0]), min(drag_start[1], drag_end[1]), 
                                abs(drag_start[0] - drag_end[0]), abs(drag_start[1] - drag_end[1]))
        pygame.draw.rect(screen, WHITE, curr_rect, 2)

    pygame.draw.line(screen, GRAY, (0, UPPER_RECT.bottom), (WIDTH, UPPER_RECT.bottom), 4)
    # 하단 사과 그리기
    draw_apple_shape(lower_apple)
    
    # 뱀 그리기
    for i, s in enumerate(snake):
        pygame.draw.rect(screen, SNAKE_BLUE, s, border_radius=5)
        if i == 0:
            eye_size, off_x, off_y = CELL // 5, CELL // 4, CELL // 3
            def get_eye(base, ox, oy, dx, dy):
                if dx > 0: return (base.right - ox, base.top + oy), (base.right - ox, base.bottom - oy)
                elif dx < 0: return (base.left + ox, base.top + oy), (base.left + ox, base.bottom - oy)
                elif dy > 0: return (base.left + oy, base.bottom - ox), (base.right - oy, base.bottom - ox)
                else: return (base.left + oy, base.top + ox), (base.right - oy, base.top + ox)
            e1, e2 = get_eye(s, off_x, off_y, direction[0], direction[1])
            pygame.draw.circle(screen, EYE_WHITE, e1, eye_size); pygame.draw.circle(screen, EYE_WHITE, e2, eye_size)
            pygame.draw.circle(screen, EYE_BLACK, e1, eye_size // 1.5); pygame.draw.circle(screen, EYE_BLACK, e2, eye_size // 1.5)

    if game_over:
        overlay = pygame.Surface((WIDTH, HEIGHT), pygame.SRCALPHA)
        overlay.fill((0, 0, 0, 230)); screen.blit(overlay, (0, 0))
        res_title = font_big.render("GAME OVER", True, RED)
        score_txt = font_big.render(f"Final Length: {len(snake)}m", True, YELLOW)
        restart_txt = font_ui.render("R: Restart / Q: Quit", True, WHITE)
        screen.blit(res_title, (WIDTH//2 - res_title.get_width()//2, 180))
        screen.blit(score_txt, (WIDTH//2 - score_txt.get_width()//2, 330))
        screen.blit(restart_txt, (WIDTH//2 - restart_txt.get_width()//2, 480))
        
    pygame.display.flip()