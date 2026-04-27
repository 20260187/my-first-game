import pygame
import sys

pygame.init()
screen = pygame.display.set_mode((800, 600))
pygame.display.set_caption("My First Pygame")

WHITE = (255, 255, 255)
BLUE = (0, 0, 255)
clock = pygame.time.Clock()

x, y = 400, 300  # 원의 위치 [cite: 174]
speed = 5        # 이동 속도 [cite: 144]

running = True
while running:
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running = False

    # 키보드 입력 처리 [cite: 175]
    keys = pygame.key.get_pressed()
    if keys[pygame.K_LEFT]: x -= speed
    if keys[pygame.K_RIGHT]: x += speed
    if keys[pygame.K_UP]: y -= speed
    if keys[pygame.K_DOWN]: y += speed

    # 화면 그리기 [cite: 36, 37, 38]
    screen.fill(WHITE)
    pygame.draw.circle(screen, BLUE, (x, y), 50)
    pygame.display.flip()
    clock.tick(60)

pygame.quit()
sys.exit()