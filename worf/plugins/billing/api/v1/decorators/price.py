from worf.settings import settings
from ....models import Price

from flask import request
from functools import wraps


def valid_price(f=None, id_field="price_id"):
    """
    Ensures that the user has one of the specified roles in the organization.
    """

    def decorator(f):
        @wraps(f)
        def valid_price(*args, **kwargs):
            if not id_field in kwargs:
                return {"message": "Price ID missing."}, 400
            price_id = kwargs[id_field]
            try:
                price = (
                    request.session.query(Price)
                    .filter(Price.ext_id == price_id)
                    .one_or_none()
                )
            except ValueError:
                return {"message": "Invalid price ID."}, 400
            if price is None:
                return {"message": "Price not found."}, 404
            request.price = price
            return f(*args, **kwargs)

        return valid_price

    if f:
        return decorator(f)
    else:
        return decorator
