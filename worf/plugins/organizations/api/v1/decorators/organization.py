from worf.settings import settings
from ....models import Organization

from flask import request
from functools import wraps


def organization(f=None, id_field="organization_id"):
    """
    Ensures that the user has one of the specified roles in the organization.
    """

    def decorator(f):
        @wraps(f)
        def organization(*args, **kwargs):
            if not id_field in kwargs:
                return {"message": "Organization ID missing."}, 400
            organization_id = kwargs[id_field]
            try:
                organization = (
                    request.session.query(Organization)
                    .filter(Organization.ext_id == organization_id)
                    .one_or_none()
                )
            except ValueError:
                return {"message": "Invalid organization ID."}, 400
            if organization is None:
                return {"message": "Organization not found."}, 404
            request.organization = organization
            return f(*args, **kwargs)

        return organization

    if f:
        return decorator(f)
    else:
        return decorator
