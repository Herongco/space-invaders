import re
import threading

import pygame

import managers.ui as ui
from settings_manager import load_settings, save_settings
from email_service import send_code
from db import (
    login_player,
    register_player,
    account_exists,
    email_registered,
    create_email_code,
    verify_email_code,
    reset_password,
)

EMAIL_RE = re.compile(r"^[^@\s]+@[^@\s]+\.[^@\s]+$")

MIN_PASSWORD = 6
RESEND_SECONDS = 30

PAGES = {
    "login": {
        "title": None,
        "fields": [
            ("username", "Username or Email", "user", False, 50),
            ("password", "Password", "lock", True, 40),
        ],
    },
    "register": {
        "title": "CREATE YOUR ACCOUNT",
        "fields": [
            ("username", "Username", "user", False, 30),
            ("email", "Email", "mail", False, 60),
            ("password", "Password", "lock", True, 40),
            ("confirm", "Confirm Password", "lock", True, 40),
        ],
    },
    "verify": {
        "title": "VERIFY YOUR EMAIL",
        "fields": [
            ("code", "6-digit code", "key", False, 6),
        ],
    },
    "forgot": {
        "title": "FORGOT PASSWORD",
        "fields": [
            ("email", "Your account email", "mail", False, 60),
        ],
    },
    "reset": {
        "title": "RESET PASSWORD",
        "fields": [
            ("code", "6-digit code", "key", False, 6),
            ("password", "New Password", "lock", True, 40),
            ("confirm", "Confirm New Password", "lock", True, 40),
        ],
    },
}

BUTTONS = {
    "login": [
        ("login", "LOGIN", True),
        ("register", "CREATE ACCOUNT", False),
    ],
    "register": [
        ("create", "CREATE ACCOUNT", True),
        ("back", "BACK TO LOGIN", False),
    ],
    "verify": [
        ("verify", "VERIFY & CREATE ACCOUNT", True),
        ("resend", "RESEND CODE", False),
        ("back", "BACK", False),
    ],
    "forgot": [
        ("send_reset", "SEND CODE", True),
        ("back", "BACK TO LOGIN", False),
    ],
    "reset": [
        ("reset", "RESET PASSWORD", True),
        ("resend", "RESEND CODE", False),
        ("back", "BACK TO LOGIN", False),
    ],
}


class LoginManager:

    def __init__(self, screen, w, h):
        self.screen = screen
        self.w = w
        self.h = h

        self.page = "login"
        self.values = {}
        self.active = 0
        self.show_password = False
        self.remember_me = True

        self.logged_in_player = None

        self.message = ""
        self.message_color = ui.RED

        self.job = None
        self.pending_email = ""
        self.pending_data = {}
        self.resend_at = 0

        self.reset_to_login()


    def reset_to_login(self):
        self.logged_in_player = None
        self.job = None
        self.go("login")

    def logout(self):
        self.reset_to_login()

    def go(self, page, keep=False):
        self.page = page
        if not keep:
            self.values = {}
        self.active = 0
        self.show_password = False
        self.message = ""

    def set_message(self, text, color):
        self.message = text
        self.message_color = color


    def run_job(self, work, done, busy_text="PLEASE WAIT..."):
        if self.job:
            return

        job = {"done": False, "result": None, "error": False, "cb": done}
        self.job = job
        self.set_message(busy_text, ui.CYAN)

        def worker():
            try:
                job["result"] = work()
            except Exception as e:
                print("JOB ERROR:", e)
                job["error"] = True
            job["done"] = True

        threading.Thread(target=worker, daemon=True).start()

    def poll(self):
        job = self.job

        if job and job["done"]:
            self.job = None

            if job["error"]:
                self.set_message("DATABASE CONNECTION ERROR", ui.RED)
            else:
                job["cb"](job["result"])


    def layout(self):
        cfg = PAGES[self.page]
        buttons = BUTTONS[self.page]

        pw = 440
        px = (self.w - pw) // 2
        ix = px + 30
        iw = pw - 60

        field_h, field_gap = 42, 10
        btn_h, btn_gap = 40, 8

        top_pad = 62 if cfg["title"] else 26
        hint_h = 26 if self.page in ("verify", "reset", "forgot") else 0
        extras_h = 34 if self.page == "login" else 0

        total = (
            top_pad + hint_h
            + len(cfg["fields"]) * (field_h + field_gap)
            + extras_h + 26
            + len(buttons) * (btn_h + btn_gap) + 12
        )

        if self.page == "login":
            py = 198 + (self.h - 600) // 2
        else:
            py = max(16, (self.h - total) // 2)

        panel = pygame.Rect(px, py, pw, total)

        y = py + top_pad + hint_h
        fields = []

        for key, placeholder, icon, secret, max_len in cfg["fields"]:
            fields.append({
                "key": key,
                "placeholder": placeholder,
                "icon": icon,
                "secret": secret,
                "max": max_len,
                "rect": pygame.Rect(ix, y, iw, field_h),
            })
            y += field_h + field_gap

        remember_rect = forgot_rect = None

        if self.page == "login":
            remember_rect = pygame.Rect(ix, y + 2, 22, 22)
            forgot_rect = pygame.Rect(ix + iw - 190, y, 190, 26)
            y += extras_h

        msg_y = y + 12
        y += 26

        btn_rects = []
        for action, text, primary in buttons:
            btn_rects.append((action, text, primary,
                              pygame.Rect(ix, y, iw, btn_h)))
            y += btn_h + btn_gap

        return {
            "panel": panel,
            "fields": fields,
            "remember": remember_rect,
            "forgot": forgot_rect,
            "msg_y": msg_y,
            "buttons": btn_rects,
        }


    def draw(self):
        self.poll()

        ui.draw_background(self.screen, self.w, self.h, dim=0,
                           image="roback.png", live=True)

        lay = self.layout()
        panel = lay["panel"]

        if self.page == "login":
            ui.draw_logo(self.screen, self.w // 2, 6 + (self.h - 600) // 2, 1.0)

        ui.draw_panel(self.screen, panel, PAGES[self.page]["title"])

        if self.page in ("verify", "reset"):
            hint = "Code sent to " + self.pending_email
            hint = ui.fit_text(hint, ui.font(13), panel.w - 40)
            ui.draw_text(self.screen, hint, 13, ui.GRAY,
                         (panel.centerx, panel.y + 56), "midtop")
        elif self.page == "forgot":
            ui.draw_text(self.screen, "We will email you a reset code",
                         13, ui.GRAY, (panel.centerx, panel.y + 56), "midtop")

        for i, f in enumerate(lay["fields"]):
            if f["key"] == "code":
                ui.draw_code_input(
                    self.screen, f["rect"],
                    self.values.get("code", ""),
                    i == self.active
                )
            else:
                ui.draw_input(
                    self.screen, f["rect"],
                    self.values.get(f["key"], ""),
                    f["placeholder"], f["icon"],
                    i == self.active,
                    f["secret"], self.show_password
                )

        if lay["remember"]:
            ui.draw_checkbox(self.screen, lay["remember"], self.remember_me)
            ui.draw_text(self.screen, "Remember me", 14, ui.GRAY,
                         (lay["remember"].right + 10,
                          lay["remember"].centery), "midleft")

            ui.draw_text(self.screen, "Forgot password?", 14, ui.CYAN,
                         (lay["forgot"].right, lay["forgot"].centery),
                         "midright", True)

            ui.add_click_area(lay["forgot"])
            ui.add_click_area(lay["remember"].inflate(130, 8))

        ui.draw_message(self.screen, self.message, self.message_color,
                        panel.centerx, lay["msg_y"])

        busy = self.job is not None
        for action, text, primary, rect in lay["buttons"]:
            ui.draw_button(self.screen, rect, text, primary,
                           enabled=not busy)


    def handle_events(self, events):
        for event in events:
            if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                self.click(event.pos)

            elif event.type == pygame.KEYDOWN:
                self.key(event)

    def click(self, pos):
        if self.job:
            return

        lay = self.layout()

        for i, f in enumerate(lay["fields"]):
            if f["rect"].collidepoint(pos):
                ui.play_click()
                self.active = i

                if f["secret"] and ui.eye_rect(f["rect"]).collidepoint(pos):
                    self.show_password = not self.show_password
                return

        if lay["remember"] and lay["remember"].inflate(130, 8).collidepoint(pos):
            self.remember_me = not self.remember_me
            return

        if lay["forgot"] and lay["forgot"].collidepoint(pos):
            self.go("forgot")
            return

        for action, text, primary, rect in lay["buttons"]:
            if rect.collidepoint(pos):
                self.do(action)
                return

    def key(self, event):
        if self.job:
            return

        fields = PAGES[self.page]["fields"]

        if event.key == pygame.K_TAB:
            step = -1 if pygame.key.get_mods() & pygame.KMOD_SHIFT else 1
            self.active = (self.active + step) % len(fields)
            return

        if event.key in (pygame.K_RETURN, pygame.K_KP_ENTER):
            if self.active < len(fields) - 1:
                self.active += 1
            else:
                self.do(BUTTONS[self.page][0][0])
            return

        name, _, _, _, max_len = fields[self.active]

        self.values[name] = ui.apply_key(
            self.values.get(name, ""),
            event,
            max_len,
            digits_only=(name == "code"),
            allow_space=False
        )

    def do(self, action):
        if action == "login":
            self.login()

        elif action == "register":
            self.go("register")

        elif action == "create":
            self.start_register()

        elif action == "verify":
            self.verify_registration()

        elif action == "resend":
            self.resend()

        elif action == "send_reset":
            self.start_forgot()

        elif action == "reset":
            self.do_reset()

        elif action == "back":
            if self.page == "verify":
                self.go("register", keep=True)
                self.values = dict(self.pending_data)
            else:
                self.go("login")


    def login(self):
        username = self.values.get("username", "").strip()
        password = self.values.get("password", "")

        if not username:
            self.set_message("PLEASE ENTER YOUR USERNAME OR EMAIL", ui.RED)
            return

        if not password:
            self.set_message("PLEASE ENTER YOUR PASSWORD", ui.RED)
            return

        def work():
            return login_player(username, password)

        def done(player):
            if not player:
                self.set_message("INVALID USERNAME/EMAIL OR PASSWORD", ui.RED)
                return

            settings = load_settings()
            settings["remembered_user"] = (
                player["username"] if self.remember_me else ""
            )
            save_settings(settings)

            self.logged_in_player = player
            self.set_message("LOGIN SUCCESSFUL!", ui.GREEN)

        self.run_job(work, done, "LOGGING IN...")


    def start_register(self):
        username = self.values.get("username", "").strip()
        email = self.values.get("email", "").strip().lower()
        password = self.values.get("password", "")
        confirm = self.values.get("confirm", "")

        if not username or not email or not password or not confirm:
            self.set_message("PLEASE COMPLETE ALL FIELDS", ui.RED)
            return

        if len(username) < 3:
            self.set_message("USERNAME MUST BE AT LEAST 3 CHARACTERS", ui.RED)
            return

        if not EMAIL_RE.match(email):
            self.set_message("PLEASE ENTER A VALID EMAIL", ui.RED)
            return

        if len(password) < MIN_PASSWORD:
            self.set_message(
                f"PASSWORD MUST BE AT LEAST {MIN_PASSWORD} CHARACTERS", ui.RED
            )
            return

        if password != confirm:
            self.set_message("PASSWORDS DO NOT MATCH", ui.RED)
            return

        def work():
            exists, msg = account_exists(username, email)
            if exists:
                return False, msg

            code = create_email_code(email, "register")
            if not code:
                return False, "DATABASE ERROR"

            return send_code(email, code, "register")

        def done(result):
            ok, msg = result

            if not ok:
                self.set_message(msg, ui.RED)
                return

            self.pending_email = email
            self.pending_data = {
                "username": username,
                "email": email,
                "password": password,
                "confirm": confirm,
            }
            self.resend_at = pygame.time.get_ticks() + RESEND_SECONDS * 1000

            self.go("verify")
            self.set_message(msg, ui.GREEN)

        self.run_job(work, done, "SENDING CODE...")

    def verify_registration(self):
        code = self.values.get("code", "").strip()

        if len(code) != 6:
            self.set_message("ENTER THE 6-DIGIT CODE", ui.RED)
            return

        data = dict(self.pending_data)

        def work():
            ok, msg = verify_email_code(data["email"], "register", code)
            if not ok:
                return False, msg

            return register_player(
                data["username"], data["email"], data["password"]
            )

        def done(result):
            ok, msg = result

            if not ok:
                self.set_message(msg, ui.RED)
                return

            self.go("login")
            self.values["username"] = data["username"]
            self.active = 1
            self.set_message("ACCOUNT CREATED! PLEASE LOGIN.", ui.GREEN)

        self.run_job(work, done, "VERIFYING...")


    def start_forgot(self):
        email = self.values.get("email", "").strip().lower()

        if not EMAIL_RE.match(email):
            self.set_message("PLEASE ENTER A VALID EMAIL", ui.RED)
            return

        def work():
            if not email_registered(email):
                return False, "NO ACCOUNT WITH THAT EMAIL"

            code = create_email_code(email, "reset")
            if not code:
                return False, "DATABASE ERROR"

            return send_code(email, code, "reset")

        def done(result):
            ok, msg = result

            if not ok:
                self.set_message(msg, ui.RED)
                return

            self.pending_email = email
            self.resend_at = pygame.time.get_ticks() + RESEND_SECONDS * 1000

            self.go("reset")
            self.set_message(msg, ui.GREEN)

        self.run_job(work, done, "SENDING CODE...")

    def do_reset(self):
        code = self.values.get("code", "").strip()
        password = self.values.get("password", "")
        confirm = self.values.get("confirm", "")
        email = self.pending_email

        if len(code) != 6:
            self.set_message("ENTER THE 6-DIGIT CODE", ui.RED)
            return

        if len(password) < MIN_PASSWORD:
            self.set_message(
                f"PASSWORD MUST BE AT LEAST {MIN_PASSWORD} CHARACTERS", ui.RED
            )
            return

        if password != confirm:
            self.set_message("PASSWORDS DO NOT MATCH", ui.RED)
            return

        def work():
            ok, msg = verify_email_code(email, "reset", code)
            if not ok:
                return False, msg

            return reset_password(email, password)

        def done(result):
            ok, msg = result

            if not ok:
                self.set_message(msg, ui.RED)
                return

            self.go("login")
            self.set_message("PASSWORD RESET! PLEASE LOGIN.", ui.GREEN)

        self.run_job(work, done, "RESETTING...")


    def resend(self):
        now = pygame.time.get_ticks()

        if now < self.resend_at:
            wait = (self.resend_at - now + 999) // 1000
            self.set_message(f"PLEASE WAIT {wait}s BEFORE RESENDING", ui.RED)
            return

        purpose = "register" if self.page == "verify" else "reset"
        email = self.pending_email

        def work():
            code = create_email_code(email, purpose)
            if not code:
                return False, "DATABASE ERROR"

            return send_code(email, code, purpose)

        def done(result):
            ok, msg = result

            if ok:
                self.resend_at = (
                    pygame.time.get_ticks() + RESEND_SECONDS * 1000
                )

            self.set_message(msg, ui.GREEN if ok else ui.RED)

        self.run_job(work, done, "SENDING CODE...")