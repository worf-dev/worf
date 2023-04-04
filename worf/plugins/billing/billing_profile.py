from .models import Customer, Subscription, SubscriptionItem, Price, Product
from worf.settings import settings
from sqlalchemy.orm import joinedload


def billing_profile(profile, user, access_token):
    with settings.session() as session:
        limits = {}
        products = settings.get("billing.products")
        subscriptions = (
            session.query(Subscription)
            .join(Customer)
            .options(
                joinedload(Subscription.items)
                .joinedload(SubscriptionItem.price, innerjoin=True)
                .joinedload(Price.product, innerjoin=True)
            )
            .filter(
                Customer.organization_id.in_(
                    [
                        org_role.organization_id
                        for org_role in user.organization_roles
                        if org_role.confirmed
                    ]
                ),
                Subscription.status != "canceled",
            )
            .all()
        )
        for subscription in subscriptions:
            for item in subscription.items:
                item_price = item.price
                limits_data = None
                # by default, we try to fetch the limits data from the database
                # this allows us to easily "grandfather" in existing subscriptions
                if item_price.data is not None and "limits" in item_price.data:
                    limits_data = item_price.data["limits"]
                # if there's no limits data available in the DB, we try to fetch it
                # from the settings instead...
                if limits_data is None:
                    settings_product = next(
                        (p for p in products if p["name"] == item_price.product.name),
                        None,
                    )
                    if settings_product is not None:
                        settings_price = next(
                            (
                                p
                                for p in settings_product.get("_prices", [])
                                if p["name"] == item_price.name
                            ),
                            None,
                        )
                        if settings_price is not None and "limits" in settings_price:
                            limits_data = settings_price["limits"]
                for k, v in limits_data.items():
                    if not k in limits:
                        limits[k] = 0
                    limits[k] += v

        # we only include the subscription if the token has the 'admin' scope
        if access_token.has_scope("admin"):
            profile["subscriptions"] = [
                subscription.export() for subscription in subscriptions
            ]
        # we add the limits to the existing ones...
        if not "limits" in profile:
            profile["limits"] = {}
        for k, v in limits.items():
            if k in profile["limits"]:
                profile["limits"][k] += v
            profile["limits"][k] = v
