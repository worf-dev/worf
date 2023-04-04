from worf.settings import settings
from .providers import providers


def get_provider(provider_name=None):
    if provider_name is None:
        provider_name = settings.get("billing.default_provider")
    if not provider_name in providers:
        raise KeyError(f"Unknown provider: {provider_name}")
    return providers[provider_name]()
