from worf.settings import settings
from ....models import Subscription, Customer

from flask import request

from functools import wraps


def valid_subscription(f=None, id_field="subscription_id"):
    """
    Ensures that the user has one of the specified roles in the organization.
    """

    def decorator(f):
        @wraps(f)
        def valid_subscription(*args, **kwargs):
            if not hasattr(request, "organization_role"):
                return {"message": "Organization role missing."}, 400
            if not id_field in kwargs:
                return {"message": "Subscription ID missing."}, 400
            subscription_id = kwargs[id_field]
            try:
                subscription = (
                    request.session.query(Subscription)
                    .join(Customer)
                    .filter(
                        Subscription.ext_id == subscription_id,
                        Customer.organization_id
                        == request.organization_role.organization_id,
                    )
                    .one_or_none()
                )
            except ValueError:
                return {"message": "Invalid subscription ID."}, 400
            if subscription is None:
                return {"message": "Subscription not found."}, 404
            request.subscription = subscription
            return f(*args, **kwargs)

        return valid_subscription

    if f:
        return decorator(f)
    else:
        return decorator
