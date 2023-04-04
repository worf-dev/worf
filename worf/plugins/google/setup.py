from .providers import GoogleLogin, GoogleSignup
from worf.settings import settings


def client_settings():
    return {"google": {"client_id": settings.get("google.client_id")}}


config = {
    "providers": {
        "login.google": GoogleLogin,
        "signup.google": GoogleSignup,
        "client_settings": client_settings,
    }
}
