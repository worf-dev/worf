from worf.utils.forms import Form, Field
from worf.utils.forms.validators import Optional, Length, DateTime, String
from .validators import Scopes, InFuture


class AccessTokenForm(Form):
    def __init__(self, *args, superuser=False, **kwargs):
        super().__init__(*args, **kwargs)
        self.superuser = superuser

    scopes = Field([Scopes()])
    valid_until = Field([Optional(), DateTime(), InFuture()])
    description = Field([Optional(), String(), Length(max=80)])
