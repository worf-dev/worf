from .models import clean_db
from .api.v1.routes import routes
from .providers import providers
from .billing_profile import billing_profile
from .cli import billing

from worf.settings import settings


def client_settings():
    provider_settings = {}
    for provider_name, provider_class in providers.items():
        provider = provider_class()
        if hasattr(provider, "client_settings"):
            provider_settings[provider_name] = provider.client_settings
    provider_settings["providers"] = list(providers.keys())
    return {"billing": provider_settings}


api_routes = routes.copy()
# we add all provider API routes
for provider_name, provider_class in providers.items():
    provider = provider_class()
    provider_routes = provider.routes
    prefixed_routes = []
    for route in provider_routes:
        key, params = list(route.items())[0]
        prefixed_routes.append({"/" + provider_name + key: params})
    api_routes.extend(prefixed_routes)

config = {
    "clean_db": clean_db,
    "api": [{"routes": api_routes, "version": "v1"}],
    "commands": [billing],
    "models": [],
    "providers": {"client_settings": client_settings, "profile": billing_profile},
    "hooks": {},
}
