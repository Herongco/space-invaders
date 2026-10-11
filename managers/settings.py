import pygame

from managers import ui
from settings_manager import (
    load_settings,
    save_settings,
    DEFAULT_SETTINGS,
)


def apply_audio(settings):
    try:
        if pygame.mixer.get_init():
            volume = settings.get("sound_volume", 80) / 100
            if not settings.get("music_enabled", True):
                volume = 0
            pygame.mixer.music.set_volume(volume)
    except pygame.error:
        pass


class Settings:

    ROW_H = 56

    def __init__(self, screen, w, h, player=None):
        self.screen = screen
        self.w = w
        self.h = h
        self.player = player
        self.action = None

        self.settings = load_settings()
        self.dragging = False

        self.panel = pygame.Rect(w // 2 - 280, 120, 560, 4 * (self.ROW_H + 8) + 28)

        self.rows = []
        rows = [
            ("music_enabled", "Music", "music"),
            ("sound_enabled", "Sound Effects", "speaker"),
            ("mobile_controls", "Mobile Controls", "phone"),
            ("sound_volume", "Volume", "speaker"),
        ]

        y = self.panel.y + 18
        for key, label, icon in rows:
            self.rows.append({
                "key": key,
                "label": label,
                "icon": icon,
                "rect": pygame.Rect(self.panel.x + 18, y,
                                    self.panel.w - 36, self.ROW_H),
            })
            y += self.ROW_H + 8

        self.reset_btn = pygame.Rect(self.panel.centerx - 130,
                                     self.panel.bottom + 16, 260, 42)
        self.back_btn = pygame.Rect(30, h - 70, 130, 42)


    def row(self, key):
        for r in self.rows:
            if r["key"] == key:
                return r["rect"]

    def toggle_rect(self, row_rect):
        return pygame.Rect(row_rect.right - 84, row_rect.centery - 13, 68, 26)

    def track_rect(self, row_rect):
        return pygame.Rect(row_rect.right - 290, row_rect.centery - 4, 200, 8)

    def save(self):
        save_settings(self.settings)
        apply_audio(self.settings)

    def set_volume_from_x(self, x):
        track = self.track_rect(self.row("sound_volume"))
        ratio = (x - track.x) / track.w
        self.settings["sound_volume"] = int(round(max(0, min(1, ratio)) * 100))
        apply_audio(self.settings)


    def draw(self):
        ui.draw_background(self.screen, self.w, self.h, dim=0)
        ui.draw_header(self.screen, self.w, "SETTINGS", icon="gear")
        ui.draw_panel(self.screen, self.panel)

        mouse = pygame.mouse.get_pos()

        for r in self.rows:
            rect, key = r["rect"], r["key"]

            hover = rect.collidepoint(mouse)

            if key != "sound_volume":
                ui.add_click_area(rect)

            pygame.draw.rect(self.screen, (9, 42, 100) if hover else (5, 24, 68),
                             rect, border_radius=8)
            pygame.draw.rect(self.screen, ui.CYAN if hover else (40, 125, 225),
                             rect, 1, border_radius=8)

            ui.draw_icon(self.screen, r["icon"], rect.x + 28, rect.centery,
                         ui.CYAN)
            ui.draw_text(self.screen, r["label"], 17, ui.WHITE,
                         (rect.x + 56, rect.centery), "midleft", True)

            if key in ("music_enabled", "sound_enabled", "mobile_controls"):
                ui.draw_toggle(self.screen, self.toggle_rect(rect),
                               self.settings[key])

            elif key == "sound_volume":
                self.draw_slider(rect)

        ui.draw_button(self.screen, self.reset_btn, "RESET TO DEFAULT")
        ui.draw_button(self.screen, self.back_btn, "BACK", icon="back")

    def draw_slider(self, row_rect):
        track = self.track_rect(row_rect)
        value = self.settings["sound_volume"]

        pygame.draw.rect(self.screen, (14, 30, 72), track, border_radius=4)

        fill = pygame.Rect(track.x, track.y, int(track.w * value / 100),
                           track.h)
        if fill.w > 0:
            pygame.draw.rect(self.screen, ui.NEON, fill, border_radius=4)

        pygame.draw.circle(self.screen, (20, 90, 190),
                           (track.x + fill.w, track.centery), 12)
        pygame.draw.circle(self.screen, ui.WHITE,
                           (track.x + fill.w, track.centery), 9)
        pygame.draw.circle(self.screen, ui.CYAN,
                           (track.x + fill.w, track.centery), 9, 2)

        ui.draw_text(self.screen, f"{value}%", 15, ui.WHITE,
                     (row_rect.right - 14, row_rect.centery), "midright",
                     True)


    def handle_events(self, events):
        self.action = None

        for event in events:
            if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                self.click(event.pos)

            elif event.type == pygame.MOUSEMOTION and self.dragging:
                self.set_volume_from_x(event.pos[0])

            elif event.type == pygame.MOUSEBUTTONUP and event.button == 1:
                if self.dragging:
                    self.dragging = False
                    self.save()

            elif event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE:
                    self.action = "back"

    def click(self, pos):
        if self.back_btn.collidepoint(pos):
            self.action = "back"
            return

        if self.reset_btn.collidepoint(pos):
            remembered = self.settings.get("remembered_user", "")
            self.settings = dict(DEFAULT_SETTINGS)
            self.settings["remembered_user"] = remembered
            self.save()
            return

        for r in self.rows:
            rect, key = r["rect"], r["key"]

            if not rect.collidepoint(pos):
                continue

            if key in ("music_enabled", "sound_enabled", "mobile_controls"):
                self.settings[key] = not self.settings[key]
                self.save()

            elif key == "sound_volume":
                track = self.track_rect(rect)
                if track.inflate(24, 30).collidepoint(pos):
                    self.dragging = True
                    self.set_volume_from_x(pos[0])
            return