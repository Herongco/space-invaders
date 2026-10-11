import math
import os
import random

import pygame

from entities.player import Player
from entities.button import MobileButtons
from entities.enemy import Enemy
from entities.bullet import Bullet

from db import save_score, get_player_highest_score, get_level_best
from settings_manager import load_settings
from managers import ui
from managers.settings import Settings, apply_audio
from managers.stars import draw_stars
from managers.hazards import Hazards


START_LIVES = 3
MAX_LIVES = 5


BOSSES = {
    "overlord": {
        "hp": 40, "points": 50, "size": (200, 150),
        "tint": (210, 110, 255),
        "move": (0.025, 0.04, 0.055),
        "interval": (90, 65, 50),
        "attacks": [
            {"spread": (3, 0.30, 4.0)},
            {"spread": (5, 0.25, 5.0)},
            {"spread": (3, 0.25, 5.5), "ring": (12, 3.2, 2)},
        ],
    },
    "emperor": {
        "hp": 80, "points": 100, "size": (230, 170),
        "tint": (255, 120, 90),
        "move": (0.03, 0.045, 0.06),
        "interval": (80, 58, 42),
        "attacks": [
            {"spread": (5, 0.22, 4.5)},
            {"spread": (5, 0.25, 5.2), "ring": (10, 3.0, 3)},
            {"spread": (7, 0.20, 5.8), "ring": (14, 3.4, 2)},
        ],
    },
    "final": {
        "hp": 140, "points": 200, "size": (260, 190),
        "tint": (255, 70, 90),
        "move": (0.03, 0.045, 0.06, 0.075),
        "interval": (75, 55, 42, 30),
        "attacks": [
            {"spread": (5, 0.22, 4.8), "rain": (2, 3.5)},
            {"spread": (7, 0.20, 5.4), "ring": (12, 3.2, 3),
             "rain": (3, 3.8)},
            {"spread": (7, 0.22, 6.0), "ring": (16, 3.4, 2),
             "rain": (4, 4.2)},
            {"spread": (9, 0.18, 6.2), "ring": (20, 3.6, 2),
             "rain": (5, 4.5)},
        ],
    },
}

LEVELS = [
    {"name": "Earth Defense", "waves": 2, "count": 5, "drop": 170,
     "mix": {"normal": 1.0}, "tint": (40, 110, 255)},
    {"name": "Lunar Attack", "waves": 3, "count": 6, "drop": 150,
     "mix": {"normal": 0.4, "fast": 0.6}, "tint": (165, 170, 190)},
    {"name": "Asteroid Field", "waves": 3, "count": 7, "drop": 140,
     "mix": {"normal": 0.3, "fast": 0.2, "zigzag": 0.5},
     "tint": (150, 105, 75), "hazard": "asteroids"},
    {"name": "Mars Invasion", "waves": 4, "count": 7, "drop": 120,
     "mix": {"normal": 0.2, "zigzag": 0.3, "strong": 0.5},
     "tint": (215, 70, 50), "hazard": "storm"},
    {"name": "Saturn's Revenge", "waves": 4, "count": 8, "drop": 100,
     "mix": {"fast": 0.25, "zigzag": 0.3, "strong": 0.45},
     "tint": (210, 175, 100), "hazard": "rings"},
    {"name": "Alien Overlord", "boss": BOSSES["overlord"],
     "tint": (150, 60, 230)},
    {"name": "Dark Galaxy", "waves": 4, "count": 8, "drop": 95,
     "mix": {"shadow": 0.5, "zigzag": 0.2, "fast": 0.15, "strong": 0.15},
     "tint": (70, 40, 130)},
    {"name": "Alien Emperor", "boss": BOSSES["emperor"],
     "tint": (230, 80, 60)},
    {"name": "Galactic War", "waves": 5, "count": 9, "drop": 80,
     "mix": {"normal": 0.1, "fast": 0.2, "zigzag": 0.2, "strong": 0.25,
             "shadow": 0.25},
     "tint": (90, 60, 190), "hazard": "asteroids"},
    {"name": "The Final Boss", "boss": BOSSES["final"], "final": True,
     "tint": (200, 30, 60)},
    {"name": "Endless Mode", "endless": True, "tint": (40, 190, 150)},
]

KINDS = {
    "normal": {"hp": 1, "speed": 4.0, "points": 1, "tint": None},
    "fast": {"hp": 1, "speed": 6.5, "points": 2, "tint": (120, 190, 255)},
    "zigzag": {"hp": 1, "speed": 4.2, "points": 3, "tint": (200, 130, 255)},
    "strong": {"hp": 3, "speed": 3.0, "points": 5, "tint": (255, 120, 120)},
    "shadow": {"hp": 2, "speed": 5.0, "points": 4, "tint": (95, 70, 170)},
}


def endless_mix(wave):
    mix = {"normal": max(0.15, 1.0 - 0.09 * wave)}

    if wave >= 2:
        mix["fast"] = min(0.35, 0.08 * wave)
    if wave >= 4:
        mix["zigzag"] = min(0.35, 0.06 * wave)
    if wave >= 6:
        mix["strong"] = min(0.40, 0.05 * wave)
    if wave >= 9:
        mix["shadow"] = min(0.40, 0.04 * wave)

    return mix


PU_INFO = {
    "rapid": {"label": "RAPID FIRE", "color": (80, 200, 255), "duration": 600},
    "shield": {"label": "SHIELD", "color": (100, 150, 255), "duration": 600},
    "freeze": {"label": "FREEZE", "color": (160, 235, 255), "duration": 300},
    "life": {"label": "EXTRA LIFE", "color": (255, 100, 170), "duration": 0},
    "blast": {"label": "MEGA BLAST", "color": (255, 150, 60), "duration": 0},
}
PU_WEIGHTS = [("rapid", 30), ("shield", 25), ("freeze", 15),
              ("life", 12), ("blast", 18)]
PU_DROP_CHANCE = 0.14

QUALITY = {
    "low": {"particles": 6, "stars": 60, "planets": False, "bg": False},
    "medium": {"particles": 12, "stars": 110, "planets": True, "bg": True},
    "high": {"particles": 22, "stars": 180, "planets": True, "bg": True},
}


def draw_heart(screen, cx, cy, color, filled=True, scale=1.0):
    w = 0 if filled else 2
    r = max(2, int(5 * scale))
    o = int(5 * scale)
    pygame.draw.circle(screen, color, (cx - o, cy - int(3 * scale)), r, w)
    pygame.draw.circle(screen, color, (cx + o, cy - int(3 * scale)), r, w)
    pygame.draw.polygon(screen, color,
                        [(cx - 2 * o, cy - int(1 * scale)),
                         (cx + 2 * o, cy - int(1 * scale)),
                         (cx, cy + int(10 * scale))],
                        w)


def draw_powerup_icon(screen, kind, cx, cy, color):
    d = pygame.draw

    if kind == "rapid":
        d.polygon(screen, color, [(cx + 2, cy - 10), (cx - 6, cy + 2),
                                  (cx - 1, cy + 2), (cx - 3, cy + 10),
                                  (cx + 6, cy - 3), (cx + 1, cy - 3)])
    elif kind == "shield":
        d.polygon(screen, color, [(cx - 7, cy - 8), (cx + 7, cy - 8),
                                  (cx + 7, cy + 1), (cx, cy + 10),
                                  (cx - 7, cy + 1)], 2)
    elif kind == "freeze":
        for i in range(3):
            a = i * math.pi / 3
            d.line(screen, color,
                   (cx - math.cos(a) * 9, cy - math.sin(a) * 9),
                   (cx + math.cos(a) * 9, cy + math.sin(a) * 9), 2)
    elif kind == "life":
        draw_heart(screen, cx, cy, color)
    elif kind == "blast":
        for i in range(8):
            a = i * math.pi / 4
            d.line(screen, color, (cx, cy),
                   (cx + math.cos(a) * 10, cy + math.sin(a) * 10), 2)
        d.circle(screen, color, (cx, cy), 4)


class TypedEnemy(Enemy):

    def __init__(self, index, total, screen_width, kind="normal",
                 hp_bonus=0, speed_mult=1.0):
        super().__init__(index, total, screen_width)

        cfg = KINDS[kind]
        self.kind = kind
        self.hp = cfg["hp"] + (hp_bonus if cfg["hp"] > 1 else 0)
        self.max_hp = self.hp
        self.speed = cfg["speed"] * speed_mult
        self.points = cfg["points"]
        self.phase = random.uniform(0, math.tau)

        if cfg["tint"]:
            self.image = self.image.copy()
            self.image.fill(cfg["tint"] + (255,),
                            special_flags=pygame.BLEND_RGBA_MULT)

    def update(self):
        super().update()

        if self.active and self.state == "dropping":
            if self.kind == "zigzag":
                self.phase += 0.12
                self.x += math.sin(self.phase) * 4
            elif self.kind == "shadow":
                self.phase += 0.08
                self.x += math.sin(self.phase) * 2.5

    def draw(self, screen):
        if self.kind == "shadow":
            alpha = 170 + int(70 * math.sin(pygame.time.get_ticks() / 150
                                            + self.phase))
            self.image.set_alpha(alpha)

        super().draw(screen)

    def hit(self, damage=1):
        self.hp -= damage
        return self.hp <= 0


class Boss:

    def __init__(self, width, height, cfg=None):
        cfg = cfg or BOSSES["overlord"]

        self.cfg = cfg
        self.screen_w = width
        self.width, self.height = cfg["size"]
        self.x = width // 2 - self.width // 2
        self.y = -self.height
        self.target_y = 92
        self.hp = cfg["hp"]
        self.max_hp = cfg["hp"]
        self.points = cfg["points"]
        self.phases = len(cfg["attacks"])
        self.entering = True
        self.t = 0
        self.fire_timer = 0
        self.flash = 0
        self.volley = 0
        self.shield_time = 0
        self.last_phase = 1

        try:
            img = pygame.image.load("assets/images/romy.png").convert_alpha()
            img = pygame.transform.scale(img, (self.width, self.height))
            img.fill(tuple(cfg["tint"]) + (255,),
                     special_flags=pygame.BLEND_RGBA_MULT)
        except pygame.error:
            img = pygame.Surface((self.width, self.height), pygame.SRCALPHA)
            pygame.draw.ellipse(img, cfg["tint"], img.get_rect())

        self.image = img
        self.flash_image = img.copy()
        self.flash_image.fill((90, 90, 90, 0), special_flags=pygame.BLEND_RGBA_ADD)

    @property
    def phase(self):
        lost = 1 - self.hp / self.max_hp
        return max(1, min(self.phases, 1 + int(lost * self.phases)))

    @property
    def enraged(self):
        return self.phase >= 2

    @property
    def shielded(self):
        return self.shield_time > 0

    def update(self):
        if self.flash > 0:
            self.flash -= 1

        if self.shield_time > 0:
            self.shield_time -= 1

        if self.entering:
            self.y += 2
            if self.y >= self.target_y:
                self.y = self.target_y
                self.entering = False
            return

        self.t += 1
        span = self.screen_w / 2 - self.width / 2 - 20
        speed = self.cfg["move"][self.phase - 1]
        self.x = self.screen_w / 2 - self.width / 2 + math.sin(self.t * speed) * span
        self.y = self.target_y + math.sin(self.t * 0.03) * 12
        self.fire_timer += 1

    def ready_to_fire(self):
        interval = self.cfg["interval"][self.phase - 1]

        if not self.entering and self.fire_timer >= interval:
            self.fire_timer = 0
            return True
        return False

    def get_rect(self):
        return pygame.Rect(self.x + 25, self.y + 20,
                           self.width - 50, self.height - 40)

    def draw(self, screen):
        screen.blit(self.flash_image if self.flash > 0 else self.image,
                    (self.x, self.y))

        if self.shield_time > 0:
            cx = int(self.x + self.width / 2)
            cy = int(self.y + self.height / 2)
            pulse = 4 * math.sin(self.shield_time * 0.4)
            r = int(self.width * 0.62 + pulse)
            bubble = pygame.Surface((r * 2 + 4, r * 2 + 4), pygame.SRCALPHA)
            pygame.draw.circle(bubble, (90, 200, 255, 60), (r + 2, r + 2), r)
            pygame.draw.circle(bubble, (160, 235, 255, 230), (r + 2, r + 2),
                               r, 3)
            screen.blit(bubble, (cx - r - 2, cy - r - 2))


class EnemyShot:
    def __init__(self, x, y, vx, vy):
        self.x, self.y, self.vx, self.vy = x, y, vx, vy

    def update(self):
        self.x += self.vx
        self.y += self.vy

    def alive(self, w, h):
        return -30 < self.x < w + 30 and -30 < self.y < h + 30

    def get_rect(self):
        return pygame.Rect(self.x - 6, self.y - 6, 12, 12)

    def draw(self, screen):
        pygame.draw.circle(screen, (255, 70, 90), (int(self.x), int(self.y)), 7)
        pygame.draw.circle(screen, (255, 200, 210), (int(self.x), int(self.y)), 3)


class PowerUp:
    def __init__(self, x, y, kind):
        self.x, self.y, self.kind = x, y, kind
        self.size = 36
        self.alive = True

    def update(self, height):
        self.y += 2
        if self.y > height + 40:
            self.alive = False

    def get_rect(self):
        return pygame.Rect(self.x - self.size // 2, self.y - self.size // 2,
                           self.size, self.size)

    def draw(self, screen):
        color = PU_INFO[self.kind]["color"]
        pos = (int(self.x), int(self.y))
        pygame.draw.circle(screen, (5, 20, 55), pos, 20)
        pygame.draw.circle(screen, color, pos, 20, 2)
        draw_powerup_icon(screen, self.kind, pos[0], pos[1], color)


class GameManager:

    def __init__(self, screen, width, height):
        self.screen = screen
        self.width = width
        self.height = height

        self.game_state = "playing"

        self.player_name = ""
        self.current_player_id = None
        self.highest_score = 0
        self.new_record = False

        self.settings = load_settings()
        self.sfx = {}
        self.load_sfx()

        self.pause_btn = pygame.Rect(width - 52, 8, 40, 40)

        panel = pygame.Rect(0, 0, 380, 290)
        panel.center = (width // 2, height // 2)
        self.pause_panel = panel
        self.resume_rect = pygame.Rect(panel.x + 40, panel.y + 90, 300, 48)
        self.settings_rect = pygame.Rect(panel.x + 40, panel.y + 150, 300, 48)
        self.menu_rect = pygame.Rect(panel.x + 40, panel.y + 210, 300, 48)

        over = pygame.Rect(0, 0, 420, 400)
        over.center = (width // 2, height // 2)
        self.over_panel = over
        self.play_again_rect = pygame.Rect(over.x + 50, over.bottom - 112,
                                           over.w - 100, 46)
        self.back_home_rect = pygame.Rect(over.x + 50, over.bottom - 56,
                                          over.w - 100, 42)

        high = pygame.Rect(0, 0, 440, 300)
        high.center = (width // 2, height // 2)
        self.high_panel = high
        self.continue_rect = pygame.Rect(high.x + 60, high.bottom - 82,
                                         high.w - 120, 50)

        self.settings_screen = None
        self._grad_cache = {}
        self._tint_cache = {}
        self._hud_cache = {}

        self.start_again()


    def apply_settings(self):
        self.settings = load_settings()
        self.quality = QUALITY["high"]
        apply_audio(self.settings)
        self.build_background()

    def load_sfx(self):
        if not pygame.mixer.get_init():
            return

        base = os.path.join(ui.ROOT, "assets", "sounds")

        for name in ("shoot", "explosion", "powerup", "hit"):
            path = os.path.join(base, name + ".wav")
            if os.path.exists(path):
                try:
                    self.sfx[name] = pygame.mixer.Sound(path)
                except pygame.error:
                    pass

        shoot = ui.load_sound(ui.SHOOT_FILE)
        if shoot:
            self.sfx["shoot"] = shoot

        over = ui.load_sound(ui.OVER_FILE)
        if over:
            self.sfx["over"] = over

    def play(self, name):
        sound = self.sfx.get(name)

        if sound and self.settings.get("sound_enabled", True):
            sound.set_volume(self.settings.get("sound_volume", 80) / 100)
            sound.play()

    def build_background(self):
        ui.get_space(self.width, self.height)


    def set_player(self, player):
        if not player:
            return

        self.current_player_id = player.get("player_id")
        self.player_name = player.get("username", "")
        self.start_again()

    def start_game(self):
        self.start_again()

    def start_again(self, level=1):
        level = max(1, min(len(LEVELS), int(level or 1)))
        self.apply_settings()

        self.game_state = "playing"
        self.score = 0
        self.score_saved = False
        self.victory = False
        self.victory_timer = 0
        self.new_record = False
        self.high_shown = False

        self.hits_taken = 0
        self.stars = 0
        self.level_best = 0
        self.level_new_best = False

        self.highest_score = 0
        if self.current_player_id:
            try:
                self.highest_score = get_player_highest_score(
                    self.current_player_id)
            except Exception as e:
                print("HIGH SCORE ERROR:", e)

        self.lives = START_LIVES
        self.invuln = 0
        self.fire_cooldown = 0
        self.enemy_timer = 0
        self.blink_timer = 0
        self.history = []

        self.player = Player(self.width, self.height)
        self.buttons = MobileButtons()

        self.bullets = []
        self.enemies = []
        self.boss = None
        self.enemy_shots = []
        self.powerups = []
        self.particles = []
        self.popups = []
        self.effects = {"rapid": 0, "shield": 0, "freeze": 0}

        self.level = level
        self.wave = 0
        self.level_banner = 0
        self.start_level(level)


    def start_level(self, level):
        self.level = level
        self.wave = 0
        self.level_banner = 150
        self.enemies = []
        self.enemy_shots = []
        self.enemy_timer = 0

        cfg = LEVELS[level - 1]
        self.hazards = Hazards(cfg.get("hazard"), self.width, self.height)

        if cfg.get("boss"):
            self.boss = Boss(self.width, self.height, cfg["boss"])
        else:
            self.boss = None
            self.spawn_wave()

    def spawn_wave(self):
        cfg = LEVELS[self.level - 1]
        self.wave += 1

        if cfg.get("endless"):
            self.spawn_endless_wave()
            return

        kinds = random.choices(
            list(cfg["mix"].keys()),
            weights=list(cfg["mix"].values()),
            k=cfg["count"]
        )

        self.enemies = [
            TypedEnemy(i, len(kinds), self.width, kind)
            for i, kind in enumerate(kinds)
        ]
        self.enemy_timer = 0

    def spawn_endless_wave(self):
        wave = self.wave
        self.enemy_timer = 0
        self.level_banner = 90
        self.enemy_shots = []

        boss_wave = wave % 10 == 0

        if boss_wave or wave < 4:
            kind = None
        else:
            kind = ("asteroids", "storm", "rings")[((wave - 4) // 3) % 3]

        if kind != self.hazards.kind:
            self.hazards = Hazards(kind, self.width, self.height)

            if self.hazards.label:
                self.add_popup("HAZARD: " + self.hazards.label,
                               self.width // 2, 190, (255, 150, 60))

        if boss_wave:
            cycle = wave // 10 - 1
            cfg = dict(BOSSES[("overlord", "emperor", "final")[cycle % 3]])
            cfg["hp"] = int(cfg["hp"] * (1 + 0.2 * cycle))

            self.enemies = []
            self.boss = Boss(self.width, self.height, cfg)
            self.add_popup("WARNING! BOSS INCOMING", self.width // 2, 220,
                           ui.RED)
            return

        mix = endless_mix(wave)
        count = min(9, 4 + wave // 2)
        kinds = random.choices(list(mix.keys()), weights=list(mix.values()),
                               k=count)

        hp_bonus = (wave - 1) // 6
        speed_mult = min(1.4, 1 + wave * 0.02)

        self.enemies = [
            TypedEnemy(i, len(kinds), self.width, kind, hp_bonus, speed_mult)
            for i, kind in enumerate(kinds)
        ]

    def check_wave_clear(self):
        if self.game_state != "playing" or self.boss or not self.enemies:
            return

        if not all(e.state == "offscreen" for e in self.enemies):
            return

        cfg = LEVELS[self.level - 1]

        if cfg.get("endless"):
            bonus = 5 * self.wave
            self.score += bonus
            self.add_popup(f"WAVE {self.wave} CLEAR +{bonus}",
                           self.width // 2, 260, ui.GREEN)

            if self.wave % 5 == 0 and self.lives < MAX_LIVES:
                self.lives += 1
                self.add_popup("EXTRA LIFE", self.width // 2, 285, ui.CYAN)

            self.spawn_wave()
            return

        if self.wave < cfg["waves"]:
            self.spawn_wave()
            return

        bonus = 10 * self.level
        self.score += bonus
        self.add_popup(f"MISSION CLEAR +{bonus}", self.width // 2, 260,
                       ui.GREEN)
        self.begin_victory()

    def begin_victory(self):
        if self.game_state == "victory_wait":
            return

        self.victory = True
        self.victory_timer = 90
        self.enemy_shots = []
        self.hazards.clear()
        self.game_state = "victory_wait"

    def calc_stars(self):
        if self.hits_taken == 0:
            return 3
        if self.hits_taken == 1:
            return 2
        return 1

    def finish_level(self):
        self.stars = self.calc_stars()
        self.level_best = self.score
        self.level_new_best = False

        if self.current_player_id and not self.score_saved:
            previous = get_level_best(self.current_player_id, self.level)

            save_score(self.current_player_id, self.score, self.level,
                       self.stars, completed=True)

            self.level_best = max(previous, self.score)
            self.level_new_best = self.score > previous
            self.highest_score = get_player_highest_score(
                self.current_player_id)

        self.score_saved = True
        self.game_state = "level_complete"


    def update(self, events):
        state = self.game_state

        if state in ("playing", "blinking"):
            self.update_playing(events)

        elif state == "victory_wait":
            self.update_effects()
            self.victory_timer -= 1
            if self.victory_timer <= 0:
                self.finish_level()

        elif state == "level_complete":
            self.update_level_complete(events)

        elif state == "paused":
            self.update_paused(events)

        elif state == "pause_settings":
            self.update_pause_settings(events)

        elif state == "confirm_exit":
            self.update_confirm_exit(events)

        elif state == "high_score":
            self.update_high_score(events)

        elif state == "game_over":
            self.update_game_over(events)


    def update_playing(self, events):
        self.update_effects()

        for event in events:
            if event.type == pygame.KEYDOWN and event.key in (
                    pygame.K_ESCAPE, pygame.K_p):
                self.game_state = "paused"
                return

            if (event.type == pygame.MOUSEBUTTONDOWN and event.button == 1
                    and self.pause_btn.collidepoint(event.pos)):
                self.game_state = "paused"
                return

        self.history.append((self.player.x, self.player.y))
        if len(self.history) > 60:
            self.history.pop(0)

        if self.game_state == "blinking":
            self.player.update_blink()
            self.blink_timer += 1

            for enemy in self.enemies:
                enemy.update()
            if self.boss:
                self.boss.update()

            if self.blink_timer >= 120:
                self.game_state = "game_over"
            return

        if self.invuln > 0:
            self.invuln -= 1
        if self.fire_cooldown > 0:
            self.fire_cooldown -= 1
        for key in self.effects:
            if self.effects[key] > 0:
                self.effects[key] -= 1

        keys = pygame.key.get_pressed()

        if keys[pygame.K_LEFT] or keys[pygame.K_a]:
            self.player.move_left()
        if keys[pygame.K_RIGHT] or keys[pygame.K_d]:
            self.player.move_right()

        fired = False

        if self.settings.get("mobile_controls", False):
            fired = self.buttons.handle_mouse(self.player, events)

        fired |= any(
            e.type == pygame.KEYDOWN and e.key == pygame.K_SPACE
            for e in events
        )
        fired |= bool(keys[pygame.K_SPACE])

        self.player.keep_inside_screen()

        if fired:
            self.fire_bullet()

        for bullet in self.bullets:
            bullet.update()
        self.bullets = [b for b in self.bullets if b.is_active]

        for pu in self.powerups:
            pu.update(self.height)
        self.powerups = [p for p in self.powerups if p.alive]

        frozen = self.effects["freeze"] > 0

        if not frozen:
            self.update_enemy_drops()
            for enemy in self.enemies:
                enemy.update()

        if self.boss:
            self.boss.update()

            if not frozen and self.boss.ready_to_fire():
                self.boss_fire()

        for shot in self.enemy_shots:
            if not frozen:
                shot.update()
        self.enemy_shots = [s for s in self.enemy_shots
                            if s.alive(self.width, self.height)]

        if not frozen:
            notice = self.hazards.update(self.player)
            if notice:
                self.add_popup(notice, self.width // 2, 190, (255, 150, 60))

        self.check_collisions()
        self.check_hazards()
        self.check_wave_clear()

    def check_hazards(self):
        if self.game_state != "playing":
            return

        for x, y, destroyed in self.hazards.hit_by_bullets(self.bullets):
            self.spawn_explosion(x, y, 0.8 if destroyed else 0.3)

            if destroyed:
                self.score += 2
                self.add_popup("+2", x, y, ui.GOLD)
                self.play("explosion")
            else:
                self.play("hit")

        self.bullets = [b for b in self.bullets if b.is_active]

        rect = self.player.get_rect().inflate(-24, -24)

        if self.invuln <= 0 and self.hazards.hits_player(rect):
            self.player_hit()

    def update_enemy_drops(self):
        if self.boss or self.level > len(LEVELS):
            return

        self.enemy_timer += 1
        cfg = LEVELS[self.level - 1]
        interval = cfg.get("drop", 170)
        at_once = 1

        if cfg.get("endless"):
            interval = max(40, 150 - self.wave * 6)
            at_once = 1 + self.wave // 8

        if self.enemy_timer >= interval:
            waiting = [e for e in self.enemies if e.state == "waiting"]

            if waiting and self.history:
                for enemy in random.sample(waiting,
                                           min(at_once, len(waiting))):
                    enemy.start_drop(*self.history[0])

            self.enemy_timer = 0

    def update_effects(self):
        for p in self.particles:
            p["x"] += p["vx"]
            p["y"] += p["vy"]
            p["vy"] += 0.05
            p["life"] -= 1
        self.particles = [p for p in self.particles if p["life"] > 0]

        for pop in self.popups:
            pop["y"] -= 0.7
            pop["life"] -= 1
        self.popups = [p for p in self.popups if p["life"] > 0]

        if self.level_banner > 0:
            self.level_banner -= 1


    def fire_bullet(self):
        rapid = self.effects["rapid"] > 0

        max_bullets = 8 if rapid else 3
        cooldown = 6 if rapid else 18

        if self.fire_cooldown > 0 or len(self.bullets) >= max_bullets:
            return

        rect = self.player.get_rect()
        self.bullets.append(Bullet(rect.centerx - 16, rect.top - 10))
        self.fire_cooldown = cooldown
        self.play("shoot")

    def boss_fire(self):
        boss = self.boss
        sx = boss.x + boss.width / 2
        sy = boss.y + boss.height - 20

        target = self.player.get_rect()
        base = math.atan2(target.centery - sy, target.centerx - sx)

        boss.volley += 1
        attack = boss.cfg["attacks"][boss.phase - 1]

        if "spread" in attack:
            count, step, speed = attack["spread"]

            for i in range(count):
                a = base + (i - (count - 1) / 2) * step
                self.enemy_shots.append(
                    EnemyShot(sx, sy, math.cos(a) * speed,
                              math.sin(a) * speed))

        if "ring" in attack:
            count, speed, every = attack["ring"]

            if boss.volley % every == 0:
                spin = boss.volley * 0.21

                for i in range(count):
                    a = spin + i * math.tau / count
                    self.enemy_shots.append(
                        EnemyShot(sx, sy, math.cos(a) * speed,
                                  math.sin(a) * speed))

        if "rain" in attack:
            count, speed = attack["rain"]

            for _ in range(count):
                self.enemy_shots.append(
                    EnemyShot(random.uniform(20, self.width - 20), -10,
                              random.uniform(-0.4, 0.4), speed))


    def check_collisions(self):
        player_rect = self.player.get_rect().inflate(-24, -24)

        for bullet in self.bullets:
            if not bullet.is_active:
                continue

            b_rect = bullet.get_rect().inflate(-8, -8)

            for enemy in self.enemies:
                if enemy.state == "offscreen":
                    continue

                if b_rect.colliderect(enemy.get_rect().inflate(-10, -10)):
                    bullet.is_active = False

                    if enemy.hit(1):
                        self.kill_enemy(enemy)
                    else:
                        self.spawn_explosion(bullet.x + 16, bullet.y, 0.3)
                        self.play("hit")
                    break

            else:
                if self.boss and not self.boss.entering:
                    if b_rect.colliderect(self.boss.get_rect()):
                        bullet.is_active = False
                        self.damage_boss(1)
                        self.spawn_explosion(bullet.x + 16, bullet.y, 0.3)

        self.bullets = [b for b in self.bullets if b.is_active]

        if self.game_state != "playing":
            return

        for enemy in self.enemies:
            if enemy.state == "offscreen":
                continue

            if player_rect.colliderect(enemy.get_rect().inflate(-16, -16)):
                self.kill_enemy(enemy, award=False, drop=False)
                self.player_hit()
                if self.game_state != "playing":
                    return

        for shot in self.enemy_shots:
            if player_rect.colliderect(shot.get_rect()):
                self.enemy_shots.remove(shot)
                self.player_hit()
                break

        for pu in self.powerups:
            if pu.alive and player_rect.inflate(30, 30).colliderect(pu.get_rect()):
                pu.alive = False
                self.apply_powerup(pu.kind)

    def kill_enemy(self, enemy, award=True, drop=True):
        enemy.state = "offscreen"
        enemy.active = False

        cx = enemy.x + enemy.width / 2
        cy = enemy.y + enemy.height / 2

        self.spawn_explosion(cx, cy)
        self.play("explosion")

        if award:
            points = getattr(enemy, "points", 1)
            self.score += points
            self.add_popup(f"+{points}", cx, cy, ui.GOLD)

        if drop and random.random() < PU_DROP_CHANCE:
            kinds, weights = zip(*PU_WEIGHTS)
            kind = random.choices(kinds, weights=weights)[0]
            self.powerups.append(PowerUp(cx, cy, kind))

    def damage_boss(self, amount):
        boss = self.boss

        if not boss:
            return

        if boss.shielded:
            self.spawn_explosion(boss.x + boss.width / 2,
                                 boss.y + boss.height / 2, 0.2, ui.NEON)
            return

        boss.hp -= amount
        boss.flash = 4

        if boss.hp <= 0:
            for _ in range(8):
                self.spawn_explosion(
                    boss.x + random.randint(0, boss.width),
                    boss.y + random.randint(0, boss.height), 1.5)

            self.play("explosion")
            self.score += boss.points
            self.add_popup(f"BOSS DEFEATED +{boss.points}",
                           self.width // 2, 240, ui.GREEN)

            self.boss = None
            self.enemy_shots = []

            if LEVELS[self.level - 1].get("endless"):
                self.spawn_wave()
            else:
                self.begin_victory()
            return

        if boss.phase != boss.last_phase:
            boss.last_phase = boss.phase
            boss.shield_time = 90
            boss.fire_timer = 0
            self.enemy_shots = []
            self.play("hit")
            self.add_popup(f"PHASE {boss.phase}!", self.width // 2, 250,
                           ui.RED)

    def player_hit(self):
        if self.invuln > 0:
            return

        rect = self.player.get_rect()

        if self.effects["shield"] > 0:
            self.effects["shield"] = 0
            self.invuln = 40
            self.spawn_explosion(rect.centerx, rect.centery, 0.6, ui.NEON)
            return

        self.lives -= 1
        self.hits_taken += 1
        self.spawn_explosion(rect.centerx, rect.centery, 1.2)
        self.play("hit")

        if self.lives <= 0:
            self.game_state = "blinking"
            self.player.is_blinking = True
            self.blink_timer = 0
            self.enemy_shots = []
        else:
            self.invuln = 120


    def apply_powerup(self, kind):
        info = PU_INFO[kind]
        rect = self.player.get_rect()

        if kind in self.effects:
            self.effects[kind] = info["duration"]

        elif kind == "life":
            self.lives = min(MAX_LIVES, self.lives + 1)

        elif kind == "blast":
            self.mega_blast()

        self.add_popup(info["label"], rect.centerx, rect.y - 10, info["color"])
        self.play("powerup")

    def mega_blast(self):
        self.spawn_explosion(self.width // 2, self.height // 2, 2.0,
                             (255, 170, 60))

        for enemy in self.enemies:
            if enemy.state != "offscreen":
                self.kill_enemy(enemy, drop=False)

        self.enemy_shots = []

        if self.boss and not self.boss.entering:
            self.damage_boss(10)


    def spawn_explosion(self, x, y, scale=1.0, color=None):
        count = max(3, int(self.quality["particles"] * scale))
        palette = [color] if color else [
            (255, 220, 90), (255, 150, 50), (255, 90, 60), (255, 255, 200)]

        for _ in range(count):
            a = random.uniform(0, math.tau)
            speed = random.uniform(1, 5) * (0.6 + scale * 0.4)
            life = random.randint(18, 38)

            self.particles.append({
                "x": x, "y": y,
                "vx": math.cos(a) * speed, "vy": math.sin(a) * speed,
                "life": life, "max": life,
                "color": random.choice(palette),
                "size": random.randint(2, 5),
            })

    def add_popup(self, text, x, y, color):
        self.popups.append({"text": text, "x": x, "y": y,
                            "color": color, "life": 60})


    def update_paused(self, events):
        for event in events:
            if event.type == pygame.KEYDOWN and event.key in (
                    pygame.K_ESCAPE, pygame.K_p):
                self.game_state = "playing"
                return

            if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                if self.resume_rect.collidepoint(event.pos):
                    self.game_state = "playing"

                elif self.settings_rect.collidepoint(event.pos):
                    self.settings_screen = Settings(
                        self.screen, self.width, self.height)
                    self.game_state = "pause_settings"

                elif self.menu_rect.collidepoint(event.pos):
                    self.game_state = "confirm_exit"
                return

    def update_pause_settings(self, events):
        self.settings_screen.handle_events(events)

        if self.settings_screen.action == "back":
            self.settings_screen = None
            self.settings = load_settings()
            apply_audio(self.settings)
            self.game_state = "paused"

    def update_confirm_exit(self, events):
        _, yes, no = ui.dialog_rects(self.width, self.height)

        for event in events:
            if event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE:
                self.game_state = "paused"
                return

            if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                if yes.collidepoint(event.pos):
                    self.go_home()
                elif no.collidepoint(event.pos):
                    self.game_state = "paused"
                return

    def update_high_score(self, events):
        for event in events:
            if (event.type == pygame.MOUSEBUTTONDOWN and event.button == 1
                    and self.continue_rect.collidepoint(event.pos)):
                self.game_state = "game_over"
                return

            if (event.type == pygame.KEYDOWN
                    and event.key in (pygame.K_RETURN, pygame.K_KP_ENTER)):
                self.game_state = "game_over"
                return

    def go_home(self):
        if self.score > 0 and not self.score_saved and self.current_player_id:
            save_score(self.current_player_id, self.score, self.level)
            self.score_saved = True

        self.game_state = "back_levels"


    def update_game_over(self, events):
        if not self.score_saved:
            if not self.victory:
                self.play("over")

            if self.current_player_id:
                previous = self.highest_score

                save_score(self.current_player_id, self.score, self.level)
                self.highest_score = get_player_highest_score(
                    self.current_player_id)

                self.new_record = self.score > previous
            else:
                self.new_record = self.score > self.highest_score
                self.highest_score = max(self.highest_score, self.score)

            self.score_saved = True

        if self.new_record and not self.high_shown:
            self.high_shown = True
            self.game_state = "high_score"
            return

        for event in events:
            if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                if self.play_again_rect.collidepoint(event.pos):
                    self.start_again(self.level)
                    return

                if self.back_home_rect.collidepoint(event.pos):
                    self.game_state = "back_levels"
                    return

            elif event.type == pygame.KEYDOWN:
                if event.key == pygame.K_RETURN:
                    self.start_again(self.level)
                    return

                if event.key == pygame.K_ESCAPE:
                    self.game_state = "back_levels"
                    return


    def update_level_complete(self, events):
        last = self.level >= len(LEVELS)

        for event in events:
            if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                if self.play_again_rect.collidepoint(event.pos):
                    self.start_again(self.level if last else self.level + 1)
                    return

                if self.back_home_rect.collidepoint(event.pos):
                    self.game_state = "back_levels"
                    return

            elif event.type == pygame.KEYDOWN:
                if event.key in (pygame.K_RETURN, pygame.K_KP_ENTER):
                    self.start_again(self.level if last else self.level + 1)
                    return

                if event.key == pygame.K_ESCAPE:
                    self.game_state = "back_levels"
                    return


    def draw(self):
        state = self.game_state

        if state == "pause_settings" and self.settings_screen:
            self.settings_screen.draw()
            return

        self.draw_playing()

        if state == "paused":
            self.draw_pause_menu()
        elif state == "confirm_exit":
            self.draw_confirm_exit()
        elif state == "high_score":
            self.draw_high_score()
        elif state == "level_complete":
            self.draw_level_complete()
        elif state == "game_over":
            self.draw_game_over()

    def draw_background(self):
        moving = self.game_state in ("playing", "blinking", "victory_wait",
                                     "level_complete", "high_score",
                                     "game_over")
        speed = 1.8 if self.game_state in ("playing", "blinking") else 1.0

        ui.draw_background(
            self.screen,
            self.width,
            self.height,
            dim=0,
            step=moving,
            speed=speed,
            planets=True,
            vignette=True,
        )

        tint = LEVELS[self.level - 1].get("tint")

        if tint:
            if self.level not in self._tint_cache:
                layer = pygame.Surface((self.width, self.height),
                                       pygame.SRCALPHA)
                layer.fill((*tint, 34))
                self._tint_cache[self.level] = layer

            self.screen.blit(self._tint_cache[self.level], (0, 0))

    def draw_playing(self):
        self.draw_background()

        for pu in self.powerups:
            pu.draw(self.screen)

        for enemy in self.enemies:
            if enemy.active and enemy.state != "offscreen":
                enemy.draw(self.screen)
                self.draw_enemy_extras(enemy)

        self.hazards.draw(self.screen)

        if self.boss:
            self.boss.draw(self.screen)

        for shot in self.enemy_shots:
            shot.draw(self.screen)

        for bullet in self.bullets:
            bullet.draw(self.screen)

        self.draw_player()

        for p in self.particles:
            size = max(1, int(p["size"] * p["life"] / p["max"]))
            pygame.draw.circle(self.screen, p["color"],
                               (int(p["x"]), int(p["y"])), size)

        for pop in self.popups:
            ui.draw_text(self.screen, pop["text"], 13, pop["color"],
                         (int(pop["x"]), int(pop["y"])), "center", True)

        self.hazards.draw_overlay(self.screen)

        if self.effects["freeze"] > 0:
            tint = pygame.Surface((self.width, self.height), pygame.SRCALPHA)
            tint.fill((120, 200, 255, 30))
            self.screen.blit(tint, (0, 0))

        self.draw_hud()
        self.draw_banner()

        if self.settings.get("mobile_controls", False):
            self.buttons.draw(self.screen)

    def draw_enemy_extras(self, enemy):
        rect = enemy.get_rect()

        if self.effects["freeze"] > 0:
            pygame.draw.rect(self.screen, (160, 235, 255), rect, 2,
                             border_radius=6)

        if getattr(enemy, "max_hp", 1) > 1:
            bar = pygame.Rect(rect.x + 10, rect.y - 8, rect.w - 20, 5)
            pygame.draw.rect(self.screen, (60, 20, 30), bar)
            fill = bar.copy()
            fill.w = int(bar.w * enemy.hp / enemy.max_hp)
            pygame.draw.rect(self.screen, ui.RED, fill)

    def draw_player(self):
        rect = self.player.get_rect()

        blink_off = (
            self.game_state == "playing"
            and self.invuln > 0
            and (self.invuln // 6) % 2 == 0
        )

        if not blink_off:
            self.player.draw(self.screen)

        shield = self.effects["shield"]
        if shield > 0 and (shield > 120 or (shield // 6) % 2 == 0):
            pygame.draw.circle(self.screen, ui.NEON, rect.center, 54, 3)
            pygame.draw.circle(self.screen, (120, 200, 255), rect.center, 58, 1)


    def hud_shape(self, pts, hover=False):
        key = tuple(pts)

        if key not in self._hud_cache:
            xs = [x for x, _ in pts]
            ys = [y for _, y in pts]
            x0, y0 = min(xs), min(ys)
            layer = pygame.Surface((max(xs) - x0 + 1, max(ys) - y0 + 1),
                                   pygame.SRCALPHA)
            pygame.draw.polygon(layer, (4, 14, 52, 190),
                                [(x - x0, y - y0) for x, y in pts])
            self._hud_cache[key] = (layer, (x0, y0))

        layer, pos = self._hud_cache[key]
        self.screen.blit(layer, pos)

        pygame.draw.polygon(self.screen, (20, 70, 160), pts, 4)
        pygame.draw.polygon(self.screen, ui.CYAN if hover else ui.NEON,
                            pts, 2)

    def hud_box(self, rect, hover=False):
        self.hud_shape(ui.chamfer(rect, 8), hover)

    def draw_hud(self):
        endless = LEVELS[self.level - 1].get("endless")
        w = self.width

        score = pygame.Rect(8, 12, 164, 32)
        self.hud_shape([(score.x, score.y), (score.right - 12, score.y),
                        (score.right, score.y + 12),
                        (score.right, score.bottom),
                        (score.x, score.bottom)])
        ui.draw_text(self.screen, "SCORE", 11, ui.GRAY,
                     (score.x + 12, score.centery), "midleft", True)
        ui.draw_text(self.screen, f"{self.score:06d}", 18, ui.WHITE,
                     (score.x + 66, score.centery), "midleft", True)

        ui.draw_text(self.screen, "LIVES", 10, ui.GRAY, (w // 2, 6),
                     "midtop", True)
        gap = 28
        x0 = w // 2 - ((self.lives - 1) * gap) // 2
        for i in range(self.lives):
            draw_heart(self.screen, x0 + i * gap, 30, (70, 170, 255),
                       scale=0.95)

        ui.add_click_area(self.pause_btn)
        hover = self.pause_btn.collidepoint(pygame.mouse.get_pos())
        self.hud_box(self.pause_btn, hover)

        color = ui.CYAN if hover else ui.WHITE
        cx, cy = self.pause_btn.center
        pygame.draw.rect(self.screen, color, (cx - 7, cy - 8, 5, 16))
        pygame.draw.rect(self.screen, color, (cx + 2, cy - 8, 5, 16))

        level = pygame.Rect(0, 12, 100, 32)
        level.right = self.pause_btn.x - 8
        self.hud_shape([(level.x + 12, level.y), (level.right, level.y),
                        (level.right, level.bottom), (level.x, level.bottom),
                        (level.x, level.y + 12)])
        ui.draw_text(self.screen, "WAVE" if endless else "LEVEL", 11,
                     ui.GRAY, (level.x + 14, level.centery), "midleft", True)
        ui.draw_text(self.screen, f"{self.wave if endless else self.level}",
                     20, ui.WHITE, (level.right - 12, level.centery),
                     "midright", True)

        if self.boss:
            self.draw_boss_bar()

        self.draw_effects_panel()

    def draw_boss_bar(self):
        boss = self.boss
        w, h = 360, 12
        x = (self.width - w) // 2
        y = 68

        hp = max(0, int(math.ceil(boss.hp)))

        ui.draw_text(self.screen, "BOSS", 11, ui.WHITE,
                     (self.width // 2, 52), "midtop", True)
        ui.draw_text(self.screen, f"{hp}/{boss.max_hp}", 11, ui.RED,
                     (x + w, 52), "topright", True)

        pygame.draw.rect(self.screen, (50, 10, 20), (x, y, w, h),
                         border_radius=6)

        fill = int(w * hp / boss.max_hp)
        if fill > 0:
            pygame.draw.rect(self.screen, ui.RED, (x, y, fill, h),
                             border_radius=6)

        for i in range(1, boss.phases):
            tx = x + int(w * (1 - i / boss.phases))
            pygame.draw.line(self.screen, (255, 210, 215), (tx, y + 1),
                             (tx, y + h - 2), 1)

        pygame.draw.rect(self.screen, (255, 150, 160), (x, y, w, h), 1,
                         border_radius=6)

    def draw_effects_panel(self):
        y = 60

        for kind in ("rapid", "shield", "freeze"):
            frames = self.effects[kind]
            if frames <= 0:
                continue

            info = PU_INFO[kind]

            icon = pygame.Surface((26, 26), pygame.SRCALPHA)
            draw_powerup_icon(icon, kind, 13, 13, info["color"])
            icon = pygame.transform.smoothscale(icon, (12, 12))

            icon_x = self.width - 14 - 12
            self.screen.blit(icon, (icon_x, y))

            track_w = 34
            bx = icon_x - 6 - track_w
            by = y + 4

            pygame.draw.rect(self.screen, (40, 50, 80),
                             (bx, by, track_w, 4), border_radius=2)

            fill = int(track_w * frames / info["duration"])
            if fill > 0:
                pygame.draw.rect(self.screen, info["color"],
                                 (bx, by, fill, 4), border_radius=2)

            y += 16

    def draw_banner(self):
        if self.level_banner <= 0 or self.game_state != "playing":
            return

        cfg = LEVELS[self.level - 1]
        cy = self.height // 2 - 80

        if cfg.get("endless") and not self.boss:
            ui.draw_glow_text(self.screen, f"WAVE {self.wave}", 18,
                              ui.WHITE, (self.width // 2, cy))
            ui.draw_text(self.screen, "ENDLESS MODE", 11, ui.GRAY,
                         (self.width // 2, cy + 26), "midtop", True)

            if self.hazards.label:
                ui.draw_text(self.screen, "HAZARD: " + self.hazards.label,
                             11, ui.GOLD, (self.width // 2, cy + 44),
                             "midtop", True)
        elif cfg.get("boss") or self.boss:
            phases = (self.boss.phases if self.boss
                      else len(cfg["boss"]["attacks"]))
            ui.draw_glow_text(self.screen, "WARNING!", 20, ui.RED,
                              (self.width // 2, cy), glow=(90, 10, 30))
            ui.draw_text(self.screen, f"BOSS BATTLE - {phases} PHASES", 11,
                         ui.WHITE, (self.width // 2, cy + 26), "midtop", True)
        else:
            ui.draw_glow_text(self.screen, f"LEVEL {self.level}", 18,
                              ui.WHITE, (self.width // 2, cy))
            ui.draw_text(self.screen, cfg["name"].upper(), 11, ui.GRAY,
                         (self.width // 2, cy + 26), "midtop", True)

            if self.hazards.label:
                ui.draw_text(self.screen, "HAZARD: " + self.hazards.label,
                             11, ui.GOLD, (self.width // 2, cy + 44),
                             "midtop", True)


    def dim_screen(self, alpha=160):
        dim = pygame.Surface((self.width, self.height), pygame.SRCALPHA)
        dim.fill((0, 0, 12, alpha))
        self.screen.blit(dim, (0, 0))

    def draw_pause_menu(self):
        self.dim_screen()
        ui.draw_panel(self.screen, self.pause_panel, alpha=240)

        ui.draw_glow_text(self.screen, "GAME PAUSED", 30, ui.WHITE,
                          (self.pause_panel.centerx, self.pause_panel.y + 28))

        ui.draw_button(self.screen, self.resume_rect, "RESUME", True, "play")
        ui.draw_button(self.screen, self.settings_rect, "SETTINGS", True, "gear")
        ui.draw_button(self.screen, self.menu_rect, "MISSION SELECT", True,
                       "back")


    def draw_confirm_exit(self):
        ui.draw_dialog(
            self.screen, self.width, self.height, "alert",
            ["Leave this mission and go", "back to mission select?"],
            "YES", "CANCEL"
        )

    def draw_high_score(self):
        self.dim_screen(170)

        p = self.high_panel
        ui.draw_panel(self.screen, p, alpha=245)

        ui.draw_invader(self.screen, p.centerx, p.y - 30, 6, ui.CYAN)

        ui.draw_glow_text(self.screen, "New High Score!", 28, ui.WHITE,
                          (p.centerx, p.y + 40))

        ui.draw_text(self.screen, f"Score:  {self.score}", 24, ui.WHITE,
                     (p.centerx, p.y + 108), "midtop", True)
        if LEVELS[self.level - 1].get("endless"):
            ui.draw_text(self.screen, f"Wave:  {self.wave}", 22, ui.WHITE,
                         (p.centerx, p.y + 148), "midtop", True)
        else:
            ui.draw_text(self.screen, f"Level:  {self.level}", 22, ui.WHITE,
                         (p.centerx, p.y + 148), "midtop", True)

        ui.draw_button(self.screen, self.continue_rect, "CONTINUE", True)

    def draw_game_over(self):
        self.dim_screen(170)

        p = self.over_panel
        LIGHT = (120, 225, 255)
        LINE = (40, 140, 255)

        ui.draw_panel(self.screen, p, alpha=245)

        title_y = p.y + 26

        if self.victory:
            ui.draw_glow_text(self.screen, "VICTORY!", 34, (170, 255, 210),
                              (p.centerx, title_y), glow=(10, 100, 70))
            ui.draw_text(self.screen, "You defeated the Boss!", 13, ui.WHITE,
                         (p.centerx, p.y + 70), "midtop")
        else:
            ui.draw_glow_text(self.screen, "GAME OVER", 34, (255, 60, 70),
                              (p.centerx, title_y), glow=(90, 0, 10))

        ui.draw_invader(self.screen, p.x + 70, title_y + 6, 3, ui.RED)
        ui.draw_invader(self.screen, p.right - 70, title_y + 6, 3, ui.RED)

        card = pygame.Rect(p.x + 36, p.y + 98, p.w - 72, 150)
        pygame.draw.rect(self.screen, (4, 12, 48), card, border_radius=12)
        pygame.draw.rect(self.screen, LINE, card, 2, border_radius=12)

        ui.draw_text(self.screen, "Final Score", 13, LIGHT,
                     (card.centerx, card.y + 10), "midtop", True)
        ui.draw_text(self.screen, self.score, 38, ui.WHITE,
                     (card.centerx, card.y + 28), "midtop", True)

        pygame.draw.line(self.screen, LINE, (card.x + 20, card.y + 84),
                         (card.right - 20, card.y + 84), 2)
        pygame.draw.line(self.screen, LINE, (card.centerx, card.y + 92),
                         (card.centerx, card.bottom - 12), 1)

        left_cx = card.x + card.w // 4
        right_cx = card.x + card.w * 3 // 4

        endless = LEVELS[self.level - 1].get("endless")

        ui.draw_text(self.screen, "Wave" if endless else "Mission", 13,
                     LIGHT, (left_cx, card.y + 94), "midtop", True)
        ui.draw_text(self.screen, self.wave if endless else self.level, 22,
                     ui.WHITE, (left_cx, card.y + 114), "midtop", True)

        ui.draw_text(self.screen, "Best Score", 13, LIGHT,
                     (right_cx, card.y + 94), "midtop", True)
        ui.draw_text(self.screen, self.highest_score, 22,
                     ui.GOLD if self.new_record else ui.WHITE,
                     (right_cx, card.y + 114), "midtop", True)

        if self.new_record:
            ui.draw_text(self.screen, "NEW HIGH SCORE!", 13, ui.GOLD,
                         (p.centerx, card.bottom + 10), "midtop", True)

        ui.draw_button(self.screen, self.play_again_rect, "RETRY",
                       True, "play")
        ui.draw_button(self.screen, self.back_home_rect, "MISSION SELECT",
                       False, "back")


    def draw_level_complete(self):
        self.dim_screen(170)

        p = self.over_panel
        last = self.level >= len(LEVELS)
        final = last or bool(LEVELS[self.level - 1].get("final"))
        LIGHT = (120, 225, 255)
        LINE = (40, 140, 255)

        ui.draw_panel(self.screen, p, alpha=245)

        ui.draw_glow_text(self.screen, "VICTORY!" if final else
                          "MISSION COMPLETE", 34 if final else 26,
                          (170, 255, 210), (p.centerx, p.y + 26),
                          glow=(10, 100, 70))

        name = LEVELS[self.level - 1]["name"].upper()
        ui.draw_text(self.screen, f"MISSION {self.level:02d} - {name}", 13,
                     ui.WHITE, (p.centerx, p.y + 70), "midtop", True)

        draw_stars(self.screen, p.centerx, p.y + 122, self.stars, size=24)

        card = pygame.Rect(p.x + 36, p.y + 160, p.w - 72, 96)
        pygame.draw.rect(self.screen, (4, 12, 48), card, border_radius=12)
        pygame.draw.rect(self.screen, LINE, card, 2, border_radius=12)
        pygame.draw.line(self.screen, LINE, (card.centerx, card.y + 12),
                         (card.centerx, card.bottom - 12), 1)

        left_cx = card.x + card.w // 4
        right_cx = card.x + card.w * 3 // 4

        ui.draw_text(self.screen, "Score", 13, LIGHT,
                     (left_cx, card.y + 14), "midtop", True)
        ui.draw_text(self.screen, self.score, 30, ui.WHITE,
                     (left_cx, card.y + 40), "midtop", True)

        ui.draw_text(self.screen, "Best Score", 13, LIGHT,
                     (right_cx, card.y + 14), "midtop", True)
        ui.draw_text(self.screen, self.level_best, 30,
                     ui.GOLD if self.level_new_best else ui.WHITE,
                     (right_cx, card.y + 40), "midtop", True)

        if self.level_new_best:
            ui.draw_text(self.screen, "NEW BEST!", 13, ui.GOLD,
                         (p.centerx, card.bottom + 6), "midtop", True)

        if last:
            ui.draw_button(self.screen, self.play_again_rect, "PLAY AGAIN",
                           True, "play")
        elif final:
            ui.draw_button(self.screen, self.play_again_rect, "ENDLESS MODE",
                           True, "play")
        else:
            ui.draw_button(self.screen, self.play_again_rect,
                           "NEXT MISSION", True, "play")

        ui.draw_button(self.screen, self.back_home_rect, "MISSION SELECT",
                       False, "back")