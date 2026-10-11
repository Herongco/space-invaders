import pygame

from managers import ui


class Home:

    SHOW_LOGO = False

    MENU = [
        ("play", "START GAME", "play", True),
        ("leaderboard", "LEADERBOARD", "crown", True),
        ("settings", "SETTINGS", "gear", True),
        ("profile", "PLAYER PROFILE", "user", True),
        ("logout", "LOGOUT", "logout", True),
    ]

    def __init__(self, screen, w, h, player=None):
        self.screen = screen
        self.w = w
        self.h = h
        self.player = player
        self.action = None
        self.confirm_logout = False

        bw = 280
        bh = 52
        gap = 16

        pw = bw + 50
        ph = len(self.MENU) * bh + (len(self.MENU) - 1) * gap + 52

        self.panel = pygame.Rect(w - pw - 24, (h - ph) // 2, pw, ph)

        bx = self.panel.x + 25
        y = self.panel.y + 26

        self.rects = {}

        for action, text, icon, primary in self.MENU:
            self.rects[action] = pygame.Rect(bx, y, bw, bh)
            y += bh + gap


    def draw(self):
        ui.draw_background(self.screen, self.w, self.h, dim=0,
                           image="romenu.png", live=True)

        if self.SHOW_LOGO:
            ui.draw_logo(self.screen, self.panel.x // 2,
                         self.h // 2 - 80, 0.9)


        for action, text, icon, primary in self.MENU:
            ui.draw_button(
                self.screen,
                self.rects[action],
                text,
                primary,
                icon
            )

        if self.confirm_logout:
            ui.draw_dialog(
                self.screen,
                self.w,
                self.h,
                "power",
                [
                    "Are you sure you want",
                    "to log out?"
                ],
                "YES",
                "CANCEL",
                title="LOGOUT"
            )


    def handle_events(self, events):
        self.action = None

        for event in events:

            if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                self.click(event.pos)

            elif event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE:
                    self.confirm_logout = False


    def click(self, pos):

        if self.confirm_logout:
            _, yes, no = ui.dialog_rects(
                self.w,
                self.h
            )

            if yes.collidepoint(pos):
                self.confirm_logout = False
                self.action = "logout"

            elif no.collidepoint(pos):
                self.confirm_logout = False

            return

        for action, rect in self.rects.items():

            if rect.collidepoint(pos):

                if action == "logout":
                    self.confirm_logout = True

                else:
                    self.action = action

                return