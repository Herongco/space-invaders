import math

import pygame

GOLD = (255, 200, 60)
GOLD_LIGHT = (255, 240, 170)
EMPTY_FILL = (20, 36, 76)
EMPTY_LINE = (60, 95, 150)


def star_points(cx, cy, r, inner=0.45):
    pts = []

    for i in range(10):
        ang = -math.pi / 2 + i * math.pi / 5
        rad = r if i % 2 == 0 else r * inner
        pts.append((cx + math.cos(ang) * rad, cy + math.sin(ang) * rad))

    return pts


def draw_star(screen, cx, cy, r, filled):
    pts = star_points(cx, cy, r)

    if filled:
        pygame.draw.polygon(screen, GOLD, pts)
        pygame.draw.polygon(screen, GOLD_LIGHT, pts, 1)
    else:
        pygame.draw.polygon(screen, EMPTY_FILL, pts)
        pygame.draw.polygon(screen, EMPTY_LINE, pts, 2)


def draw_stars(screen, cx, cy, earned, size=12, total=3):
    step = size * 2 + size * 0.6
    x0 = cx - (total - 1) * step / 2

    for i in range(total):
        draw_star(screen, int(x0 + i * step), cy, size, i < earned)