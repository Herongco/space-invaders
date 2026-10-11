import math
import random

import pygame


def _clamp(v, lo=0, hi=255):
    return max(lo, min(hi, int(v)))


def _norm(v):
    length = math.sqrt(sum(c * c for c in v)) or 1.0
    return tuple(c / length for c in v)


def radial_glow(radius, color, strength=1.0):
    surf = pygame.Surface((radius * 2, radius * 2))
    surf.fill((0, 0, 0))
    for i in range(radius, 0, -2):
        k = (1 - i / radius) ** 2 * strength
        col = tuple(_clamp(c * k) for c in color)
        pygame.draw.circle(surf, col, (radius, radius), i)
    return surf


def make_sphere(radius, base, bands=0, rim=(110, 190, 255), seed=1,
                glow=14, light=(-0.55, -0.6, 0.58)):
    size = 2 * (radius + glow)
    surf = pygame.Surface((size, size), pygame.SRCALPHA)
    lx, ly, lz = _norm(light)
    rng = random.Random(seed)
    p0, p1, p2 = (rng.uniform(0, 6.28) for _ in range(3))
    c = size / 2.0
    outer = (radius + glow) / radius

    for py in range(size):
        ny = (py + 0.5 - c) / radius
        for px in range(size):
            nx = (px + 0.5 - c) / radius
            d2 = nx * nx + ny * ny
            dist = math.sqrt(d2)

            if dist >= outer:
                continue

            if dist >= 1.0:
                k = 1 - (dist - 1.0) / (outer - 1.0)
                a = int(150 * k ** 2.4)
                if a > 0:
                    surf.set_at((px, py), rim + (a,))
                continue

            nz = math.sqrt(1.0 - d2)
            lam = max(0.0, nx * lx + ny * ly + nz * lz)
            shade = 0.10 + 0.95 * lam ** 0.9

            if bands:
                b = 0.5 + 0.5 * math.sin(
                    ny * bands + 1.6 * math.sin(nx * 2.2 + p0) + p1)
                tex = 0.72 + 0.28 * b
            else:
                tex = 0.86 + 0.14 * math.sin(nx * 6 + p0) * math.sin(
                    ny * 5 + p2)

            fres = (1 - nz) ** 3
            r = base[0] * shade * tex + rim[0] * fres * (0.25 + lam) * 0.8
            g = base[1] * shade * tex + rim[1] * fres * (0.25 + lam) * 0.8
            bl = base[2] * shade * tex + rim[2] * fres * (0.25 + lam) * 0.8

            surf.set_at((px, py), (_clamp(r), _clamp(g), _clamp(bl), 255))

    return surf


def make_ringed(radius, base, ring_color, tilt=-18, seed=3):
    sphere = make_sphere(radius, base, bands=6, seed=seed, glow=8)
    cw = int(radius * 5.4)
    ch = int(radius * 5.4)
    cx, cy = cw // 2, ch // 2

    def ring_rects():
        n = 9
        for k in range(n):
            t = k / (n - 1)
            a = radius * (1.45 + 0.75 * t)
            b = a * 0.26
            yield t, pygame.Rect(cx - a, cy - b, a * 2, b * 2)

    canvas = pygame.Surface((cw, ch), pygame.SRCALPHA)

    for t, rect in ring_rects():
        fade = 150 + int(90 * math.sin(t * math.pi))
        col = tuple(_clamp(v * (0.7 + 0.3 * t)) for v in ring_color) + (fade,)
        pygame.draw.ellipse(canvas, col, rect, 3)

    canvas.blit(sphere, sphere.get_rect(center=(cx, cy)))

    for t, rect in ring_rects():
        fade = 150 + int(90 * math.sin(t * math.pi))
        col = tuple(_clamp(v * (0.7 + 0.3 * t)) for v in ring_color) + (fade,)
        pygame.draw.arc(canvas, col, rect, math.pi, math.tau, 3)

    return pygame.transform.rotate(canvas, -tilt)


_SHIP_V = {
    "N": (0, 3.2, 0), "T": (0, 0.6, 0.55), "B": (0, 0.6, -0.35),
    "L": (-0.55, 0.6, 0), "R": (0.55, 0.6, 0),
    "T2": (0, -1.8, 0.4), "B2": (0, -1.8, -0.3),
    "L2": (-0.5, -1.8, 0), "R2": (0.5, -1.8, 0),
    "WRf": (0.5, 0.4, 0.06), "WRt": (3.1, -1.7, 0.02),
    "WRr": (0.5, -1.6, 0.06),
    "WLf": (-0.5, 0.4, 0.06), "WLt": (-3.1, -1.7, 0.02),
    "WLr": (-0.5, -1.6, 0.06),
    "FRa": (3.1, -1.7, 0.02), "FRb": (3.1, -2.1, 0.02),
    "FRc": (3.1, -1.7, 0.75),
    "FLa": (-3.1, -1.7, 0.02), "FLb": (-3.1, -2.1, 0.02),
    "FLc": (-3.1, -1.7, 0.75),
}

_SHIP_F = [
    (("N", "T", "R"), (110, 160, 235)), (("N", "R", "B"), (70, 110, 200)),
    (("N", "B", "L"), (70, 110, 200)), (("N", "L", "T"), (110, 160, 235)),
    (("T", "R", "R2"), (95, 140, 225)), (("T", "R2", "T2"), (95, 140, 225)),
    (("R", "B", "B2"), (60, 95, 185)), (("R", "B2", "R2"), (60, 95, 185)),
    (("B", "L", "L2"), (60, 95, 185)), (("B", "L2", "B2"), (60, 95, 185)),
    (("L", "T", "T2"), (95, 140, 225)), (("L", "T2", "L2"), (95, 140, 225)),
    (("T2", "R2", "B2"), (40, 70, 150)), (("T2", "B2", "L2"), (40, 70, 150)),
    (("WRf", "WRt", "WRr"), (90, 150, 245)),
    (("WLf", "WLt", "WLr"), (90, 150, 245)),
    (("FRa", "FRb", "FRc"), (120, 200, 255)),
    (("FLa", "FLb", "FLc"), (120, 200, 255)),
]


class Space3D:
    UNIT = 100
    DEPTH = 8.0

    def __init__(self, w, h):
        self.w, self.h = w, h
        self.cx, self.cy = w / 2, h / 2
        self.UNIT = 100 * w / 800
        self.rng = random.Random(11)
        self.t = 0.0
        self.mx = 0.0
        self.my = 0.0
        self.camx = 0.0
        self.camy = 0.0
        self.last = pygame.time.get_ticks()
        self._still = None

        self._build_backdrop()
        self._build_stars()
        self._build_sparkles()
        self._build_planets()
        self._build_vignette()
        self._ship_glow = radial_glow(46, (40, 170, 255), 1.0)

    def _build_backdrop(self):
        w, h = self.w, self.h
        bw, bh = int(w * 1.25), int(h * 1.25)
        self.bw, self.bh = bw, bh

        back = pygame.Surface((bw, bh))
        top, mid, bot = (2, 5, 34), (10, 24, 112), (8, 40, 150)

        for y in range(bh):
            t = y / (bh - 1)
            if t < 0.55:
                a, b, k = top, mid, t / 0.55
            else:
                a, b, k = mid, bot, (t - 0.55) / 0.45
            col = tuple(int(a[i] + (b[i] - a[i]) * k) for i in range(3))
            pygame.draw.line(back, col, (0, y), (bw, y))

        sw, sh = bw // 6, bh // 6
        neb = pygame.Surface((sw, sh), pygame.SRCALPHA)
        palette = [(40, 80, 255), (110, 60, 240), (20, 150, 255),
                   (170, 70, 255), (50, 110, 255), (20, 60, 220)]

        for _ in range(64):
            col = self.rng.choice(palette)
            r = self.rng.randint(max(4, sw // 14), sw // 5)
            x = self.rng.randint(0, sw)
            y = self.rng.randint(0, sh)
            blob = pygame.Surface((r * 2, r * 2), pygame.SRCALPHA)

            for i in range(r, 0, -1):
                a = int(46 * (1 - i / r) ** 1.3) + 1
                pygame.draw.circle(blob, col + (a,), (r, r), i)

            neb.blit(blob, (x - r, y - r))

        neb = pygame.transform.smoothscale(neb, (bw, bh))
        back.blit(neb, (0, 0))

        for gx, gy, rad, col, st in (
                (0.10, 0.08, 230, (40, 120, 255), 0.65),
                (0.90, 0.12, 260, (70, 90, 255), 0.60),
                (0.88, 0.80, 240, (150, 60, 255), 0.55),
                (0.50, 0.96, 200, (30, 190, 255), 0.50),
                (0.12, 0.85, 200, (60, 60, 255), 0.50),
                (0.50, 0.45, 160, (40, 100, 255), 0.25)):
            glow = radial_glow(rad, col, st)
            back.blit(glow, (int(gx * bw) - rad, int(gy * bh) - rad),
                      special_flags=pygame.BLEND_RGB_ADD)

        self.backdrop = back

    def _build_stars(self):
        rng = self.rng
        self.stars = []
        for _ in range(240):
            self.stars.append(self._new_star(rng.uniform(0.08, 1.0)))

    def _new_star(self, z=1.0):
        rng = self.rng
        tint = rng.random()
        if tint < 0.12:
            col = (255, 170, 230)
        elif tint < 0.40:
            col = (130, 235, 255)
        else:
            col = (200, 220, 255)

        return [rng.uniform(-1.7, 1.7), rng.uniform(-1.3, 1.3), z,
                rng.uniform(0, 6.28), col]

    def _build_sparkles(self):
        rng = random.Random(23)
        self.sparkles = []
        for _ in range(16):
            self.sparkles.append((
                rng.uniform(0.03, 0.97), rng.uniform(0.03, 0.97),
                rng.uniform(0, 6.28), rng.uniform(5, 11),
                rng.uniform(0.6, 1.6)))

    def _build_planets(self):
        self.planets = []

        gas = make_sphere(112, (30, 70, 235), bands=8, seed=5,
                          rim=(90, 190, 255), glow=18)
        violet = make_sphere(72, (70, 45, 200), bands=5, seed=9,
                             rim=(150, 120, 255), glow=14)
        ringed = make_ringed(46, (150, 60, 235), (200, 170, 255), seed=8)
        teal = make_sphere(44, (30, 170, 230), bands=0, seed=2,
                           rim=(120, 240, 255))

        for surf, anchor, wob, speed, ph in (
                (gas, (4.3, -2.7, 1.0), (0.15, 0.12, 0.5), 0.30, 0.0),
                (violet, (-4.3, -2.5, 2.0), (0.15, 0.15, 0.5), 0.35, 1.5),
                (ringed, (-4.3, 1.9, 3.0), (0.20, 0.25, 0.6), 0.28, 2.0),
                (teal, (4.3, -0.2, 6.0), (0.30, 0.25, 0.8), 0.40, 4.0)):
            self.planets.append({
                "surf": surf, "anchor": anchor, "wob": wob,
                "speed": speed, "phase": ph, "z": anchor[2],
            })

    def _build_vignette(self):
        sw, sh = 64, 48
        small = pygame.Surface((sw, sh), pygame.SRCALPHA)
        for y in range(sh):
            for x in range(sw):
                dx = (x / (sw - 1) - 0.5) * 2
                dy = (y / (sh - 1) - 0.5) * 2
                d = min(1.0, math.sqrt(dx * dx * 0.8 + dy * dy * 0.9))
                a = int(125 * max(0.0, d - 0.45) / 0.55)
                small.set_at((x, y), (0, 0, 12, min(150, a)))
        self.vignette = pygame.transform.smoothscale(small, (self.w, self.h))

    def project(self, x, y, z):
        k = self.w * 0.30 / z
        return (self.cx + (x - self.camx) * k,
                self.cy + (y - self.camy) * k * 1.0)

    def draw(self, screen, step=True, speed=1.0, planets=True,
             vignette=True):
        now = pygame.time.get_ticks()
        dt = min(0.05, max(0.0, (now - self.last) / 1000.0))
        self.last = now
        f = dt * 60.0 if step else 0.0

        if step:
            self.t += dt

        px, py = pygame.mouse.get_pos()
        tx = (px / self.w - 0.5) * 2
        ty = (py / self.h - 0.5) * 2
        self.mx += (tx - self.mx) * 0.04
        self.my += (ty - self.my) * 0.04

        t = self.t
        self.camx = math.sin(t * 0.30) * 0.14 + self.mx * 0.30
        self.camy = math.cos(t * 0.23) * 0.10 + self.my * 0.22

        ox = -(self.bw - self.w) / 2 - self.camx * 70
        oy = -(self.bh - self.h) / 2 - self.camy * 52
        screen.blit(self.backdrop, (int(ox), int(oy)))

        self._draw_stars(screen, f, speed, far=True)

        if planets:
            self._draw_planets(screen)

        self._draw_stars(screen, f, speed, far=False)

        self._draw_sparkles(screen)

        if vignette:
            screen.blit(self.vignette, (0, 0))

    def _draw_stars(self, screen, f, speed, far):
        w, h = self.w, self.h
        t = self.t
        dz = 0.0016 * speed * f

        for star in self.stars:
            is_far = star[2] >= 0.5

            if is_far != far:
                continue

            star[2] -= dz
            z = star[2]

            if z <= 0.05:
                star[:] = self._new_star(1.0)
                continue

            sx, sy = self.project(star[0], star[1], z)

            if sx < -30 or sx > w + 30 or sy < -30 or sy > h + 30:
                star[:] = self._new_star(1.0)
                continue

            b = 1.0 - z * 0.75
            if z > 0.5:
                b *= 0.72 + 0.28 * math.sin(t * 3 + star[3] * 6)

            r, g, bl = star[4]
            col = (_clamp(r * b + 20), _clamp(g * b + 20), _clamp(bl * b + 30))

            if z < 0.45 and speed > 0:
                tx, ty = self.project(star[0], star[1], z + dz * 5 + 0.004)
                width = 1 if z > 0.25 else 2
                pygame.draw.line(screen, col, (tx, ty), (sx, sy), width)
                if z < 0.25:
                    pygame.draw.circle(screen, col, (int(sx), int(sy)), 2)
            else:
                size = 1 if z > 0.55 else 2
                if size == 1:
                    screen.set_at((int(sx), int(sy)), col)
                else:
                    pygame.draw.circle(screen, col, (int(sx), int(sy)), 1)

    @staticmethod
    def _sparkle(screen, x, y, size, pulse):
        r = size * (0.5 + 0.5 * pulse)
        d = r * 0.45

        col = (_clamp(120 + 135 * pulse), _clamp(210 + 45 * pulse), 255)
        dim = (_clamp(10 + 30 * pulse), _clamp(90 * pulse),
               _clamp(160 * pulse))

        pygame.draw.line(screen, dim, (x - d, y - d), (x + d, y + d), 1)
        pygame.draw.line(screen, dim, (x - d, y + d), (x + d, y - d), 1)
        pygame.draw.line(screen, col, (x - r, y), (x + r, y), 1)
        pygame.draw.line(screen, col, (x, y - r), (x, y + r), 1)
        pygame.draw.circle(screen, (255, 255, 255), (x, y), 1)

    def _draw_sparkles(self, screen):
        t = self.t

        for fx, fy, ph, size, spd in self.sparkles:
            pulse = 0.5 + 0.5 * math.sin(t * spd * 2 + ph)
            if pulse < 0.15:
                continue

            x = int(fx * self.w - self.camx * 30)
            y = int(fy * self.h - self.camy * 22)
            self._sparkle(screen, x, y, size, pulse)

    def tick(self):
        now = pygame.time.get_ticks()
        dt = min(0.05, max(0.0, (now - self.last) / 1000.0))
        self.last = now
        self.t += dt

    def draw_static(self, screen):
        self.tick()

        if self._still is None:
            self._still = self._build_still()

        screen.blit(self._still, (0, 0))

    def _build_still(self):
        w, h = self.w, self.h
        surf = pygame.Surface((w, h))
        surf.blit(self.backdrop,
                  (-(self.bw - w) // 2, -(self.bh - h) // 2))

        rng = random.Random(5)
        for _ in range(170):
            x = rng.randint(0, w - 1)
            y = rng.randint(0, h - 1)
            b = rng.uniform(0.35, 1.0)
            tint = rng.random()

            if tint < 0.10:
                base = (255, 170, 230)
            elif tint < 0.40:
                base = (130, 235, 255)
            else:
                base = (200, 220, 255)

            col = tuple(_clamp(c * b) for c in base)

            if rng.random() < 0.15:
                pygame.draw.circle(surf, col, (x, y), 1)
            else:
                surf.set_at((x, y), col)

        for p in sorted(self.planets, key=lambda i: -i["z"]):
            ax, ay, az = p["anchor"]
            s = self.DEPTH / (self.DEPTH + az)
            sx = self.cx + ax * s * self.UNIT
            sy = self.cy + ay * s * self.UNIT
            size = (max(8, int(p["surf"].get_width() * s)),
                    max(8, int(p["surf"].get_height() * s)))
            img = pygame.transform.smoothscale(p["surf"], size)
            surf.blit(img, img.get_rect(center=(int(sx), int(sy))))

        for fx, fy, ph, size, spd in self.sparkles:
            self._sparkle(surf, int(fx * w), int(fy * h), size, 0.85)

        surf.blit(self.vignette, (0, 0))
        return surf

    def _draw_planets(self, screen):
        t = self.t
        items = []

        for p in self.planets:
            ax, ay, az = p["anchor"]
            wx, wy, wz = p["wob"]
            a = t * p["speed"] + p["phase"]

            X = ax + math.cos(a) * wx
            Y = ay + math.sin(a * 0.8) * wy
            Z = az + math.sin(a) * wz

            s = self.DEPTH / (self.DEPTH + Z)
            sx = self.cx + (X - self.camx * 1.6) * s * self.UNIT
            sy = self.cy + (Y - self.camy * 1.6) * s * self.UNIT
            items.append((Z, p["surf"], s, sx, sy))

        for Z, surf, s, sx, sy in sorted(items, key=lambda i: -i[0]):
            size = (max(8, int(surf.get_width() * s)),
                    max(8, int(surf.get_height() * s)))
            img = pygame.transform.smoothscale(surf, size)
            screen.blit(img, img.get_rect(center=(int(sx), int(sy))))

    def draw_ship(self, screen, cx, cy, scale=34, heading=0.55):
        t = self.t

        roll = math.sin(t * 0.7) * 0.28
        pitch = 0.55 + math.sin(t * 0.9) * 0.08
        yaw = heading + math.sin(t * 0.5) * 0.10
        bob = math.sin(t * 1.3) * 7

        cr, sr = math.cos(roll), math.sin(roll)
        cp, sp = math.cos(pitch), math.sin(pitch)
        cz, sz = math.cos(yaw), math.sin(yaw)

        def transform(v):
            x, y, z = v
            x, z = x * cr + z * sr, -x * sr + z * cr
            y, z = y * cp - z * sp, y * sp + z * cp
            x, y = x * cz - y * sz, x * sz + y * cz
            return x, y, z

        pts = {name: transform(v) for name, v in _SHIP_V.items()}
        light = _norm((-0.4, 0.55, 0.75))
        faces = []

        for names, base in _SHIP_F:
            a, b, c = (pts[n] for n in names)
            ux, uy, uz = b[0] - a[0], b[1] - a[1], b[2] - a[2]
            vx, vy, vz = c[0] - a[0], c[1] - a[1], c[2] - a[2]
            n = _norm((uy * vz - uz * vy, uz * vx - ux * vz,
                       ux * vy - uy * vx))
            lam = abs(n[0] * light[0] + n[1] * light[1] + n[2] * light[2])
            shade = 0.30 + 0.85 * lam
            color = tuple(_clamp(ch * shade) for ch in base)
            depth = (a[2] + b[2] + c[2]) / 3
            faces.append((depth, names, color))

        def to_screen(p):
            return (cx + p[0] * scale, cy + bob - p[1] * scale)

        rear = [transform((sx, -1.8, 0.0)) for sx in (-0.28, 0.28)]
        gx, gy = to_screen(((rear[0][0] + rear[1][0]) / 2,
                            (rear[0][1] + rear[1][1]) / 2, 0))
        screen.blit(self._ship_glow, (int(gx - 46), int(gy - 46)),
                    special_flags=pygame.BLEND_RGB_ADD)

        flick = 0.85 + 0.25 * math.sin(t * 40)
        for sx in (-0.28, 0.28):
            base = transform((sx, -1.8, 0.0))
            tip = transform((sx, -1.8 - 1.5 * flick, 0.0))
            wl = transform((sx - 0.16, -1.8, 0.0))
            wr = transform((sx + 0.16, -1.8, 0.0))
            pygame.draw.polygon(screen, (60, 180, 255),
                                [to_screen(wl), to_screen(wr), to_screen(tip)])
            tip2 = transform((sx, -1.8 - 0.8 * flick, 0.0))
            pygame.draw.polygon(screen, (230, 250, 255),
                                [to_screen(transform((sx - 0.08, -1.8, 0))),
                                 to_screen(transform((sx + 0.08, -1.8, 0))),
                                 to_screen(tip2)])

        for depth, names, color in sorted(faces, key=lambda f: f[0]):
            poly = [to_screen(pts[n]) for n in names]
            pygame.draw.polygon(screen, color, poly)
            pygame.draw.polygon(screen, (110, 220, 255), poly, 1)