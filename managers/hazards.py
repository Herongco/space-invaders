import math
import random

import pygame

LABELS = {
    "asteroids": "ASTEROID SHOWER",
    "storm": "DUST STORMS",
    "rings": "RING LASERS",
}


class Asteroid:
    def __init__(self, width):
        self.size = random.randint(30, 54)
        self.x = random.uniform(self.size, width - self.size)
        self.y = -self.size
        self.vx = random.uniform(-1.0, 1.0)
        self.vy = random.uniform(2.6, 4.6)
        self.hp = 2
        self.angle = random.uniform(0, 360)
        self.spin = random.uniform(-3, 3)
        self.alive = True
        self.base = self.make_image(self.size)

    @staticmethod
    def make_image(size):
        surf = pygame.Surface((size, size), pygame.SRCALPHA)
        c = size // 2
        pygame.draw.circle(surf, (112, 86, 68), (c, c), c - 1)
        pygame.draw.circle(surf, (160, 128, 100), (c - size // 7,
                                                   c - size // 7), c // 2)
        rng = random.Random(size * 31)
        for _ in range(3):
            r = max(2, size // rng.randint(7, 10))
            pos = (rng.randint(c - c // 2, c + c // 2),
                   rng.randint(c - c // 2, c + c // 2))
            pygame.draw.circle(surf, (78, 58, 46), pos, r)
        pygame.draw.circle(surf, (200, 160, 120), (c, c), c - 1, 2)
        return surf

    def update(self, height, width):
        self.x += self.vx
        self.y += self.vy
        self.angle += self.spin

        if self.y > height + self.size or not -80 < self.x < width + 80:
            self.alive = False

    def get_rect(self):
        s = int(self.size * 0.8)
        return pygame.Rect(self.x - s / 2, self.y - s / 2, s, s)

    def draw(self, screen):
        img = pygame.transform.rotate(self.base, self.angle)
        screen.blit(img, img.get_rect(center=(int(self.x), int(self.y))))


class RingBeam:

    WARN = 70
    FIRE = 35
    WIDTH = 56

    def __init__(self, cx, height):
        self.cx = cx
        self.height = height
        self.t = 0
        self.hit = False
        self.alive = True
        self.layer = pygame.Surface((self.WIDTH, height), pygame.SRCALPHA)
        self.layer.fill((255, 190, 80, 70))
        core = self.WIDTH // 2 - 9
        pygame.draw.rect(self.layer, (255, 235, 170, 150),
                         (core, 0, 18, height))
        pygame.draw.rect(self.layer, (255, 250, 225, 235),
                         (core + 5, 0, 8, height))

    @property
    def firing(self):
        return self.WARN <= self.t < self.WARN + self.FIRE

    def update(self):
        self.t += 1

        if self.t >= self.WARN + self.FIRE:
            self.alive = False

    def get_rect(self):
        return pygame.Rect(self.cx - self.WIDTH // 2, 0, self.WIDTH,
                           self.height)

    def draw(self, screen):
        if self.firing:
            screen.blit(self.layer, (self.cx - self.WIDTH // 2, 0))
            return

        if (self.t // 6) % 2 == 0:
            for y in range(40, self.height, 26):
                pygame.draw.line(screen, (255, 150, 70),
                                 (self.cx, y), (self.cx, y + 12), 2)

            top = [(self.cx, 8), (self.cx - 11, 28), (self.cx + 11, 28)]
            pygame.draw.polygon(screen, (255, 200, 60), top)
            pygame.draw.polygon(screen, (60, 30, 0), top, 2)
            pygame.draw.line(screen, (60, 30, 0), (self.cx, 14),
                             (self.cx, 21), 2)
            pygame.draw.circle(screen, (60, 30, 0), (self.cx, 25), 1)


class Hazards:
    def __init__(self, kind, width, height):
        self.kind = kind if kind in LABELS else None
        self.w = width
        self.h = height

        self.asteroids = []
        self.beams = []
        self.timer = 0
        self.next_spawn = 90

        self.storm_t = 0
        self.storm_len = 0
        self.wind_dir = 1
        self.intensity = 0.0
        self.dust = [[random.uniform(0, width), random.uniform(0, height),
                      random.uniform(9, 20), random.randint(10, 26)]
                     for _ in range(46)]
        self.overlay = pygame.Surface((width, height), pygame.SRCALPHA)

    @property
    def label(self):
        return LABELS.get(self.kind, "")

    def clear(self):
        self.asteroids = []
        self.beams = []
        self.storm_len = 0
        self.intensity = 0.0


    def update(self, player):
        if not self.kind:
            return None

        self.timer += 1
        notice = None

        if self.kind == "asteroids":
            if self.timer >= self.next_spawn:
                self.timer = 0
                self.next_spawn = random.randint(55, 95)
                self.asteroids.append(Asteroid(self.w))

            for a in self.asteroids:
                a.update(self.h, self.w)
            self.asteroids = [a for a in self.asteroids if a.alive]

        elif self.kind == "storm":
            notice = self.update_storm(player)

        elif self.kind == "rings":
            if self.timer >= self.next_spawn:
                self.timer = 0
                self.next_spawn = random.randint(150, 230)
                self.add_beam(player)

                if random.random() < 0.35:
                    self.add_beam(player, side=True)

            for b in self.beams:
                b.update()
            self.beams = [b for b in self.beams if b.alive]

        return notice

    def add_beam(self, player, side=False):
        aim = player.x + player.width // 2
        aim += random.randint(-70, 70) + (150 if side else 0)
        half = RingBeam.WIDTH // 2
        cx = int(max(half, min(self.w - half, aim)))
        self.beams.append(RingBeam(cx, self.h))

    def update_storm(self, player):
        notice = None

        if self.storm_len == 0:
            if self.timer >= self.next_spawn:
                self.timer = 0
                self.storm_t = 0
                self.storm_len = random.randint(260, 360)
                self.wind_dir = random.choice((-1, 1))
                notice = "DUST STORM!"
        else:
            self.storm_t += 1

            if self.storm_t >= self.storm_len:
                self.storm_len = 0
                self.timer = 0
                self.next_spawn = random.randint(360, 540)

        if self.storm_len:
            self.intensity = min(1.0, self.storm_t / 45,
                                 (self.storm_len - self.storm_t) / 45)
        else:
            self.intensity = max(0.0, self.intensity - 0.03)

        if self.intensity > 0:
            gust = 1.4 + 0.7 * math.sin(self.storm_t * 0.05)
            player.x += self.wind_dir * gust * self.intensity

            for d in self.dust:
                d[0] += self.wind_dir * d[2]
                d[1] += 1.5

                if d[0] < -30:
                    d[0] = self.w + 30
                elif d[0] > self.w + 30:
                    d[0] = -30

                if d[1] > self.h:
                    d[1] = 0

        player.keep_inside_screen()
        return notice


    def hit_by_bullets(self, bullets):
        events = []

        for bullet in bullets:
            if not bullet.is_active:
                continue

            b_rect = bullet.get_rect().inflate(-8, -8)

            for a in self.asteroids:
                if a.alive and b_rect.colliderect(a.get_rect()):
                    bullet.is_active = False
                    a.hp -= 1

                    if a.hp <= 0:
                        a.alive = False

                    events.append((a.x, a.y, not a.alive))
                    break

        self.asteroids = [a for a in self.asteroids if a.alive]
        return events

    def hits_player(self, rect):
        for a in self.asteroids:
            if a.alive and rect.colliderect(a.get_rect()):
                a.alive = False
                self.asteroids = [x for x in self.asteroids if x.alive]
                return True

        for b in self.beams:
            if b.firing and not b.hit and rect.colliderect(b.get_rect()):
                b.hit = True
                return True

        return False


    def draw(self, screen):
        for a in self.asteroids:
            a.draw(screen)

        for b in self.beams:
            b.draw(screen)

    def draw_overlay(self, screen):
        if self.kind != "storm" or self.intensity <= 0:
            return

        self.overlay.fill((200, 110, 50, int(95 * self.intensity)))
        screen.blit(self.overlay, (0, 0))

        color = (255, 205, 150)

        for x, y, speed, length in self.dust:
            end = (x - self.wind_dir * length, y - 2)
            pygame.draw.line(screen, color, (x, y), end, 2)