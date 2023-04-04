from flask import request

from worf.api.resource import Resource
from worf.settings import settings
from ....models import Customer, CustomerProvider, SubscriptionProvider

from worf.api.decorators.user import authorized
from worf.api.decorators.uuid import valid_uuid
from worf.plugins.organizations.api.v1.decorators import organization_role
from ..decorators import valid_subscription
from ....helpers import get_provider

import datetime
import logging

logger = logging.getLogger(__name__)


class Checkout(Resource):

    """
    Check out the given customer with the given provider.
    """

    @authorized(scopes=("admin",))
    @valid_uuid(field="organization_id")
    @organization_role(roles=("superuser", "admin"))
    @valid_subscription
    def post(self, organization_id, subscription_id, provider_name):
        """
        Check out the customer with the given provider.
        """
        try:
            provider = get_provider(provider_name)
        except KeyError:
            return {"message": "invalid provider"}, 400

        with settings.session() as session:
            org = request.organization_role.organization
            session.add(org)
            customer = Customer.get(session, org)
            customer_provider = CustomerProvider.get_or_create(
                session, customer, provider.name
            )

            # we create the customer at the provider
            provider.customers.update_or_create(customer_provider)

            # we save the update to make sure it's persisted
            session.commit()

            # we add the customer and the subscription again
            session.add(customer_provider)
            session.add(request.subscription)

            # we move the trial end date to 7 days from now
            request.subscription.trial_end_date = (
                datetime.date.today()
                + datetime.timedelta(days=settings.get("billing.trial_days", 7))
            )

            # we save the subscription to make sure the provider will see the update...
            session.commit()

            subscription_provider = SubscriptionProvider.get_or_create(
                session, request.subscription, provider.name
            )

            # we create the subscription at the provider
            provider.subscriptions.update_or_create(subscription_provider)

            if (
                subscription_provider.default_payment_method is not None
                or request.subscription.status in ("active")
            ):
                # the subscription is already active or we already have a payment method!
                # we return it immediately with a 201 result
                return {"data": request.subscription.export()}, 201

            data, client_data = provider.checkouts.create(
                customer_provider,
                subscription_provider,
                {"subscription": request.subscription.ext_id},
            )
            return {"data": client_data}, 200
