from worf.utils.forms import Form, Field
from worf.settings import settings
from worf.utils.forms.validators import (
    String,
    Optional,
    Required,
    EMail,
    Boolean,
    Equal,
    Choices,
    Regex,
)

from google.oauth2 import id_token
from google.auth.transport import requests


class GoogleIDToken:
    def __call__(self, name, value, form):
        client_id = settings.get("google.client_id")
        test = settings.get("test")

        if test:
            if value == "1234":
                # this returns a test token
                return (
                    [],
                    {
                        "iss": "accounts.google.com",
                        "azp": "1094985475488-[...].apps.googleusercontent.com",
                        "aud": "1094985475488-[...].apps.googleusercontent.com",
                        "sub": "1234",
                        "email": "max.mustermann@googlemail.com",
                        "email_verified": True,
                        "at_hash": "[hash]",
                        "name": "Max",
                        "picture": "https://lh3.googleusercontent.com/[...]/photo.jpg",
                        "given_name": "Mustermann",
                        "locale": "de",
                        "iat": 1347947492,
                        "exp": 1943351292,
                        "jti": "[numerical value]",
                    },
                    False,
                )
            return ["not a valid token"], None, True

        try:
            id_info = id_token.verify_oauth2_token(value, requests.Request(), client_id)
            return [], id_info, False
        except ValueError:
            return ["not a valid token"], None, True


class GoogleForm(Form):
    id_token = Field([Required(), String(), GoogleIDToken()])


class GoogleIDTokenForm(Form):
    sub = Field([Required(), String(), Regex(r"^\d+$")])
    email = Field([Required(), EMail()])
    email_verified = Field([Required(), Boolean(), Equal(True)])
    iss = Field(
        [
            Required(),
            String(),
            Choices(["accounts.google.com", "https://accounts.google.com"]),
        ]
    )
