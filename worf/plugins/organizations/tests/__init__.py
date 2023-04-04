# we load the test settings

from worf.settings import load_settings, settings
import os

base_path = os.path.dirname(__file__)
settings_path = os.path.join(base_path, "settings/test.yml")
s = load_settings([settings_path])
settings.update(s)
