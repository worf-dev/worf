from flask import request

from worf.api.resource import Resource
from worf.settings import settings
from ....models import Invoice, Subscription, Customer

from sqlalchemy.orm import joinedload

from worf.api.decorators.user import authorized
from worf.api.decorators.uuid import valid_uuid
from worf.plugins.organizations.api.v1.decorators import organization_role


class Invoices(Resource):

    """
    Return information about invoices for a given organization.
    """

    @authorized(scopes=("admin",))
    @valid_uuid(field="organization_id")
    @organization_role(roles=("superuser", "admin"))
    def get(self, organization_id):
        """
        Return all invoices belonging to the organization.
        """
        with settings.session() as session:
            invoices = (
                session.query(Invoice)
                .join(Invoice.subscription)
                .join(Subscription.customer)
                .options(
                    joinedload(Invoice.subscription, innerjoin=True)
                    .joinedload(Subscription.customer, innerjoin=True)
                    .joinedload(Customer.organization, innerjoin=True)
                )
                .filter(
                    Customer.organization_id
                    == request.organization_role.organization_id
                )
                .all()
            )
        return ({"data": [invoice.export() for invoice in invoices]}, 200)
