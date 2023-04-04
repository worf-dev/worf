from flask import request

from worf.api.decorators.user import authorized
from worf.api.resource import Resource
from .....helpers import get_provider


class Sync(Resource):

    """
    Synchronize provider data (e.g. prices, taxes, ...)
    """

    @authorized(scopes=("admin",), superuser=True)
    def post(self, provider_name=None):
        """
        Get a list of users for an organization.
        """
        provider = get_provider(provider_name)
        return {"data": provider.sync()}, 200
