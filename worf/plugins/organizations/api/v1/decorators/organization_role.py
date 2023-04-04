from worf.settings import settings
from ....models import Organization, OrganizationRole

from flask import request

from functools import wraps
from sqlalchemy.orm import joinedload


def organization_role(f=None, id_field="organization_id", roles=("superuser",)):
    """
    Ensures that the user has one of the specified roles in the organization.
    """

    def decorator(f):
        @wraps(f)
        def organization_role(*args, **kwargs):
            if not hasattr(request, "user"):
                return {"message": "You need to be authenticated."}, 403
            if not id_field in kwargs:
                return {"message": "Organization ID missing."}, 400
            organization_id = kwargs[id_field]
            try:
                organization_role = (
                    request.session.query(OrganizationRole)
                    .join(Organization)
                    .options(joinedload(OrganizationRole.organization, innerjoin=True))
                    .filter(
                        Organization.ext_id == organization_id,
                        OrganizationRole.user == request.user,
                        OrganizationRole.role.in_(roles),
                    )
                    .first()
                )
            except ValueError:
                return {"message": "Invalid organization ID."}, 400
            if organization_role is None:
                return {"message": "Role not found."}, 404
            request.organization_role = organization_role
            return f(*args, **kwargs)

        return organization_role

    if f:
        return decorator(f)
    else:
        return decorator
