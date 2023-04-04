from .providers import PasswordLogin, PasswordSignup
from .api.v1.routes import routes

config = {
    "api": [{"routes": routes, "version": "v1"}],
    "providers": {"login.password": PasswordLogin, "signup.password": PasswordSignup},
}
