from worf.utils.forms import Form, Field, Subform, String, Integer, Optional


class DatabaseForm(Form):
    url = Field([String()])
    user = Field([Optional(), String()])
    password = Field([Optional(), String()])
    host = Field([Optional(), String()])
    ports = Field([Optional(), Integer()])


class SettingsForm(Form):
    db = Field([Subform(DatabaseForm)])
