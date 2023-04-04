from flask import request
import datetime
from worf.api.resource import Resource
from worf.settings import settings
from ....models import Subscription, SubscriptionItem, Customer, TaxRate
from ....helpers import get_provider

from sqlalchemy.orm import joinedload
from ..forms.products import ProductsForm
from ..decorators import valid_price, valid_subscription
from worf.api.decorators.user import authorized
from worf.api.decorators.uuid import valid_uuid
from worf.plugins.organizations.api.v1.decorators import organization_role


class SubscriptionItems(Resource):
    pass


def get_customer_tax_rate(session, customer):
    tax_rates = session.query(TaxRate).filter(TaxRate.active == True).all()
    today = datetime.date.today()
    for tax_rate in tax_rates:
        if (tax_rate.valid_from is not None and tax_rate.valid_from > today) or (
            tax_rate.valid_until is not None and tax_rate.valid_until < today
        ):
            continue  # this tax rate is not valid
        ctx = {"customer": customer}
        # we check if the tax rate applies to the customer
        if eval(tax_rate.rule, ctx, ctx):
            return tax_rate
    return None


class Subscriptions(Resource):

    """
    Return information about subscriptions for a given organization.
    """

    @authorized(scopes=("admin",))
    @valid_uuid(field="organization_id")
    @organization_role(roles=("superuser", "admin"))
    @valid_price
    def post(self, organization_id, price_id):
        """
        Subscribe the organization to the given price.

        - Ensure a customer exists for the organization
        - Ensure no other subscription exists for the the same product
        - Create a subscription and add the price as an item
        - Return the subscription ID
        """

        form = ProductsForm(request.get_json())
        if not form.validate():
            return {"message": "invalid data", "errors": form.errors}, 400
        access_code = form.valid_data.get("access_code")
        with settings.session() as session:
            org = request.organization_role.organization
            session.add(org)
            session.add(request.price)
            if request.price.restricted:
                if access_code is None or not access_code in request.price.access_codes:
                    return {"message": "invalid access code for restricted price"}, 400
            customer = Customer.get(session, org)
            if customer is None:
                return {"message": "create a customer first"}, 400
            active_subscriptions = (
                session.query(Subscription)
                .options(
                    joinedload(Subscription.items).joinedload(
                        SubscriptionItem.tax_rate
                    ),
                    joinedload(Subscription.customer).joinedload(Customer.organization),
                )
                .filter(
                    Subscription.customer == customer,
                    Subscription.status.notin_(["canceled"]),
                )
            ).all()
            for subscription in active_subscriptions:
                for item in subscription.items:
                    if item.price.product_id == request.price.product_id:
                        # this subscription is for the same product
                        if subscription.status == "initialized":
                            # there already is one subscription that has been initialized
                            return {"data": subscription.export()}, 200
                        else:
                            return (
                                {
                                    "message": "there already is an active subscription for this product"
                                },
                                400,
                            )
            customer_tax_rate = get_customer_tax_rate(session, customer)
            if customer_tax_rate is None:
                return (
                    {
                        "code": "no-tax-rate",
                        "message": "cannot determine your tax rate",
                    },
                    400,
                )
            # seems there's no subscription for this product yet, we create one
            subscription = Subscription(
                customer=customer,
                start_date=datetime.date.today(),
                trial_end_date=datetime.date.today()
                + datetime.timedelta(days=settings.get("billing.trial_days", 7)),
                items=[
                    SubscriptionItem(
                        price=request.price, tax_rate=customer_tax_rate, quantity=1
                    )
                ],
            )
            # if the price is zero, we already activate the subscription without a checkout
            if request.price.unit_amount == 0:
                subscription.status = "active"

            session.add(subscription)

            # we remove the access code from the price, except if it starts
            # with the "unlimited-" prefix...
            if request.price.restricted and not access_code.startswith("unlimited-"):
                session.add(request.price)
                # we remove the access code from the price
                request.price.access_codes.remove(access_code)

            session.commit()

            return {"data": subscription.export()}, 200

    @authorized(scopes=("admin",))
    @valid_uuid(field="organization_id")
    @organization_role(roles=("superuser", "admin"))
    @valid_subscription
    def delete(self, organization_id, subscription_id):
        """
        Cancel the given subscription (or delete it if it is not yet active).
        """
        if not request.subscription.providers:
            request.session.delete(request.subscription)
            return {"message": "subscription deleted"}, 200
        else:
            for subscription_provider in request.subscription.providers:
                provider = get_provider(subscription_provider.provider)
                # we cancel the subscription
                provider.subscriptions.cancel(subscription_provider)
            return {"message": "subscription canceled"}, 200

    @authorized(scopes=("admin",))
    @valid_uuid(field="organization_id")
    @organization_role(roles=("superuser", "admin"))
    def get(self, organization_id):
        """
        Return all subscriptions belonging to the organization.
        """
        with settings.session() as session:
            subscriptions = (
                session.query(Subscription)
                .join(Subscription.customer)
                .options(
                    joinedload(Subscription.customer, innerjoin=True).joinedload(
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
                {"data": [subscription.export() for subscription in subscriptions]},
                200,
            )
