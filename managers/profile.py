import os
import re
import tkinter as tk
from tkinter import filedialog

import pygame

from managers import ui
from db import (
    update_player_profile,
    delete_player,
    get_player_highest_score,
    get_player_highest_level,
    get_last_error,
)


EMAIL_RE = re.compile(r"^[^@\s]+@[^@\s]+\.[^@\s]+$")


class Profile:

    def __init__(self, screen, w, h, player):

        self.screen = screen
        self.w = w
        self.h = h
        self.player = player

        self.action = None
        self.editing = False
        self.confirm_delete = False
        self.delete_success_time = 0

        self.message = ""
        self.active = "username"

        self.white = ui.WHITE
        self.cyan = ui.CYAN
        self.gold = ui.GOLD
        self.green = ui.GREEN
        self.red = ui.RED


        self.player_id = self.get_player_id()
        self.username = self.get_username()
        self.email = self.get_email()

        self.edit_username = ""
        self.edit_email = ""

        try:
            self.highest_score = get_player_highest_score(self.player_id)
        except Exception as e:
            print("HIGH SCORE ERROR:", e)
            self.highest_score = 0

        try:
            self.highest_level = get_player_highest_level(self.player_id)
        except Exception as e:
            print("HIGH LEVEL ERROR:", e)
            self.highest_level = 1


        os.makedirs(ui.IMG_DIR, exist_ok=True)

        self.avatar_path = ui.avatar_path(self.player_id)
        self.avatar_image = None
        self.load_avatar()


        self.panel = pygame.Rect(w // 2 - 250, 130, 500, 400)
        px, py = self.panel.x, self.panel.y

        self.username_box = pygame.Rect(px + 40, py + 80, 420, 46)
        self.email_box = pygame.Rect(px + 40, py + 170, 420, 46)
        self.save_btn = pygame.Rect(px + 40, py + 250, 200, 44)
        self.cancel_btn = pygame.Rect(px + 260, py + 250, 200, 44)

        bw, bh, gap = 200, 42, 20
        top_x = self.panel.centerx - (bw * 2 + gap) // 2
        by = self.panel.bottom - 118

        self.edit_btn = pygame.Rect(top_x, by, bw, bh)
        self.photo_btn = pygame.Rect(top_x + bw + gap, by, bw, bh)
        self.delete_btn = pygame.Rect(self.panel.centerx - 100,
                                      by + bh + 14, 200, 38)

        self.confirm_yes_btn = pygame.Rect(px + 60, py + 270, 180, 44)
        self.confirm_no_btn = pygame.Rect(px + 260, py + 270, 180, 44)

        self.back_btn = pygame.Rect(30, h - 66, 130, 42)


    def get_player_id(self):
        try:
            if isinstance(self.player, dict):
                for key in ("player_id", "id"):
                    if self.player.get(key) is not None:
                        return self.player.get(key)
                return None

            if hasattr(self.player, "id"):
                return self.player.id

            return self.player[0]

        except Exception:
            return None

    def get_username(self):
        try:
            if isinstance(self.player, dict):
                return (self.player.get("username")
                        or self.player.get("name")
                        or "Player")

            if hasattr(self.player, "username"):
                return self.player.username

            return self.player[1]

        except Exception:
            return "Player"

    def get_email(self):
        try:
            if isinstance(self.player, dict):
                return self.player.get("email", "") or ""

            if hasattr(self.player, "email"):
                return self.player.email

            return self.player[2]

        except Exception:
            return ""


    def load_avatar(self):
        self.avatar_image = None
        self.avatar_circle = None

        if not os.path.exists(self.avatar_path):
            return

        try:
            self.avatar_image = pygame.image.load(
                self.avatar_path).convert_alpha()
            self.avatar_circle = ui.circle_crop(self.avatar_image, 110)
        except Exception as e:
            print("AVATAR LOAD ERROR:", e)
            self.avatar_image = None
            self.avatar_circle = None

    def choose_photo(self):
        root = None

        try:
            root = tk.Tk()
            root.withdraw()
            root.attributes("-topmost", True)

            file_path = filedialog.askopenfilename(
                parent=root,
                title="Choose Profile Photo",
                filetypes=[
                    ("Image Files", "*.png *.jpg *.jpeg *.webp"),
                    ("PNG Files", "*.png"),
                    ("JPG Files", "*.jpg *.jpeg"),
                    ("WEBP Files", "*.webp"),
                    ("All Files", "*.*"),
                ],
            )

            if file_path:
                try:
                    image = pygame.image.load(file_path).convert_alpha()
                    pygame.image.save(image, self.avatar_path)

                    self.load_avatar()
                    ui.clear_avatar_cache()

                    self.message = "PROFILE PICTURE UPDATED"

                except Exception as e:
                    print("PROFILE PHOTO ERROR:", e)
                    self.message = "FAILED TO UPDATE PHOTO"

        except Exception as e:
            print("FILE PICKER ERROR:", e)
            self.message = "FAILED TO OPEN PHOTO PICKER"

        finally:
            if root:
                try:
                    root.destroy()
                except Exception:
                    pass

    def draw_profile_picture(self, cx, cy, radius):
        photo = self.avatar_circle

        pygame.draw.circle(self.screen, (20, 90, 200), (cx, cy), radius + 7, 2)
        pygame.draw.circle(self.screen, (10, 50, 130), (cx, cy), radius + 4, 2)

        ui.draw_avatar(self.screen, cx, cy, radius, self.cyan, photo)


    def field(self, x, y, label, value, size, color):
        ui.draw_text(self.screen, label, 12, self.cyan, (x, y), "topleft",
                     True)
        ui.draw_text(self.screen, value, size, color, (x, y + 18),
                     "topleft", True)

    def draw_input_box(self, rect, label, text, active):
        ui.add_click_area(rect)
        ui.draw_text(self.screen, label, 12, self.cyan,
                     (rect.x, rect.y - 20), "topleft", True)

        pygame.draw.rect(self.screen, ui.INPUT, rect, border_radius=8)
        pygame.draw.rect(self.screen, self.cyan if active else (40, 125, 225),
                         rect, 2, border_radius=8)

        shown = ui.fit_text(text, ui.font(17), rect.w - 24)
        surf = ui.font(17).render(shown, True, self.white)
        self.screen.blit(surf, (rect.x + 12,
                                rect.centery - surf.get_height() // 2))

        if active and (pygame.time.get_ticks() // 500) % 2 == 0:
            cx = rect.x + 12 + surf.get_width() + 2
            pygame.draw.line(self.screen, self.cyan,
                             (cx, rect.centery - 10), (cx, rect.centery + 10), 2)


    def draw_view(self):
        p = self.panel

        self.draw_profile_picture(p.x + 95, p.y + 105, 55)

        tx = p.x + 180
        maxw = p.w - 180 - 24

        name = ui.fit_text(self.username, ui.font(24, True), maxw)
        ui.draw_text(self.screen, name, 24, self.white, (tx, p.y + 40),
                     "topleft", True)

        email = ui.fit_text(self.email or "-", ui.font(14), maxw)
        self.field(tx, p.y + 88, "EMAIL", email, 14, self.white)

        self.field(tx, p.y + 142, "HIGHEST SCORE", str(self.highest_score),
                   26, self.gold)
        self.field(tx, p.y + 202, "LEVEL", str(self.highest_level), 22,
                   self.white)

        if self.message:
            ok = "UPDATED" in self.message or "SUCCESS" in self.message
            ui.draw_message(self.screen, self.message,
                            self.green if ok else self.red,
                            p.centerx, p.bottom - 152)

        ui.draw_button(self.screen, self.edit_btn, "EDIT PROFILE",
                       primary=True, icon="edit")
        ui.draw_button(self.screen, self.photo_btn, "CHANGE PHOTO",
                       primary=True, icon="camera")
        ui.draw_button(self.screen, self.delete_btn, "DELETE ACCOUNT",
                       icon="trash")


    def draw_edit(self):
        self.draw_input_box(self.username_box, "USERNAME",
                            self.edit_username, self.active == "username")
        self.draw_input_box(self.email_box, "EMAIL",
                            self.edit_email, self.active == "email")

        if self.message:
            ui.draw_message(self.screen, self.message, self.red,
                            self.panel.centerx, self.panel.y + 232)

        ui.draw_button(self.screen, self.save_btn, "SAVE", primary=True,
                       icon="check")
        ui.draw_button(self.screen, self.cancel_btn, "CANCEL", icon="back")


    def draw_delete_confirmation(self):
        p = self.panel

        pygame.draw.circle(self.screen, (4, 20, 70), (p.centerx, p.y + 70), 30)
        pygame.draw.circle(self.screen, self.red, (p.centerx, p.y + 70), 30, 2)
        ui.draw_icon(self.screen, "warn", p.centerx, p.y + 70, self.red)

        ui.draw_text(self.screen, "DELETE ACCOUNT?", 24, self.red,
                     (p.centerx, p.y + 120), "midtop", True)
        ui.draw_text(self.screen, "This action cannot be undone.", 15,
                     self.white, (p.centerx, p.y + 164), "midtop")

        if self.message:
            ui.draw_message(self.screen, self.message, self.red,
                            p.centerx, p.y + 236)

        ui.draw_button(self.screen, self.confirm_yes_btn, "DELETE",
                       primary=True, icon="trash")
        ui.draw_button(self.screen, self.confirm_no_btn, "CANCEL",
                       icon="back")


    def draw(self):
        ui.draw_background(self.screen, self.w, self.h, dim=0)

        if self.action == "delete_success":
            ui.draw_glow_text(self.screen, "ACCOUNT DELETED", 36, ui.WHITE,
                              (self.w // 2, 230))
            ui.draw_text(self.screen, self.message, 18, self.green,
                         (self.w // 2, 300), "midtop", True)
            return

        ui.draw_header(self.screen, self.w, "PLAYER PROFILE")
        ui.draw_panel(self.screen, self.panel)

        if self.confirm_delete:
            self.draw_delete_confirmation()
        elif self.editing:
            self.draw_edit()
        else:
            self.draw_view()

        ui.draw_button(self.screen, self.back_btn, "BACK", icon="back")


    def save_profile(self):
        username = self.edit_username.strip()
        email = self.edit_email.strip()

        if not username:
            self.message = "USERNAME IS REQUIRED"
            return

        if email and not EMAIL_RE.match(email):
            self.message = "INVALID EMAIL"
            return

        try:
            update_player_profile(self.player_id, username, email)

            self.username = username
            self.email = email

            try:
                if isinstance(self.player, dict):
                    self.player["username"] = username
                    self.player["email"] = email
                else:
                    if hasattr(self.player, "username"):
                        self.player.username = username
                    if hasattr(self.player, "email"):
                        self.player.email = email
            except Exception:
                pass

            self.editing = False
            self.message = "PROFILE UPDATED"

        except Exception as e:
            print("UPDATE PROFILE ERROR:", e)
            self.message = "FAILED TO UPDATE PROFILE"


    def perform_delete(self):
        self.confirm_delete = False
        name = self.username

        if delete_player(self.player_id):

            try:
                if os.path.exists(self.avatar_path):
                    os.remove(self.avatar_path)
                ui.clear_avatar_cache()
            except Exception:
                pass

            self.message = f"{name} SUCCESSFULLY DELETED"
            self.delete_success_time = pygame.time.get_ticks()

            self.action = "delete_success"

        else:
            reason = get_last_error()

            self.message = (
                ("DELETE FAILED: " + reason)[:52]
                if reason else "FAILED TO DELETE ACCOUNT"
            )


    def mouse_click(self, pos):

        if self.back_btn.collidepoint(pos):
            self.action = "back"
            return

        if self.confirm_delete:
            if self.confirm_yes_btn.collidepoint(pos):
                self.perform_delete()
            elif self.confirm_no_btn.collidepoint(pos):
                self.confirm_delete = False
                self.message = ""
            return

        if self.editing:
            if self.save_btn.collidepoint(pos):
                self.save_profile()
            elif self.cancel_btn.collidepoint(pos):
                self.editing = False
                self.message = ""
            elif self.username_box.collidepoint(pos):
                ui.play_click()
                self.active = "username"
            elif self.email_box.collidepoint(pos):
                ui.play_click()
                self.active = "email"
            return

        if self.edit_btn.collidepoint(pos):
            self.editing = True
            self.active = "username"
            self.edit_username = self.username
            self.edit_email = self.email
            self.message = ""
            return

        if self.photo_btn.collidepoint(pos):
            self.choose_photo()
            return

        if self.delete_btn.collidepoint(pos):
            self.confirm_delete = True
            self.message = ""
            return


    def handle_event(self, event):

        if event.type != pygame.KEYDOWN:
            return

        if not self.editing:
            return

        if event.key == pygame.K_RETURN:
            self.save_profile()
            return

        if event.key == pygame.K_ESCAPE:
            self.editing = False
            self.message = ""
            return

        if event.key == pygame.K_TAB:
            self.active = "email" if self.active == "username" else "username"
            return

        if event.key == pygame.K_BACKSPACE:
            if self.active == "username":
                self.edit_username = self.edit_username[:-1]
            else:
                self.edit_email = self.edit_email[:-1]
            return

        if event.unicode and event.unicode.isprintable():
            if self.active == "username":
                if len(self.edit_username) < 25:
                    self.edit_username += event.unicode
            else:
                if len(self.edit_email) < 60:
                    self.edit_email += event.unicode


    def handle_events(self, events):

        if self.action == "delete_success":
            if pygame.time.get_ticks() - self.delete_success_time >= 2000:
                self.action = "deleted"
            return

        for event in events:

            if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                self.mouse_click(event.pos)

            self.handle_event(event)

    def get_action(self):
        action = self.action
        self.action = None
        return action