from flask import request

from worf.api.resource import Resource
from worf.settings import settings
from ....models import PaymentMethod, Customer

from sqlalchemy.orm import joinedload

from worf.api.decorators.user import authorized
from worf.api.decorators.uuid import valid_uuid
from worf.plugins.organizations.api.v1.decorators import organization_role


class PaymentMethods(Resource):

    """
    Return information about payment_methods for a given organization.
    """

    @authorized(scopes=("admin",))
    @valid_uuid(field="organization_id")
    @organization_role(roles=("superuser", "admin"))
    def get(self, organization_id):
        """
        Return all payment_methods belonging to the organization.
        """
        with settings.session() as session:
            payment_methods = (
                session.query(PaymentMethod)
                .join(Customer)
                .options(
                    joinedload(PaymentMethod.customer, innerjoin=True).joinedload(
                        Customer.organization, innerjoin=True
                    )
                )
                .filter(
                    Customer.organization_id
                    == request.organization_role.organization_id
                )
                .all()
            )
        return (
            {"data": [payment_method.export() for payment_method in payment_methods]},
            200,
        )
