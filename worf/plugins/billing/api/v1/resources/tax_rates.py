from flask import request

from worf.api.resource import Resource
from worf.settings import settings
from ....models import TaxRate

from worf.api.decorators.user import authorized


class TaxRates(Resource):

    """
    Return information about all available tax_rates.
    """

    @authorized(scopes=("admin",))
    def get(self):
        """
        Return all tax_rates.
        """
        with settings.session() as session:
            tax_rates = session.query(TaxRate).all()
        return ({"data": [tax_rate.export() for tax_rate in tax_rates]}, 200)
