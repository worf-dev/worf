from flask import request

from worf.api.resource import Resource
from worf.settings import settings
from ....models import Payment, Invoice, PaymentMethod, Subscription, Customer

from sqlalchemy.orm import joinedload

from worf.api.decorators.user import authorized
from worf.api.decorators.uuid import valid_uuid
from worf.plugins.organizations.api.v1.decorators import organization_role


class Payments(Resource):

    """
    Return information about payments for a given organization.
    """

    @authorized(scopes=("admin",))
    @valid_uuid(field="organization_id")
    @organization_role(roles=("superuser", "admin"))
    def get(self, organization_id):
        """
        Return all payments belonging to the organization.
        """
        with settings.session() as session:
            payments = (
                session.query(Payment)
                .join(Payment.invoice)
                .join(Invoice.subscription)
                .join(Subscription.customer)
                .options(
                    joinedload(Payment.payment_method, innerjoin=True),
                    joinedload(Payment.invoice, innerjoin=True)
                    .joinedload(Invoice.subscription, innerjoin=True)
                    .joinedload(Subscription.customer, innerjoin=True)
                    .joinedload(Customer.organization, innerjoin=True),
                )
                .filter(
                    Customer.organization_id
                    == request.organization_role.organization_id
                )
                .all()
            )
        return ({"data": [payment.export() for payment in payments]}, 200)
