from .providers import GithubLogin, GithubSignup
from worf.settings import settings


def client_settings():
    gh = settings.get("github")
    return {
        "github": {
            "client_id": gh["client_id"],
            "redirect_uri": gh["redirect_uri"],
            "scope": gh["scope"],
            "host": gh["host"],
            "authorize_path": gh["authorize_path"],
        }
    }


config = {
    "providers": {
        "login.github": GithubLogin,
        "signup.github": GithubSignup,
        "client_settings": client_settings,
    }
}
