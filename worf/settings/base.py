from worf.utils.settings import Settings, load_settings
import os

settings_filenames = []

# finally we load custom settings...
_worf_settings_d = os.environ.get("WORF_SETTINGS_D", "").split(":")
if _worf_settings_d:
    for s in _worf_settings_d:
        settings_directory = os.path.abspath(s)
        if not os.path.exists(settings_directory):
            continue
        settings_filenames += [
            os.path.join(settings_directory, fn)
            for fn in sorted(os.listdir(settings_directory))
            if fn.endswith(".yml") and not fn.startswith(".")
        ]

raw_settings = load_settings(settings_filenames)
settings = Settings(raw_settings)
