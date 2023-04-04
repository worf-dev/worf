from flask import request

from worf.api.resource import Resource
from worf.settings import settings
from ....models import Customer as CustomerModel
from ..forms import CustomerForm

from sqlalchemy.orm import joinedload

from worf.api.decorators.user import authorized
from worf.api.decorators.uuid import valid_uuid
from worf.plugins.organizations.api.v1.decorators import organization_role


class Customer(Resource):

    """
    Return information about the customer for a given organization. Right now
    the rule is that a given organization always has a single customer
    representing that organization.
    """

    @authorized(scopes=("admin",))
    @valid_uuid(field="organization_id")
    @organization_role(roles=("superuser", "admin"))
    def get(self, organization_id):
        """
        Return the customer belonging to the organization.
        """
        with settings.session() as session:
            customer = (
                session.query(CustomerModel)
                .options(joinedload(CustomerModel.organization, innerjoin=True))
                .filter(
                    CustomerModel.organization_id
                    == request.organization_role.organization_id
                )
                .one_or_none()
            )
            return ({"data": customer.export() if customer is not None else None}, 200)

    @authorized(scopes=("admin",))
    @valid_uuid(field="organization_id")
    @organization_role(roles=("superuser", "admin"))
    def post(self, organization_id):
        """
        Return the customer belonging to the organization.
        """
        form = CustomerForm(request.get_json())
        if not form.validate():
            return {"message": self.t("invalid-data"), "errors": form.errors}, 400
        with settings.session() as session:
            org = request.organization_role.organization
            session.add(org)
            customer = CustomerModel.get_or_create(session, org)
            for k, v in form.valid_data.items():
                setattr(customer, k, v)
            # we fill in the user's email by default
            if customer.email is None:
                customer.email = request.user.email
            return ({"data": customer.export()}, 200)
