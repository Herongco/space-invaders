import math
import random

import pygame

from managers import ui
from managers.space3d import make_sphere
from managers.stars import draw_stars
from db import load_level_progress, get_unlocked_level

try:
    from managers.game_manager import LEVELS
except Exception:
    LEVELS = [{"name": f"Level {i}"} for i in range(1, 12)]

ORANGE = (255, 150, 60)

THEMES = [
    {"name": "EARTH DEFENSE", "short": "EARTH", "diff": "EASY",
     "dcol": ui.GREEN,
     "base": (40, 110, 255), "rim": (120, 200, 255),
     "story": "Alien invaders are approaching Earth. Hold the line and "
              "protect our home planet."},
    {"name": "LUNAR ATTACK", "short": "LUNAR", "diff": "EASY",
     "dcol": ui.GREEN,
     "base": (165, 170, 190), "rim": (205, 215, 240),
     "story": "Faster invaders are swarming the Moon. Keep moving and "
              "shoot them down."},
    {"name": "ASTEROID FIELD", "short": "ASTEROIDS", "diff": "MEDIUM",
     "dcol": ui.GOLD,
     "base": (150, 105, 75), "rim": (235, 175, 125),
     "story": "Zigzagging invaders hide inside the asteroid field. "
              "Stay sharp."},
    {"name": "MARS INVASION", "short": "MARS", "diff": "HARD",
     "dcol": ORANGE,
     "base": (215, 70, 50), "rim": (255, 150, 110),
     "story": "Armored invaders attack the red planet. They take many "
              "hits to destroy."},
    {"name": "SATURN'S REVENGE", "short": "SATURN", "diff": "VERY HARD",
     "dcol": (255, 110, 70),
     "base": (210, 175, 100), "rim": (250, 225, 160),
     "story": "The invaders strike back at Saturn with huge, fast and "
              "armored fleets. No mistakes."},
    {"name": "ALIEN OVERLORD", "short": "OVERLORD", "diff": "BOSS FIGHT",
     "dcol": ui.RED,
     "base": (150, 60, 230), "rim": (220, 150, 255), "boss": True,
     "reward": "REWARD: UNLOCK DARK GALAXY",
     "story": "The alien mothership has arrived. Dodge its fire and "
              "bring it down."},
    {"name": "DARK GALAXY", "short": "DARK GALAXY", "diff": "VERY HARD",
     "dcol": (255, 110, 70),
     "base": (80, 50, 150), "rim": (170, 140, 245),
     "story": "Shadow aliens flicker in the dark. Four waves, and each "
              "one takes two hits."},
    {"name": "ALIEN EMPEROR", "short": "EMPEROR", "diff": "BOSS FIGHT",
     "dcol": ui.RED,
     "base": (230, 80, 60), "rim": (255, 170, 140), "boss": True,
     "reward": "REWARD: UNLOCK GALACTIC WAR",
     "story": "The Emperor commands a stronger fleet. More bullets, more "
              "health, no mercy."},
    {"name": "GALACTIC WAR", "short": "GALACTIC WAR", "diff": "EXTREME",
     "dcol": (255, 70, 90),
     "base": (90, 60, 190), "rim": (190, 160, 255),
     "story": "Every alien type joins the war. Five waves of invaders "
              "and falling asteroids."},
    {"name": "THE FINAL BOSS", "short": "FINAL BOSS", "diff": "FINAL BOSS",
     "dcol": ui.RED,
     "base": (200, 30, 60), "rim": (255, 120, 140), "boss": True,
     "reward": "REWARD: WIN + ENDLESS MODE",
     "story": "The last stand. Four phases of bullets, rain and rings. "
              "Save the galaxy."},
    {"name": "ENDLESS MODE", "short": "ENDLESS", "diff": "ENDLESS",
     "dcol": (80, 235, 190),
     "base": (40, 190, 150), "rim": (130, 255, 220), "endless": True,
     "reward": "REWARD: LEADERBOARD GLORY",
     "story": "No finish line. Survive as long as you can and set a new "
              "high score."},
]


def wrap(text, size, width):
    f = ui.font(size)
    lines, cur = [], ""

    for word in text.split():
        test = (cur + " " + word).strip()
        if f.size(test)[0] <= width:
            cur = test
        else:
            lines.append(cur)
            cur = word

    if cur:
        lines.append(cur)

    return lines


class LevelSelect:

    TILE_W = 112
    TILE_H = 92
    GAP = 10
    PREVIEW_H = 160
    COLS = 4

    def __init__(self, screen, w, h, player=None):
        self.screen = screen
        self.w = w
        self.h = h
        self.player = player
        self.action = None
        self.start_level = 1

        self.total = max(1, len(LEVELS))
        self.unlocked = 1
        self.progress = {}

        pid = player.get("player_id") if isinstance(player, dict) else None

        if pid:
            try:
                self.progress = load_level_progress(pid)
                self.unlocked = get_unlocked_level(pid, self.total)
            except Exception as e:
                print("LEVEL SELECT ERROR:", e)

        self.selected = self.unlocked
        self.message = ""
        self.message_timer = 0

        self.previews = {}
        self.icons = {}

        for n in range(1, self.total + 1):
            th = self.theme(n)
            self.icons[n] = make_sphere(16, th["base"], bands=0, seed=n,
                                        rim=th["rim"], glow=4)

        rows = (self.total + self.COLS - 1) // self.COLS
        grid_w = self.COLS * self.TILE_W + (self.COLS - 1) * self.GAP
        grid_h = rows * self.TILE_H + (rows - 1) * self.GAP

        mission_w = 310
        mission_h = 454
        top = 96
        panel_gap = 40
        left = (w - (grid_w + 52 + panel_gap + mission_w)) // 2

        self.grid_panel = pygame.Rect(left, top, grid_w + 52, grid_h + 44)

        self.tiles = {}
        for i in range(self.total):
            r, c = divmod(i, self.COLS)
            in_row = min(self.COLS, self.total - r * self.COLS)
            shift = (self.COLS - in_row) * (self.TILE_W + self.GAP) // 2

            self.tiles[i + 1] = pygame.Rect(
                self.grid_panel.x + 26 + shift
                + c * (self.TILE_W + self.GAP),
                self.grid_panel.y + 22 + r * (self.TILE_H + self.GAP),
                self.TILE_W,
                self.TILE_H,
            )

        self.progress_panel = pygame.Rect(
            self.grid_panel.x,
            self.grid_panel.bottom + 12,
            self.grid_panel.w,
            top + mission_h - (self.grid_panel.bottom + 12),
        )

        self.mission_panel = pygame.Rect(self.grid_panel.right + panel_gap, top,
                                         mission_w, mission_h)

        self.play_btn = pygame.Rect(0, 0, 260, 46)
        self.play_btn.midtop = (self.mission_panel.centerx,
                                self.mission_panel.bottom + 18)

        self.back_btn = pygame.Rect(30, h - 66, 130, 42)


    def theme(self, n):
        th = dict(THEMES[(n - 1) % len(THEMES)])

        if n > len(THEMES) and n <= len(LEVELS):
            th["name"] = str(LEVELS[n - 1].get("name", th["name"])).upper()

        if n <= len(LEVELS) and LEVELS[n - 1].get("boss"):
            th["boss"] = True
            th.setdefault("diff", "BOSS FIGHT")

        if n <= len(LEVELS) and LEVELS[n - 1].get("endless"):
            th["endless"] = True

        return th

    def best_score(self, n):
        return self.progress.get(n, {}).get("best", 0)

    def stars(self, n):
        return self.progress.get(n, {}).get("stars", 0)

    def completed(self, n):
        return bool(self.progress.get(n, {}).get("completed"))

    def total_stars(self):
        return sum(self.stars(n) for n in range(1, self.total + 1))

    def max_stars(self):
        return 3 * sum(1 for c in LEVELS if not c.get("endless"))

    def cfg(self, n):
        return LEVELS[n - 1] if n <= len(LEVELS) else {}

    def start(self):
        if self.selected <= self.unlocked:
            self.start_level = self.selected
            self.action = "start"

    def show_locked(self, n):
        self.message = f"COMPLETE MISSION {n - 1} TO UNLOCK THIS ONE"
        self.message_timer = 150

    def move(self, dx, dy):
        n = self.selected + dx + dy * self.COLS

        if 1 <= n <= self.unlocked:
            self.selected = n


    def preview(self, n):
        if n not in self.previews:
            size = (self.mission_panel.w - 40, self.PREVIEW_H)
            img = ui.load_image(f"rogame{n}.png", size)

            if img is None:
                img = self.make_preview(n, size)

            self.previews[n] = img

        return self.previews[n]

    def make_preview(self, n, size):
        th = self.theme(n)
        w, h = size
        surf = pygame.Surface(size)

        for y in range(h):
            k = y / (h - 1)
            col = tuple(int(c0 + (c1 * 0.30 - c0) * k)
                        for c0, c1 in zip((3, 8, 36), th["base"]))
            pygame.draw.line(surf, col, (0, y), (w, y))

        rng = random.Random(n * 17)
        for _ in range(40):
            x, y = rng.randint(0, w - 1), rng.randint(0, h - 1)
            b = rng.randint(120, 255)
            surf.set_at((x, y), (b, b, 255))

        if th.get("endless"):
            for i in range(5):
                ui.draw_invader(surf, int(w * (0.12 + 0.19 * i)),
                                int(h * 0.12 + (i % 2) * 22), 3, th["dcol"])
            self.draw_infinity(surf, w // 2, int(h * 0.68), 15, th["dcol"])
        elif th.get("boss"):
            glow = pygame.Surface((120, 120), pygame.SRCALPHA)
            for r in range(60, 0, -4):
                pygame.draw.circle(glow, (180, 40, 90, int(70 * (1 - r / 60))),
                                   (60, 60), r)
            surf.blit(glow, (w // 2 - 60, h // 2 - 60))
            ui.draw_invader(surf, w // 2, h // 2 - 32, 8, ui.RED)
        else:
            planet = make_sphere(38, th["base"], bands=0, seed=n,
                                 rim=th["rim"], glow=10)
            surf.blit(planet, planet.get_rect(center=(int(w * 0.70),
                                                      int(h * 0.55))))

            if n % len(THEMES) == 3:
                for _ in range(10):
                    x = rng.randint(10, w - 10)
                    y = rng.randint(8, h - 8)
                    r = rng.randint(4, 11)
                    pygame.draw.circle(surf, (105, 80, 62), (x, y), r)
                    pygame.draw.circle(surf, (170, 135, 105), (x - 1, y - 1),
                                       max(1, r // 2))

            ui.draw_invader(surf, int(w * 0.25), int(h * 0.30), 4,
                            th["dcol"])

        return surf

    @staticmethod
    def draw_infinity(surf, cx, cy, r, color):
        pygame.draw.circle(surf, color, (cx - r, cy), r, 3)
        pygame.draw.circle(surf, color, (cx + r, cy), r, 3)


    def draw(self):
        ui.draw_background(self.screen, self.w, self.h, dim=0)
        ui.draw_header(self.screen, self.w, "SELECT YOUR MISSION",
                       icon="play")

        ui.draw_panel(self.screen, self.grid_panel, alpha=205)

        for n, rect in self.tiles.items():
            self.draw_tile(n, rect)

        self.draw_progress()
        self.draw_mission()

        ui.draw_button(self.screen, self.play_btn, "START MISSION", True,
                       "play")
        ui.draw_button(self.screen, self.back_btn, "BACK", icon="back")

        if self.message_timer > 0:
            self.message_timer -= 1
            ui.draw_text(self.screen, self.message, 14, ui.RED,
                         (self.grid_panel.centerx, self.back_btn.centery),
                         "center", True)

    def draw_tile(self, n, rect):
        th = self.theme(n)
        locked = n > self.unlocked
        cleared = self.completed(n)
        selected = n == self.selected
        newest = (n == self.unlocked and n > 1)
        hover = (not locked) and rect.collidepoint(pygame.mouse.get_pos())
        now = pygame.time.get_ticks() / 1000.0

        pts = ui.chamfer(rect, 12)

        if locked:
            fill, border = (6, 18, 50), (45, 75, 120)
        elif selected or hover:
            fill, border = (14, 70, 160), (ui.CYAN if selected else ui.NEON)
        else:
            fill, border = (6, 30, 86), (40, 125, 225)

        if newest:
            k = 0.5 + 0.5 * math.sin(now * 4)
            glow = (int(30 + 60 * k), int(130 + 100 * k), 255)
            pygame.draw.polygon(
                self.screen, glow,
                ui.chamfer(rect.inflate(8 + int(4 * k), 8 + int(4 * k)),
                           15), 2)

            for i in range(7):
                t = (now * 0.7 + i / 7.0) % 1.0
                x = rect.x + 10 + (i * 41) % (rect.w - 20)
                y = rect.bottom - 6 - t * (rect.h + 14)
                c = int(255 * (1 - t))
                pygame.draw.circle(self.screen, (c // 3, c, 255),
                                   (int(x), int(y)), 2)

        pygame.draw.polygon(self.screen, fill, pts)
        pygame.draw.polygon(self.screen, border, pts, 3 if selected else 2)

        cx = rect.centerx
        pc = (cx, rect.y + 36)

        ui.draw_text(self.screen, f"{n:02d}", 13,
                     ui.GRAY if locked else ui.CYAN,
                     (rect.x + 8, rect.y + 7), "topleft", True)

        if cleared and not th.get("endless"):
            draw_stars(self.screen, rect.right - 32, rect.y + 16,
                       self.stars(n), size=6)

        if locked:
            pygame.draw.circle(self.screen, (18, 34, 70), pc, 17)
            pygame.draw.circle(self.screen, (45, 75, 120), pc, 17, 2)
            ui.draw_icon(self.screen, "lock", pc[0], pc[1] + 2, ui.GRAY)
        elif th.get("endless"):
            self.draw_infinity(self.screen, cx, pc[1], 8, th["dcol"])
        elif th.get("boss"):
            ui.draw_invader(self.screen, cx, pc[1] - 12, 3, ui.RED)
        else:
            icon = self.icons[n]
            self.screen.blit(icon, icon.get_rect(center=pc))
            ui.add_click_area(rect)

        if (th.get("boss") or th.get("endless")) and not locked:
            ui.add_click_area(rect)

        name = ui.fit_text(th.get("short", th["name"]), ui.font(11, True),
                           rect.w - 10)
        ui.draw_text(self.screen, name, 11,
                     ui.GRAY if locked else ui.WHITE,
                     (cx, rect.y + 64), "center", True)

        ui.draw_text(self.screen, th["diff"], 10,
                     (70, 95, 130) if locked else th["dcol"],
                     (cx, rect.y + 79), "center", True)

    def draw_progress(self):
        panel = self.progress_panel
        ui.draw_panel(self.screen, panel, alpha=205)

        ui.draw_text(self.screen, "MISSION PROGRESS", 15, ui.CYAN,
                     (panel.x + 26, panel.y + 10), "topleft", True)

        bar_w = panel.w - 52
        seg_w = (bar_w - (self.total - 1) * 6) / self.total

        for n in range(1, self.total + 1):
            seg = pygame.Rect(int(panel.x + 26 + (n - 1) * (seg_w + 6)),
                              panel.y + 34, int(seg_w), 12)

            if self.completed(n):
                col = ui.GREEN
            elif n == self.unlocked:
                col = ui.CYAN
            else:
                col = (20, 36, 76)

            pygame.draw.rect(self.screen, col, seg, border_radius=4)
            pygame.draw.rect(self.screen, (40, 125, 225), seg, 1,
                             border_radius=4)

        ui.draw_text(self.screen,
                     f"UNLOCKED: {self.unlocked} / {self.total}", 14,
                     ui.WHITE, (panel.x + 26, panel.y + 54), "topleft",
                     True)

        ui.draw_text(self.screen,
                     f"STARS: {self.total_stars()} / {self.max_stars()}", 14,
                     ui.GOLD, (panel.right - 26, panel.y + 54), "topright",
                     True)

        ui.draw_text(self.screen,
                     "Complete a mission to unlock the next one.", 12,
                     ui.GRAY, (panel.x + 26, panel.y + 74), "topleft")

    def draw_mission(self):
        panel = self.mission_panel
        ui.draw_panel(self.screen, panel, alpha=205)

        n = self.selected
        th = self.theme(n)
        cfg = self.cfg(n)
        x = panel.x + 20
        iw = panel.w - 40
        o = self.PREVIEW_H - 110

        box = pygame.Rect(x, panel.y + 20, iw, self.PREVIEW_H)
        self.screen.blit(self.preview(n), box.topleft)
        pygame.draw.rect(self.screen, ui.NEON, box, 2, border_radius=6)

        ui.draw_text(self.screen, f"MISSION {n:02d}", 14, ui.CYAN,
                     (x, panel.y + 142 + o), "topleft", True)

        name = ui.fit_text(th["name"], ui.font(22, True), iw)
        ui.draw_text(self.screen, name, 22, ui.WHITE,
                     (x, panel.y + 162 + o), "topleft", True)

        ui.draw_text(self.screen, "DIFFICULTY:", 14, ui.GRAY,
                     (x, panel.y + 196 + o), "topleft")
        ui.draw_text(self.screen, th["diff"], 14, th["dcol"],
                     (x + 98, panel.y + 196 + o), "topleft", True)

        if th.get("endless"):
            goal = "A boss appears every 10 waves."
        elif th.get("boss"):
            goal = "Defeat the boss to win."
        else:
            goal = (f"Defeat {cfg.get('waves', 1)} waves of "
                    f"{cfg.get('count', 5)} invaders.")

        lines = wrap(th["story"] + " " + goal, 13, iw)[:5]

        for i, line in enumerate(lines):
            ui.draw_text(self.screen, line, 13, ui.GRAY,
                         (x, panel.y + 222 + o + i * 18), "topleft")

        reward = th.get("reward", f"REWARD: +{10 * n} BONUS POINTS")
        ui.draw_text(self.screen, reward, 13, ui.GOLD,
                     (x, panel.y + 326 + o), "topleft", True)

        ui.draw_text(self.screen,
                     f"BEST SCORE: {self.best_score(n)}", 13, ui.WHITE,
                     (x, panel.y + 348 + o), "topleft", True)

        if not th.get("endless"):
            draw_stars(self.screen, panel.right - 58, panel.y + 356 + o,
                       self.stars(n), size=9)

    def handle_events(self, events):
        self.action = None

        for event in events:

            if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                pos = event.pos

                if self.back_btn.collidepoint(pos):
                    self.action = "back"
                    return

                if self.play_btn.collidepoint(pos):
                    self.start()
                    return

                for n, rect in self.tiles.items():
                    if rect.collidepoint(pos):
                        if n <= self.unlocked:
                            self.selected = n
                        else:
                            self.show_locked(n)
                        break

            elif event.type == pygame.KEYDOWN:

                if event.key == pygame.K_ESCAPE:
                    self.action = "back"
                    return

                elif event.key in (pygame.K_RETURN, pygame.K_KP_ENTER,
                                   pygame.K_SPACE):
                    self.start()
                    return

                elif event.key in (pygame.K_LEFT, pygame.K_a):
                    self.move(-1, 0)
                elif event.key in (pygame.K_RIGHT, pygame.K_d):
                    self.move(1, 0)
                elif event.key in (pygame.K_UP, pygame.K_w):
                    self.move(0, -1)
                elif event.key in (pygame.K_DOWN, pygame.K_s):
                    self.move(0, 1)