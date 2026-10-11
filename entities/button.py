import math

import pygame

CYAN = (40, 245, 255)
NEON = (40, 180, 255)
WHITE = (235, 250, 255)
ORANGE = (255, 150, 60)
RED = (255, 80, 90)


class MobileButtons:

    def __init__(self):
        self.left = pygame.Rect(16, 606, 66, 50)
        self.right = pygame.Rect(92, 606, 66, 50)

        self.fire_center = (942, 632)
        self.fire_radius = 30
        self.fire = pygame.Rect(
            self.fire_center[0] - self.fire_radius,
            self.fire_center[1] - self.fire_radius,
            self.fire_radius * 2,
            self.fire_radius * 2,
        )


    def over_fire(self, pos):
        dx = pos[0] - self.fire_center[0]
        dy = pos[1] - self.fire_center[1]
        return dx * dx + dy * dy <= self.fire_radius ** 2

    def pressed(self, rect=None, fire=False):
        if not pygame.mouse.get_pressed()[0]:
            return False

        pos = pygame.mouse.get_pos()

        if fire:
            return self.over_fire(pos)

        return rect.collidepoint(pos)


    def draw(self, screen):
        self.draw_arrow_button(screen, self.left, "left",
                               self.pressed(self.left))
        self.draw_arrow_button(screen, self.right, "right",
                               self.pressed(self.right))
        self.draw_fire_button(screen, self.pressed(fire=True))

    def draw_arrow_button(self, screen, rect, direction, down):
        layer = pygame.Surface(rect.size, pygame.SRCALPHA)

        fill = (30, 110, 230, 190) if down else (6, 24, 66, 150)
        pygame.draw.rect(layer, fill, layer.get_rect(), border_radius=12)
        screen.blit(layer, rect.topleft)

        border = CYAN if down else NEON
        pygame.draw.rect(screen, border, rect, 2, border_radius=12)
        pygame.draw.rect(screen, (20, 70, 160), rect.inflate(-8, -8), 1,
                         border_radius=9)

        cx, cy = rect.center
        s = 11 if down else 12
        d = -1 if direction == "left" else 1

        arrow = [
            (cx + d * s, cy),
            (cx - d * s * 0.5, cy - s),
            (cx - d * s * 0.5, cy + s),
        ]
        pygame.draw.polygon(screen, WHITE if down else CYAN, arrow)

    def draw_fire_button(self, screen, down):
        cx, cy = self.fire_center
        r = self.fire_radius - (2 if down else 0)

        size = self.fire_radius * 2 + 20
        layer = pygame.Surface((size, size), pygame.SRCALPHA)
        mid = size // 2

        pygame.draw.circle(layer, (255, 80, 60, 60), (mid, mid), r + 6)

        body = (255, 110, 70, 235) if down else (200, 40, 55, 200)
        pygame.draw.circle(layer, body, (mid, mid), r)
        screen.blit(layer, (cx - mid, cy - mid))

        pygame.draw.circle(screen, (255, 220, 200) if down else ORANGE,
                           (cx, cy), r, 2)
        pygame.draw.circle(screen, (255, 170, 150), (cx, cy), r - 7, 1)

        color = WHITE
        pygame.draw.circle(screen, color, (cx, cy - 4), 8, 2)
        pygame.draw.circle(screen, color, (cx, cy - 4), 2)
        for a in range(4):
            ang = a * math.pi / 2
            pygame.draw.line(
                screen, color,
                (cx + math.cos(ang) * 6, cy - 4 + math.sin(ang) * 6),
                (cx + math.cos(ang) * 11, cy - 4 + math.sin(ang) * 11), 2)

        if not hasattr(self, "_font"):
            self._font = pygame.font.SysFont("consolas", 11, bold=True)
        font = self._font
        label = font.render("FIRE", True, color)
        screen.blit(label, label.get_rect(center=(cx, cy + 18)))


    def handle_mouse(self, player, events):
        if pygame.mouse.get_pressed()[0]:
            mouse_pos = pygame.mouse.get_pos()

            if self.left.collidepoint(mouse_pos):
                player.move_left()

            if self.right.collidepoint(mouse_pos):
                player.move_right()

            if self.over_fire(mouse_pos):
                return True

        for event in events:
            if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                if self.over_fire(event.pos):
                    return True

        return False