from worf.settings import settings
from worf.models import EMailRequest, CryptoToken
from worf.api.resource import Resource

from flask import request

from collections import defaultdict


def client_settings(settings):
    """
    Returns client settings via the API, which clients can use to e.g.
    discover which services are defined.
    """
    client_settings = settings.get("client_settings", {}).copy()
    for provider in settings.providers["client_settings"]:
        client_settings.update(provider())
    providers = defaultdict(list)
    for provider in settings.providers:
        names = provider.split(".")
        if len(names) == 2:
            providers[names[0]].append(names[1])
    client_settings["providers"] = providers
    return client_settings


class ClientSettings(Resource):
    def get(self):
        return {"settings": client_settings(settings)}, 200
