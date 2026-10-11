import math
import os
import random

import pygame

from settings_manager import load_settings
from managers.space3d import Space3D

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
IMG_DIR = os.path.join(ROOT, "assets", "images")
FONT_DIR = os.path.join(ROOT, "assets", "fonts")

BLACK = (2, 5, 18)
PANEL = (5, 16, 56)
INPUT = (4, 14, 48)
BLUE = (30, 110, 255)
NEON = (40, 180, 255)
CYAN = (40, 245, 255)
WHITE = (235, 250, 255)
GRAY = (130, 175, 210)
RED = (255, 90, 110)
GREEN = (80, 255, 170)
GOLD = (255, 200, 60)
SILVER = (200, 210, 225)
BRONZE = (215, 135, 70)

FONT_NAMES = "orbitron,exo2,bahnschrift,segoeui,trebuchetms,consolas"
CUSTOM_FONTS = ("Orbitron.ttf", "orbitron.ttf", "Orbitron-Bold.ttf",
                "Exo2.ttf", "exo2.ttf")

_fonts = {}
_custom_path = None
_custom_checked = False


def _custom_font_path():
    global _custom_path, _custom_checked

    if not _custom_checked:
        _custom_checked = True
        for name in CUSTOM_FONTS:
            path = os.path.join(FONT_DIR, name)
            if os.path.exists(path):
                _custom_path = path
                break

    return _custom_path


def font(size, bold=False, italic=False):
    key = (size, bold, italic)

    if key not in _fonts:
        path = _custom_font_path()

        try:
            if path:
                f = pygame.font.Font(path, size)
                f.set_bold(bold)
            else:
                f = pygame.font.SysFont(FONT_NAMES, size, bold=bold)
        except Exception:
            f = pygame.font.SysFont("consolas", size, bold=bold)

        if italic:
            f.set_italic(True)

        _fonts[key] = f

    return _fonts[key]


def draw_text(screen, text, size, color, pos, anchor="topleft", bold=False):
    surf = font(size, bold).render(str(text), True, color)
    rect = surf.get_rect(**{anchor: pos})
    screen.blit(surf, rect)
    return rect


def draw_glow_text(screen, text, size, color, pos, anchor="midtop",
                   glow=(10, 70, 200)):
    f = font(size, True)
    base = f.render(str(text), True, color)
    shadow = f.render(str(text), True, glow)
    rect = base.get_rect(**{anchor: pos})

    for dx, dy in ((-2, 0), (2, 0), (0, -2), (0, 2), (2, 2), (-2, 2),
                   (2, -2), (-2, -2)):
        screen.blit(shadow, rect.move(dx, dy))

    screen.blit(base, rect)
    return rect


def fit_text(text, fnt, max_w):
    text = str(text)
    if fnt.size(text)[0] <= max_w:
        return text
    while text and fnt.size(text + "...")[0] > max_w:
        text = text[:-1]
    return text + "..."


_img_cache = {}


def load_image(name, size=None):
    key = (name, size)
    if key in _img_cache:
        return _img_cache[key]

    img = None
    path = os.path.join(IMG_DIR, name)
    if os.path.exists(path):
        try:
            img = pygame.image.load(path).convert_alpha()
            if size:
                img = pygame.transform.smoothscale(img, size)
        except pygame.error as e:
            print("IMAGE ERROR:", name, e)
            img = None

    _img_cache[key] = img
    return img


def find_image(names):
    if isinstance(names, str):
        names = [names]

    for name in names or []:
        path = os.path.join(IMG_DIR, name)
        if os.path.exists(path):
            return path
    return None


GAME_BG = "rogame.png"
BG_NAMES = ["background.png", "background.jpg", "background.jpeg",
            "bg.png", "bg.jpg", "bg.jpeg"]

_space = None
_bg_cache = {}
_overlay_cache = {}
_live = None
_level_bg = None


def set_level_background(level):
    global _level_bg
    _level_bg = f"rogame{level}.png" if level else None


def get_space(w=1000, h=680):
    global _space

    if _space is None:
        _space = Space3D(w, h)
    return _space


def _background_image(w, h, names=None, fallback=True):
    if isinstance(names, str):
        names = [names]

    names = list(names or []) + (BG_NAMES if fallback else [])
    key = (w, h, tuple(names))

    if key not in _bg_cache:
        img = None
        path = find_image(names)

        if path:
            try:
                raw = pygame.image.load(path).convert()
                rw, rh = raw.get_size()
                k = max(w / rw, h / rh)
                size = (max(w, int(rw * k)), max(h, int(rh * k)))
                raw = pygame.transform.smoothscale(raw, size)

                img = pygame.Surface((w, h))
                img.blit(raw, ((w - size[0]) // 2, (h - size[1]) // 2))

            except pygame.error as e:
                print("BACKGROUND IMAGE ERROR:", e)
                img = None

        _bg_cache[key] = img

    return _bg_cache[key]


def _draw_twinkle(screen, w, h):
    global _live

    now = pygame.time.get_ticks()

    if _live is None:
        rng = random.Random(7)
        stars = []
        for _ in range(90):
            stars.append({
                "x": rng.randint(0, w - 1), "y": rng.randint(0, h - 1),
                "size": rng.choice((1, 1, 1, 2)),
                "ph": rng.uniform(0, 6.28), "sp": rng.uniform(1.2, 3.4),
                "col": rng.choice(((200, 230, 255), (120, 230, 255),
                                   (190, 170, 255))),
            })

        flares = [(rng.uniform(0.05, 0.95), rng.uniform(0.05, 0.95),
                   rng.uniform(0, 6.28), rng.uniform(6, 12),
                   rng.uniform(0.6, 1.4)) for _ in range(12)]

        _live = {"stars": stars, "flares": flares}

    t = now / 1000.0

    for s in _live["stars"]:
        b = 0.15 + 0.85 * (0.5 + 0.5 * math.sin(t * s["sp"] + s["ph"]))
        col = tuple(int(c * b) for c in s["col"])

        if s["size"] > 1:
            pygame.draw.circle(screen, col, (s["x"], s["y"]), 1)
            if b > 0.7:
                screen.set_at((s["x"], s["y"]), (255, 255, 255))
        else:
            screen.set_at((s["x"], s["y"]), col)

    for fx, fy, ph, size, spd in _live["flares"]:
        pulse = 0.5 + 0.5 * math.sin(t * spd * 2 + ph)
        if pulse > 0.2:
            Space3D._sparkle(screen, int(fx * w), int(fy * h), size, pulse)


def draw_background(screen, w, h, dim=0, image=None, step=None,
                    speed=None, planets=True, live=False, scene3d=None,
                    **extra):
    if scene3d is None:
        if image is None:
            scene3d = True

            for name in ([_level_bg] if _level_bg else []) + [GAME_BG]:
                if _background_image(w, h, name, False) is not None:
                    image = name
                    live = True
                    scene3d = False
                    break
        else:
            scene3d = False

    if scene3d:
        get_space(w, h).draw(
            screen,
            step=True if step is None else step,
            speed=1.0 if speed is None else speed,
            planets=planets,
            vignette=extra.get("vignette", True),
        )
    else:
        bg = _background_image(w, h, image)

        if bg is not None:
            screen.blit(bg, (0, 0))
            get_space(w, h).tick()
        else:
            get_space(w, h).draw_static(screen)

        if live:
            _draw_twinkle(screen, w, h)

    if dim > 0:
        key = (w, h, dim)
        if key not in _overlay_cache:
            overlay = pygame.Surface((w, h), pygame.SRCALPHA)
            overlay.fill((0, 5, 25, dim))
            _overlay_cache[key] = overlay
        screen.blit(_overlay_cache[key], (0, 0))


MUSIC_FILES = ["romusic.mp3", "romusic.ogg", "romusic.wav", "rosound.mp3"]
CLICK_FILE = "robutton.mp3"
SHOOT_FILE = "rollet.mp3"
OVER_FILE = "rover.mp3"

SOUND_DIRS = [
    os.path.join(ROOT, "assets", "sounds"),
    os.path.join(ROOT, "assets", "audio"),
    os.path.join(ROOT, "assets", "music"),
    os.path.join(ROOT, "assets"),
    ROOT,
]

_sound_cache = {}
_click_areas = []
_click_warned = False
_last_click = -1000


_SKIP_DIRS = {"venv", ".venv", "env", ".git", "__pycache__", "node_modules"}


def find_sound(name):
    for folder in SOUND_DIRS:
        path = os.path.join(folder, name)
        if os.path.exists(path):
            return path

    stem = os.path.splitext(name)[0].lower()
    wanted = {name.lower()} | {stem + ext for ext in (".mp3", ".wav", ".ogg")}

    for folder, dirs, files in os.walk(ROOT):
        dirs[:] = [d for d in dirs if d.lower() not in _SKIP_DIRS]

        for file in files:
            if file.lower() in wanted:
                return os.path.join(folder, file)

    return None


def load_sound(name):
    if name in _sound_cache:
        return _sound_cache[name]

    snd = None

    if pygame.mixer.get_init():
        path = find_sound(name)
        if path:
            try:
                snd = pygame.mixer.Sound(path)
            except pygame.error as e:
                print("SOUND ERROR:", name, e)
        else:
            print("SOUND NOT FOUND:", name)

    _sound_cache[name] = snd
    return snd


def start_music():
    if not pygame.mixer.get_init():
        return

    path = None
    for name in MUSIC_FILES:
        path = find_sound(name)
        if path:
            break

    if not path:
        print("MUSIC NOT FOUND:", MUSIC_FILES[0])
        return

    try:
        pygame.mixer.music.load(path)
        pygame.mixer.music.play(-1)
    except pygame.error as e:
        print("MUSIC ERROR:", e)


def play_click():
    global _last_click

    now = pygame.time.get_ticks()
    if now - _last_click < 80:
        return
    _last_click = now

    settings = load_settings()

    if not settings.get("sound_enabled", True):
        return

    snd = load_sound(CLICK_FILE)
    if snd:
        snd.set_volume(settings.get("sound_volume", 80) / 100)
        snd.play()
    else:
        global _click_warned
        if not _click_warned:
            _click_warned = True
            print("CLICK SOUND NOT PLAYING: robutton.mp3 was not loaded "
                  "(check the SOUND messages above)")


def add_click_area(rect):
    _click_areas.append(rect)


def clear_click_areas():
    _click_areas.clear()


def play_click_if_button(pos):
    for rect in _click_areas:
        if rect.collidepoint(pos):
            play_click()
            return


def lerp_color(a, b, t):
    return tuple(int(a[i] + (b[i] - a[i]) * t) for i in range(3))


def vgradient(size, stops):
    w, h = size
    surf = pygame.Surface(size, pygame.SRCALPHA)

    for y in range(h):
        t = y / max(1, h - 1)

        for i in range(len(stops) - 1):
            t0, c0 = stops[i]
            t1, c1 = stops[i + 1]
            if t0 <= t <= t1:
                k = (t - t0) / max(0.0001, t1 - t0)
                pygame.draw.line(surf, lerp_color(c0, c1, k), (0, y), (w, y))
                break

    return surf


def chamfer(rect, c):
    x, y, r, b = rect.left, rect.top, rect.right - 1, rect.bottom - 1
    return [(x + c, y), (r - c, y), (r, y + c), (r, b - c),
            (r - c, b), (x + c, b), (x, b - c), (x, y + c)]


def brighten(color, amount):
    return tuple(min(255, c + amount) for c in color)


_panel_cache = {}


def panel_surface(size, alpha=215, cut=14):
    key = (size, alpha, cut)
    if key in _panel_cache:
        return _panel_cache[key]

    w, h = size
    pad = 12
    surf = pygame.Surface((w + pad * 2, h + pad * 2), pygame.SRCALPHA)
    body = pygame.Rect(pad, pad, w, h)

    for i in range(9, 0, -1):
        a = max(4, 62 - i * 6)
        pygame.draw.polygon(surf, (40, 150, 255, a),
                            chamfer(body.inflate(i * 2, i * 2), cut + i), 2)

    fill = vgradient((w, h), [(0.0, (14, 44, 118)), (0.45, (6, 20, 70)),
                              (1.0, (3, 10, 42))])
    fill.fill((255, 255, 255, alpha), special_flags=pygame.BLEND_RGBA_MIN)

    mask = pygame.Surface((w, h), pygame.SRCALPHA)
    pygame.draw.polygon(mask, (255, 255, 255, 255),
                        chamfer(pygame.Rect(0, 0, w, h), cut))
    fill.blit(mask, (0, 0), special_flags=pygame.BLEND_RGBA_MIN)
    surf.blit(fill, (pad, pad))

    pygame.draw.polygon(surf, (70, 205, 255), chamfer(body, cut), 2)
    pygame.draw.polygon(surf, (28, 100, 220),
                        chamfer(body.inflate(-12, -12), max(4, cut - 5)), 1)

    pts = chamfer(body, cut)
    for a, b in ((0, 7), (1, 2), (3, 4), (5, 6)):
        pygame.draw.line(surf, (190, 250, 255), pts[a], pts[b], 3)

    _panel_cache[key] = surf
    return surf


def draw_panel(screen, rect, title=None, alpha=215):
    screen.blit(panel_surface(rect.size, alpha), (rect.x - 12, rect.y - 12))

    if title:
        label = font(17, True).render(title, True, WHITE)
        tab = pygame.Rect(0, 0, label.get_width() + 60, 34)
        tab.center = (rect.centerx, rect.y)
        screen.blit(panel_surface(tab.size, 252, 10),
                    (tab.x - 12, tab.y - 12))
        screen.blit(label, label.get_rect(center=tab.center))


def draw_header(screen, w, title, y=20, icon=None):
    f = font(28, True)
    tw = f.size(title)[0]
    extra = 64 if icon else 0
    tab = pygame.Rect(0, 0, max(250, tw + 80 + extra), 54)
    tab.midtop = (w // 2, y)

    screen.blit(panel_surface(tab.size, 240, 16), (tab.x - 12, tab.y - 12))

    tx = tab.centerx

    if icon:
        cx, cy = tab.x + 38, tab.centery
        pygame.draw.circle(screen, (4, 20, 70), (cx, cy), 20)
        pygame.draw.circle(screen, NEON, (cx, cy), 20, 2)
        pygame.draw.circle(screen, (30, 100, 220), (cx, cy), 16, 1)
        draw_icon(screen, icon, cx, cy, WHITE)
        tx = tab.centerx + 26

    draw_glow_text(screen, title, 28, WHITE, (tx, tab.centery - 18))


_btn_cache = {}


def button_surface(size, kind, state):
    key = (size, kind, state)
    if key in _btn_cache:
        return _btn_cache[key]

    w, h = size
    pad = 9
    radius = min(18, h // 2)
    surf = pygame.Surface((w + pad * 2, h + pad * 2), pygame.SRCALPHA)
    body = pygame.Rect(pad, pad, w, h)
    hover = state in ("hover", "down")

    if kind == "primary":
        stops = [(0.0, (95, 215, 255)), (0.5, (25, 135, 255)),
                 (1.0, (8, 70, 215))]
        border = (175, 242, 255)
        glow = (40, 170, 255)
        glow_a = 20 if hover else 11
    elif kind == "secondary":
        stops = [(0.0, (16, 58, 140)), (1.0, (5, 22, 72))]
        border = CYAN if hover else (45, 150, 245)
        glow = (40, 150, 255)
        glow_a = 15 if hover else 7
    else:
        stops = [(0.0, (32, 44, 70)), (1.0, (14, 22, 42))]
        border = (60, 80, 115)
        glow = (40, 60, 100)
        glow_a = 0

    if hover and kind != "disabled":
        stops = [(t, brighten(c, 34 if kind == "primary" else 18))
                 for t, c in stops]

    if state == "down":
        stops = [(t, tuple(int(v * 0.82) for v in c)) for t, c in stops]

    for i in range(6, 0, -1):
        if glow_a:
            pygame.draw.rect(surf, glow + (glow_a * (7 - i),),
                             body.inflate(i * 2, i * 2), 2,
                             border_radius=radius + i)

    fill = vgradient((w, h), stops)
    mask = pygame.Surface((w, h), pygame.SRCALPHA)
    pygame.draw.rect(mask, (255, 255, 255, 255), mask.get_rect(),
                     border_radius=radius)
    fill.blit(mask, (0, 0), special_flags=pygame.BLEND_RGBA_MIN)
    surf.blit(fill, (pad, pad))

    if kind == "primary":
        gloss = pygame.Surface((w - 10, h // 2 - 2), pygame.SRCALPHA)
        pygame.draw.rect(gloss, (255, 255, 255, 62), gloss.get_rect(),
                         border_radius=max(4, radius - 4))
        surf.blit(gloss, (pad + 5, pad + 3))

    pygame.draw.rect(surf, border, body, 2, border_radius=radius)

    _btn_cache[key] = surf
    return surf


def draw_button(screen, rect, text, primary=False, icon=None, enabled=True):
    hover = enabled and rect.collidepoint(pygame.mouse.get_pos())
    down = hover and pygame.mouse.get_pressed()[0]

    if enabled:
        add_click_area(rect)

    kind = "disabled" if not enabled else ("primary" if primary else "secondary")
    state = "down" if down else ("hover" if hover else "normal")

    screen.blit(button_surface(rect.size, kind, state), (rect.x - 9, rect.y - 9))

    size = 18 if rect.h >= 40 else 15
    color = WHITE if enabled else GRAY
    f = font(size, True)
    label = f.render(text, True, color)
    shadow = f.render(text, True, (0, 40, 130) if primary else (0, 10, 40))
    off = 1 if down else 0

    if icon:
        total = label.get_width() + 34
        start = rect.centerx - total // 2
        draw_icon(screen, icon, start + 11, rect.centery + off, color)
        pos = (start + 34, rect.centery - label.get_height() // 2 + off)
    else:
        pos = (rect.centerx - label.get_width() // 2,
               rect.centery - label.get_height() // 2 + off)

    screen.blit(shadow, (pos[0], pos[1] + 1))
    screen.blit(label, pos)


def eye_rect(rect):
    return pygame.Rect(rect.right - 44, rect.y, 44, rect.height)


def draw_input(screen, rect, text, placeholder, icon, active,
               secret=False, show=False):
    add_click_area(rect)
    pygame.draw.rect(screen, INPUT, rect, border_radius=8)

    if active:
        pygame.draw.rect(screen, (20, 120, 200), rect.inflate(6, 6), 2,
                         border_radius=10)

    pygame.draw.rect(screen, CYAN if active else (40, 125, 225), rect, 2,
                     border_radius=8)

    draw_icon(screen, icon, rect.x + 24, rect.centery,
              CYAN if active else GRAY)

    f = font(16)
    avail = rect.w - 48 - (44 if secret else 8) - 8

    if text:
        shown = text if (not secret or show) else "*" * len(text)
        while shown and f.size(shown)[0] > avail:
            shown = shown[1:]
        surf = f.render(shown, True, WHITE)
    else:
        surf = f.render(placeholder, True, (110, 150, 195))

    pos = (rect.x + 48, rect.centery - surf.get_height() // 2)
    screen.blit(surf, pos)

    if active and (pygame.time.get_ticks() // 500) % 2 == 0:
        cx = pos[0] + (surf.get_width() if text else 0) + 2
        pygame.draw.line(screen, CYAN, (cx, rect.centery - 10),
                         (cx, rect.centery + 10), 2)

    if secret:
        add_click_area(eye_rect(rect))
        hot = show or eye_rect(rect).collidepoint(pygame.mouse.get_pos())
        draw_icon(screen, "eye" if show else "eye_off",
                  rect.right - 24, rect.centery, CYAN if hot else GRAY)


def draw_code_input(screen, rect, text, active, length=6):
    add_click_area(rect)
    box_w, gap = 44, 10
    total = length * box_w + (length - 1) * gap
    x0 = rect.centerx - total // 2
    current = min(len(text), length - 1)

    for i in range(length):
        box = pygame.Rect(x0 + i * (box_w + gap), rect.y, box_w, rect.h)
        filled = i < len(text)
        is_current = active and i == current

        pygame.draw.rect(screen, INPUT, box, border_radius=8)

        if is_current:
            border = CYAN
        elif filled:
            border = NEON
        else:
            border = (40, 120, 220)
        pygame.draw.rect(screen, border, box, 2, border_radius=8)

        if filled:
            surf = font(24, True).render(text[i], True, WHITE)
            screen.blit(surf, surf.get_rect(center=box.center))
        elif is_current and (pygame.time.get_ticks() // 500) % 2 == 0:
            pygame.draw.line(screen, CYAN, (box.centerx, box.centery - 10),
                             (box.centerx, box.centery + 10), 2)


def draw_checkbox(screen, rect, checked):
    pygame.draw.rect(screen, INPUT, rect, border_radius=4)
    pygame.draw.rect(screen, CYAN if checked else (40, 120, 220), rect, 2,
                     border_radius=4)
    if checked:
        pygame.draw.lines(screen, CYAN, False, [
            (rect.x + 5, rect.centery),
            (rect.x + 10, rect.bottom - 6),
            (rect.right - 5, rect.y + 6),
        ], 3)


def draw_toggle(screen, rect, on):
    r = rect.h // 2

    if on:
        fill = vgradient(rect.size, [(0.0, (80, 215, 255)),
                                     (1.0, (20, 120, 240))])
        mask = pygame.Surface(rect.size, pygame.SRCALPHA)
        pygame.draw.rect(mask, (255, 255, 255, 255), mask.get_rect(),
                         border_radius=r)
        fill.blit(mask, (0, 0), special_flags=pygame.BLEND_RGBA_MIN)
        screen.blit(fill, rect.topleft)
        pygame.draw.rect(screen, (170, 240, 255), rect, 2, border_radius=r)
    else:
        pygame.draw.rect(screen, (18, 30, 62), rect, border_radius=r)
        pygame.draw.rect(screen, (70, 95, 140), rect, 2, border_radius=r)

    knob_x = rect.right - r if on else rect.x + r
    pygame.draw.circle(screen, WHITE if on else GRAY, (knob_x, rect.centery),
                       r - 4)

    draw_text(screen, "ON" if on else "OFF", 11, WHITE,
              (rect.x + 10, rect.centery) if on
              else (rect.right - 10, rect.centery),
              "midleft" if on else "midright", True)


def draw_message(screen, text, color, cx, cy):
    if text:
        draw_text(screen, text, 14, color, (cx, cy), "center", True)


def apply_key(value, event, max_len, digits_only=False, allow_space=True):
    if event.key == pygame.K_BACKSPACE:
        return value[:-1]

    ch = event.unicode
    if ch and ch.isprintable() and len(value) < max_len:
        if digits_only and not ch.isdigit():
            return value
        if ch == " " and not allow_space:
            return value
        return value + ch
    return value


def dialog_rects(w, h):
    panel = pygame.Rect(0, 0, 440, 280)
    panel.center = (w // 2, h // 2)
    yes = pygame.Rect(panel.x + 50, panel.bottom - 112, panel.w - 100, 44)
    no = pygame.Rect(panel.x + 50, panel.bottom - 58, panel.w - 100, 40)
    return panel, yes, no


def draw_dialog(screen, w, h, icon, lines, yes_text="YES",
                no_text="CANCEL", title=None):
    dim = pygame.Surface((w, h), pygame.SRCALPHA)
    dim.fill((0, 4, 22, 175))
    screen.blit(dim, (0, 0))

    panel, yes, no = dialog_rects(w, h)
    draw_panel(screen, panel, alpha=245)

    cy = panel.y + 44
    pygame.draw.circle(screen, (4, 20, 70), (panel.centerx, cy), 26)
    pygame.draw.circle(screen, CYAN, (panel.centerx, cy), 26, 2)
    draw_icon(screen, icon, panel.centerx, cy, CYAN)

    y = panel.y + 82

    if title:
        draw_glow_text(screen, title, 22, WHITE, (panel.centerx, y))
        y += 34

    for line in lines:
        draw_text(screen, line, 16, WHITE, (panel.centerx, y), "midtop")
        y += 22

    draw_button(screen, yes, yes_text, primary=True)
    draw_button(screen, no, no_text)


def draw_icon(screen, name, cx, cy, color=CYAN):
    d = pygame.draw

    if name == "user":
        d.circle(screen, color, (cx, cy - 5), 5, 2)
        d.arc(screen, color, (cx - 9, cy + 2, 18, 14), 0, math.pi, 2)

    elif name == "lock":
        d.rect(screen, color, (cx - 7, cy - 1, 14, 10), 2, border_radius=2)
        d.arc(screen, color, (cx - 5, cy - 10, 10, 12), 0, math.pi, 2)

    elif name == "mail":
        d.rect(screen, color, (cx - 10, cy - 7, 20, 14), 2, border_radius=2)
        d.lines(screen, color, False,
                [(cx - 10, cy - 7), (cx, cy + 1), (cx + 10, cy - 7)], 2)

    elif name in ("eye", "eye_off"):
        top, bottom = [], []
        for x in range(-11, 12):
            h = 7 * (1 - (x / 11) ** 2)
            top.append((cx + x, cy - h))
            bottom.append((cx + x, cy + h))
        d.lines(screen, color, True, top + bottom[::-1], 2)
        d.circle(screen, color, (cx, cy), 3)
        if name == "eye_off":
            d.line(screen, color, (cx - 11, cy + 9), (cx + 11, cy - 9), 2)

    elif name == "key":
        d.circle(screen, color, (cx - 6, cy), 6, 2)
        d.line(screen, color, (cx, cy), (cx + 10, cy), 2)
        d.line(screen, color, (cx + 7, cy), (cx + 7, cy + 5), 2)

    elif name == "play":
        d.polygon(screen, color,
                  [(cx - 5, cy - 9), (cx - 5, cy + 9), (cx + 9, cy)])

    elif name == "board":
        d.rect(screen, color, (cx - 10, cy - 1, 6, 10), 2)
        d.rect(screen, color, (cx - 3, cy - 9, 6, 18), 2)
        d.rect(screen, color, (cx + 4, cy - 5, 6, 14), 2)

    elif name == "crown":
        d.polygon(screen, color, [(cx - 10, cy + 6), (cx - 10, cy - 6),
                                  (cx - 4, cy), (cx, cy - 9), (cx + 4, cy),
                                  (cx + 10, cy - 6), (cx + 10, cy + 6)], 2)
        d.line(screen, color, (cx - 10, cy + 10), (cx + 10, cy + 10), 2)

    elif name == "gear":
        d.circle(screen, color, (cx, cy), 6, 2)
        d.circle(screen, color, (cx, cy), 2)
        for i in range(8):
            a = i * math.pi / 4
            d.line(screen, color,
                   (cx + math.cos(a) * 7, cy + math.sin(a) * 7),
                   (cx + math.cos(a) * 11, cy + math.sin(a) * 11), 3)

    elif name == "logout":
        d.lines(screen, color, False,
                [(cx - 2, cy - 9), (cx - 10, cy - 9),
                 (cx - 10, cy + 9), (cx - 2, cy + 9)], 2)
        d.line(screen, color, (cx - 4, cy), (cx + 10, cy), 2)
        d.lines(screen, color, False,
                [(cx + 4, cy - 6), (cx + 10, cy), (cx + 4, cy + 6)], 2)

    elif name == "power":
        d.arc(screen, color, (cx - 10, cy - 9, 20, 20),
              math.pi / 2 + 0.75, math.tau + math.pi / 2 - 0.75, 3)
        d.line(screen, color, (cx, cy - 12), (cx, cy - 1), 3)

    elif name == "back":
        d.line(screen, color, (cx + 9, cy), (cx - 9, cy), 2)
        d.lines(screen, color, False,
                [(cx - 3, cy - 6), (cx - 9, cy), (cx - 3, cy + 6)], 2)

    elif name == "right":
        d.line(screen, color, (cx - 9, cy), (cx + 9, cy), 2)
        d.lines(screen, color, False,
                [(cx + 3, cy - 6), (cx + 9, cy), (cx + 3, cy + 6)], 2)

    elif name == "music":
        d.circle(screen, color, (cx - 4, cy + 6), 4, 2)
        d.line(screen, color, (cx, cy + 6), (cx, cy - 9), 2)
        d.line(screen, color, (cx, cy - 9), (cx + 7, cy - 6), 2)

    elif name == "speaker":
        d.polygon(screen, color, [(cx - 9, cy - 3), (cx - 4, cy - 3),
                                  (cx + 2, cy - 8), (cx + 2, cy + 8),
                                  (cx - 4, cy + 3), (cx - 9, cy + 3)], 2)
        d.arc(screen, color, (cx - 1, cy - 6, 12, 12), -0.9, 0.9, 2)

    elif name == "phone":
        d.rect(screen, color, (cx - 6, cy - 10, 12, 20), 2, border_radius=3)
        d.line(screen, color, (cx - 2, cy + 6), (cx + 2, cy + 6), 2)

    elif name == "screen":
        d.rect(screen, color, (cx - 10, cy - 8, 20, 13), 2, border_radius=2)
        d.line(screen, color, (cx - 5, cy + 9), (cx + 5, cy + 9), 2)

    elif name == "star":
        pts = []
        for i in range(10):
            a = -math.pi / 2 + i * math.pi / 5
            r = 10 if i % 2 == 0 else 4.5
            pts.append((cx + math.cos(a) * r, cy + math.sin(a) * r))
        d.polygon(screen, color, pts, 2)

    elif name == "home":
        d.polygon(screen, color, [(cx - 12, cy - 1), (cx, cy - 11),
                                  (cx + 12, cy - 1)])
        d.rect(screen, color, (cx - 8, cy - 1, 16, 11))
        d.rect(screen, (6, 24, 66), (cx - 2, cy + 3, 4, 7))

    elif name == "warn":
        d.polygon(screen, color, [(cx, cy - 10), (cx - 10, cy + 8),
                                  (cx + 10, cy + 8)], 2)
        d.line(screen, color, (cx, cy - 3), (cx, cy + 2), 2)
        d.circle(screen, color, (cx, cy + 5), 1)

    elif name == "alert":
        d.line(screen, color, (cx, cy - 10), (cx, cy + 2), 3)
        d.circle(screen, color, (cx, cy + 8), 2)

    elif name == "check":
        d.lines(screen, color, False, [(cx - 8, cy), (cx - 2, cy + 7),
                                       (cx + 9, cy - 7)], 3)

    elif name == "camera":
        d.rect(screen, color, (cx - 10, cy - 5, 20, 14), 2, border_radius=3)
        d.rect(screen, color, (cx - 4, cy - 8, 8, 4), 2)
        d.circle(screen, color, (cx, cy + 2), 4, 2)

    elif name == "edit":
        d.line(screen, color, (cx - 8, cy + 8), (cx + 7, cy - 7), 3)
        d.polygon(screen, color, [(cx - 10, cy + 10), (cx - 9, cy + 4),
                                  (cx - 4, cy + 9)])

    elif name == "trash":
        d.rect(screen, color, (cx - 7, cy - 4, 14, 14), 2)
        d.line(screen, color, (cx - 10, cy - 6), (cx + 10, cy - 6), 2)
        d.rect(screen, color, (cx - 3, cy - 10, 6, 4), 2)
        d.line(screen, color, (cx - 2, cy - 1), (cx - 2, cy + 7), 1)
        d.line(screen, color, (cx + 2, cy - 1), (cx + 2, cy + 7), 1)

    elif name == "invader":
        draw_invader(screen, cx, cy - 8, 2, color)


_avatar_cache = {}


def circle_crop(image, diameter):
    iw, ih = image.get_size()
    side = min(iw, ih)
    sub = image.subsurface(pygame.Rect((iw - side) // 2, (ih - side) // 2,
                                       side, side))
    sub = pygame.transform.smoothscale(sub, (diameter, diameter))

    out = pygame.Surface((diameter, diameter), pygame.SRCALPHA)
    out.blit(sub, (0, 0))

    mask = pygame.Surface((diameter, diameter), pygame.SRCALPHA)
    pygame.draw.circle(mask, (255, 255, 255, 255),
                       (diameter // 2, diameter // 2), diameter // 2)
    out.blit(mask, (0, 0), special_flags=pygame.BLEND_RGBA_MIN)
    return out


def avatar_path(player_id):
    return os.path.join(IMG_DIR, f"profile_avatar_{player_id}.png")


def clear_avatar_cache():
    _avatar_cache.clear()


def avatar_surface(player_id, diameter):
    key = (player_id, diameter)
    if key in _avatar_cache:
        return _avatar_cache[key]

    surf = None
    path = avatar_path(player_id)

    if player_id is not None and os.path.exists(path):
        try:
            img = pygame.image.load(path).convert_alpha()
            surf = circle_crop(img, diameter)
        except Exception as e:
            print("AVATAR ERROR:", e)

    _avatar_cache[key] = surf
    return surf


_SHIP = [
    "....#....",
    "...###...",
    "...#o#...",
    ".#.###.#.",
    ".#######.",
    "####.####",
    "#.#####.#",
    "#..###..#",
    "....f....",
]


def draw_ship(screen, cx, cy, px=4, color=CYAN):
    cols, rows = len(_SHIP[0]), len(_SHIP)
    left = cx - (cols * px) // 2
    top = cy - (rows * px) // 2
    palette = {"#": color, "o": (235, 250, 255), "f": (255, 150, 60)}

    for r, line in enumerate(_SHIP):
        for c, ch in enumerate(line):
            if ch in palette:
                pygame.draw.rect(screen, palette[ch],
                                 (left + c * px, top + r * px, px, px))


def draw_avatar(screen, cx, cy, r, color=CYAN, image=None):
    if image is not None:
        screen.blit(image, image.get_rect(center=(cx, cy)))
    else:
        pygame.draw.circle(screen, (4, 22, 74), (cx, cy), r)
        pygame.draw.circle(screen, (10, 50, 130), (cx, cy), int(r * 0.78), 1)
        px = max(2, int(r * 1.4) // len(_SHIP[0]))
        draw_ship(screen, cx, cy, px, color)

    pygame.draw.circle(screen, color, (cx, cy), r, 2)


_INVADER = [
    "..#.....#..",
    "...#...#...",
    "..#######..",
    ".##.###.##.",
    "###########",
    "#.#######.#",
    "#.#.....#.#",
    "...##.##...",
]


def draw_invader(screen, cx, top, px=5, color=CYAN):
    cols = len(_INVADER[0])
    left = cx - (cols * px) // 2
    for r, line in enumerate(_INVADER):
        for c, ch in enumerate(line):
            if ch == "#":
                pygame.draw.rect(screen, color,
                                 (left + c * px, top + r * px, px, px))


_logo_cache = {}


def _chrome_text(text, size):
    f = font(size, True, italic=True)
    base = f.render(text, True, (255, 255, 255))
    w, h = base.get_size()
    pad = 22

    out = pygame.Surface((w + pad * 2, h + pad * 2), pygame.SRCALPHA)

    glow_src = f.render(text, True, (40, 160, 255))
    small = pygame.Surface((w + pad * 2, h + pad * 2), pygame.SRCALPHA)
    small.blit(glow_src, (pad, pad))
    sw, sh = max(1, small.get_width() // 5), max(1, small.get_height() // 5)
    blur = pygame.transform.smoothscale(
        pygame.transform.smoothscale(small, (sw, sh)), small.get_size())
    out.blit(blur, (0, 0))
    out.blit(blur, (0, 0))

    dark = f.render(text, True, (4, 22, 120))
    for dx in range(-3, 4):
        for dy in range(-3, 4):
            if dx * dx + dy * dy <= 10:
                out.blit(dark, (pad + dx, pad + dy))

    grad = vgradient((w, h), [(0.0, (225, 250, 255)), (0.45, (90, 200, 255)),
                              (0.55, (40, 140, 255)), (1.0, (25, 70, 225))])
    grad.blit(base, (0, 0), special_flags=pygame.BLEND_RGBA_MULT)
    out.blit(grad, (pad, pad))
    return out


def build_logo(scale=1.0):
    size = int(48 * scale)
    space = _chrome_text("SPACE", size)
    inv = _chrome_text("INVADERS", size)

    width = max(space.get_width(), inv.get_width()) + int(150 * scale)
    px = max(3, int(5 * scale))
    inv_h = 8 * px
    ring_h = int(size * 1.7)

    height = inv_h + 8 + space.get_height() + inv.get_height() - 30
    logo = pygame.Surface((width, height), pygame.SRCALPHA)

    inv_top = 0
    draw_invader(logo, width // 2, inv_top, px, CYAN)

    sy = inv_h - 6
    logo_space = space.get_rect(midtop=(width // 2, sy))
    logo_inv = inv.get_rect(midtop=(width // 2,
                                    sy + space.get_height() - 36))

    rw = space.get_width() + int(120 * scale)
    rh = max(22, int(size * 0.62))
    ring = pygame.Surface((rw + 40, rw + 40), pygame.SRCALPHA)
    rc = ring.get_width() // 2
    ring_rect = pygame.Rect(rc - rw // 2, rc - rh // 2, rw, rh)

    back = ring.copy()
    front = ring.copy()

    for i, (col, wd) in enumerate((((30, 120, 255, 90), 9),
                                   ((60, 190, 255, 255), 4),
                                   ((215, 250, 255, 255), 2))):
        pygame.draw.ellipse(back, col, ring_rect, wd)
        pygame.draw.arc(front, col, ring_rect, math.pi, math.tau, wd)

    back = pygame.transform.rotate(back, 7)
    front = pygame.transform.rotate(front, 7)
    ring_center = (logo_space.centerx, logo_space.centery + 2)

    logo.blit(back, back.get_rect(center=ring_center))
    logo.blit(space, logo_space)
    logo.blit(front, front.get_rect(center=ring_center))
    logo.blit(inv, logo_inv)

    return logo


def draw_logo(screen, cx, top, scale=1.0):
    key = round(scale, 2)
    if key not in _logo_cache:
        _logo_cache[key] = build_logo(scale)

    logo = _logo_cache[key]
    screen.blit(logo, logo.get_rect(midtop=(cx, top)))
    return top + logo.get_height()