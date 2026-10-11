import json
import os

SETTINGS_FILE = os.path.join(
    os.path.dirname(os.path.abspath(__file__)),
    "settings.json"
)

DEFAULT_SETTINGS = {
    "sound_volume": 80,
    "music_enabled": True,
    "sound_enabled": True,
    "mobile_controls": False,
    "remembered_user": ""
}


def load_settings():
    settings = dict(DEFAULT_SETTINGS)

    if not os.path.exists(SETTINGS_FILE):
        save_settings(settings)
        return settings

    try:
        with open(SETTINGS_FILE, "r") as file:
            data = json.load(file)

        if isinstance(data, dict):
            settings.update(data)
            settings.pop("graphics_quality", None)

    except (json.JSONDecodeError, IOError):
        pass

    return settings


def save_settings(settings):
    try:
        with open(SETTINGS_FILE, "w") as file:
            json.dump(settings, file, indent=4)
    except IOError as e:
        print(f"Error sa pag-save: {e}")