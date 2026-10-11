import pygame

from managers import ui
from db import load_leaderboard


class Leader:

    TABLE_X = 120
    TABLE_W = 760
    TABLE_Y = 90

    COL_RANK = 150
    COL_AVATAR = 200
    COL_NAME = 228
    COL_SCORE = 420
    COL_LEVEL = 530
    COL_DATE = 620

    ROW_H = 36

    def __init__(self, screen, w, h, player=None):
        self.screen = screen
        self.w = w
        self.h = h
        self.player = player
        self.action = None

        self.my_id = None

        if isinstance(player, dict):
            self.my_id = player.get("player_id")

        self.back_btn = pygame.Rect(
            30,
            h - 66,
            130,
            42
        )

        self.rows = []

        self.load_data()


    def load_data(self):
        try:
            self.rows = load_leaderboard()

        except Exception as e:
            print("LEADERBOARD ERROR:", e)
            self.rows = []


    def draw(self):

        ui.draw_background(
            self.screen,
            self.w,
            self.h,
            dim=0
        )

        ui.draw_header(
            self.screen,
            self.w,
            "LEADERBOARD",
            icon="crown"
        )

        table = pygame.Rect(
            self.TABLE_X,
            self.TABLE_Y,
            self.TABLE_W,
            self.ROW_H * 10 + 66
        )

        ui.draw_panel(
            self.screen,
            table,
            alpha=215
        )


        head_y = table.y + 16

        for text, x, anchor in (
            ("RANK", self.COL_RANK, "midtop"),
            ("USERNAME", self.COL_NAME, "topleft"),
            ("SCORE", self.COL_SCORE, "topleft"),
            ("LEVEL", self.COL_LEVEL, "topleft"),
            ("DATE / TIME", self.COL_DATE, "topleft")
        ):
            ui.draw_text(
                self.screen,
                text,
                13,
                ui.CYAN,
                (x, head_y),
                anchor,
                True
            )

        pygame.draw.line(
            self.screen,
            ui.NEON,
            (table.x + 20, head_y + 26),
            (table.right - 20, head_y + 26),
            1
        )


        if not self.rows:

            ui.draw_text(
                self.screen,
                "NO SCORES YET - BE THE FIRST PILOT!",
                18,
                ui.GRAY,
                table.center,
                "center",
                True
            )

        else:

            self.draw_rows(
                table,
                head_y + 34
            )


        ui.draw_button(
            self.screen,
            self.back_btn,
            "BACK",
            icon="back"
        )


    def draw_rows(self, table, start_y):

        row_h = self.ROW_H

        medal = {
            1: ui.GOLD,
            2: ui.SILVER,
            3: ui.BRONZE
        }

        for index, row in enumerate(self.rows[:10], start=1):

            y = start_y + (index - 1) * row_h

            rect = pygame.Rect(
                table.x + 16,
                y,
                table.w - 32,
                row_h - 4
            )

            mine = (
                self.my_id is not None
                and row.get("player_id") == self.my_id
            )


            pygame.draw.rect(
                self.screen,
                (12, 62, 135) if mine else (5, 22, 62),
                rect,
                border_radius=6
            )

            pygame.draw.rect(
                self.screen,
                ui.CYAN if mine else (25, 85, 170),
                rect,
                1,
                border_radius=6
            )

            cy = rect.centery


            if index in medal:

                pygame.draw.circle(
                    self.screen,
                    medal[index],
                    (self.COL_RANK, cy),
                    11
                )

                ui.draw_text(
                    self.screen,
                    index,
                    14,
                    ui.BLACK,
                    (self.COL_RANK, cy),
                    "center",
                    True
                )

            else:

                ui.draw_text(
                    self.screen,
                    index,
                    16,
                    ui.WHITE,
                    (self.COL_RANK, cy),
                    "center"
                )


            photo = ui.avatar_surface(row.get("player_id"), 22)

            ui.draw_avatar(
                self.screen,
                self.COL_AVATAR,
                cy,
                12,
                ui.CYAN if mine else ui.NEON,
                photo
            )


            name = ui.fit_text(
                row.get("username", "PLAYER"),
                ui.font(16, mine),
                170
            )

            ui.draw_text(
                self.screen,
                name,
                16,
                ui.CYAN if mine else ui.WHITE,
                (self.COL_NAME, cy),
                "midleft",
                mine
            )


            ui.draw_text(
                self.screen,
                row.get("score", 0),
                16,
                ui.GOLD,
                (self.COL_SCORE, cy),
                "midleft",
                True
            )


            ui.draw_text(
                self.screen,
                row.get("level") or 1,
                16,
                ui.WHITE,
                (self.COL_LEVEL + 12, cy),
                "midleft"
            )


            ui.draw_text(
                self.screen,
                self.format_date(
                    row.get("date_added")
                ),
                13,
                ui.GRAY,
                (self.COL_DATE, cy),
                "midleft"
            )


    @staticmethod
    def format_date(value):

        if not value:
            return "N/A"

        try:
            return value.strftime(
                "%d/%m/%Y %I:%M %p"
            )

        except Exception:
            return str(value)


    def handle_events(self, events):

        self.action = None

        for event in events:


            if (
                event.type == pygame.MOUSEBUTTONDOWN
                and event.button == 1
            ):

                if self.back_btn.collidepoint(event.pos):
                    self.action = "back"


            elif event.type == pygame.KEYDOWN:

                if event.key == pygame.K_ESCAPE:
                    self.action = "back"