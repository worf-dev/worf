from .providers import GitlabLogin, GitlabSignup
from worf.settings import settings


def client_settings():
    gh = settings.get("gitlab")
    return {
        "gitlab": {
            "client_id": gh["client_id"],
            "redirect_uri": gh["redirect_uri"],
            "scope": gh["scope"],
            "host": gh["host"],
            "authorize_path": gh["authorize_path"],
        }
    }


config = {
    "providers": {
        "login.gitlab": GitlabLogin,
        "signup.gitlab": GitlabSignup,
        "client_settings": client_settings,
    }
}
