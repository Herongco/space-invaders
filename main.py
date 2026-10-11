import pygame

from db import setup_database
from settings_manager import load_settings
from managers.login_screen import LoginManager
from managers.game_manager import GameManager
from managers.home import Home
from managers.profile import Profile
from managers.leader import Leader
from managers.level_select import LevelSelect
from managers.settings import Settings, apply_audio
from managers import ui

pygame.init()

try:
    pygame.mixer.init()
except pygame.error as e:
    print("AUDIO NOT AVAILABLE:", e)

SCREEN_WIDTH = 1000
SCREEN_HEIGHT = 680

screen = pygame.display.set_mode(
    (SCREEN_WIDTH, SCREEN_HEIGHT)
)

pygame.display.set_caption(
    "Space Invaders by Herongco, Rochel T."
)

if not setup_database():
    print("WARNING: database setup failed - is MySQL (XAMPP) running?")

ui.start_music()
apply_audio(load_settings())

login = LoginManager(
    screen,
    SCREEN_WIDTH,
    SCREEN_HEIGHT
)

game = GameManager(
    screen,
    SCREEN_WIDTH,
    SCREEN_HEIGHT
)

home = None
profile = None
leader = None
settings_screen = None
levels = None
current_screen = "login"


def make_home():
    return Home(
        screen,
        SCREEN_WIDTH,
        SCREEN_HEIGHT,
        login.logged_in_player
    )


clock = pygame.time.Clock()
running = True

while running:

    events = pygame.event.get()

    for event in events:
        if event.type == pygame.QUIT:
            running = False

        elif event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            ui.play_click_if_button(event.pos)

    ui.clear_click_areas()

    if current_screen == "game":
        ui.set_level_background(getattr(game, "level", None))
    else:
        ui.set_level_background(None)

    if current_screen == "login":

        login.handle_events(events)
        login.draw()

        if login.logged_in_player is not None:
            home = make_home()
            current_screen = "home"

    elif current_screen == "home":

        home.handle_events(events)
        home.draw()

        if home.action == "profile":

            home.action = None

            profile = Profile(
                screen,
                SCREEN_WIDTH,
                SCREEN_HEIGHT,
                login.logged_in_player
            )

            current_screen = "profile"

        elif home.action == "leaderboard":

            home.action = None

            leader = Leader(
                screen,
                SCREEN_WIDTH,
                SCREEN_HEIGHT,
                login.logged_in_player
            )

            current_screen = "leader"

        elif home.action == "settings":

            home.action = None

            settings_screen = Settings(
                screen,
                SCREEN_WIDTH,
                SCREEN_HEIGHT,
                login.logged_in_player
            )

            current_screen = "settings"

        elif home.action == "play":

            home.action = None

            levels = LevelSelect(
                screen,
                SCREEN_WIDTH,
                SCREEN_HEIGHT,
                login.logged_in_player
            )

            current_screen = "levels"

        elif home.action == "logout":

            home.action = None

            login.logout()
            home = None
            profile = None
            leader = None
            settings_screen = None
            levels = None

            current_screen = "login"

    elif current_screen == "profile":

        profile.handle_events(events)
        profile.draw()

        if profile.player is not None:
            login.logged_in_player = profile.player

        if profile.action == "back":

            profile.action = None
            home = make_home()
            current_screen = "home"

        elif profile.action == "deleted":

            login.logout()
            profile = None
            home = None
            leader = None
            settings_screen = None

            current_screen = "login"

    elif current_screen == "leader":

        leader.handle_events(events)
        leader.draw()

        if leader.action == "back":

            leader.action = None
            home = make_home()
            current_screen = "home"

    elif current_screen == "settings":

        settings_screen.handle_events(events)
        settings_screen.draw()

        if settings_screen.action == "back":

            settings_screen.action = None
            home = make_home()
            current_screen = "home"

    elif current_screen == "levels":

        levels.handle_events(events)
        levels.draw()

        if levels.action == "back":

            levels.action = None
            home = make_home()
            current_screen = "home"

        elif levels.action == "start":

            levels.action = None

            game.current_player_id = (
                login.logged_in_player["player_id"]
            )

            game.player_name = (
                login.logged_in_player["username"]
            )

            game.start_again(levels.start_level)

            current_screen = "game"

    elif current_screen == "game":

        game.update(events)
        game.draw()

        if game.game_state == "back_levels":

            game.game_state = "playing"

            levels = LevelSelect(
                screen,
                SCREEN_WIDTH,
                SCREEN_HEIGHT,
                login.logged_in_player
            )

            current_screen = "levels"

        elif game.game_state == "back_home":

            game.game_state = "playing"
            home = make_home()
            current_screen = "home"

    pygame.display.update()
    clock.tick(60)

pygame.quit()