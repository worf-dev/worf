from flask import request
from ..forms.organization import (
    OrganizationEditForm,
    OrganizationRoleEditForm,
    OrganizationRoleForm,
    OrganizationForm,
)

from worf.api.decorators.user import authorized
from worf.api.decorators.uuid import valid_uuid
from worf.api.resource import Resource
from worf.settings import settings
from worf.models import User
from ....models import Organization, OrganizationRole
from ..decorators import organization_role

from sqlalchemy.sql import and_, exists


class OrganizationRoles(Resource):

    """
    Manage organization roles.
    """

    @authorized(scopes=("admin",))
    @valid_uuid(field="organization_id")
    @organization_role(roles=("superuser",))
    def get(self, organization_id):
        """
        Get a list of users roles for an organization.
        """
        return (
            {
                "users": [
                    uo.export()
                    for uo in request.session.query(OrganizationRole)
                    .filter(
                        OrganizationRole.organization_id
                        == request.organization_role.organization_id
                    )
                    .all()
                ]
            },
            200,
        )

    @authorized(scopes=("admin",))
    @valid_uuid(field="organization_id")
    @organization_role(roles=("superuser",))
    def post(self, organization_id):
        """
        Add a user to an organization.
        """
        form = OrganizationRoleForm(request.get_json())
        if not form.validate():
            return {"message": "invalid data", "errors": form.errors}, 400

        user = User.get_by_email(request.session, form.valid_data["email"])

        if user is None:
            return {"message": "invalid user"}, 404

        other_organizations = (
            request.session.query(Organization.id)
            .distinct()
            .join(OrganizationRole)
            .filter(
                OrganizationRole.organization != request.organization_role.organization,
                OrganizationRole.user == user,
            )
            .count()
        )

        if other_organizations:
            return {"message": "user is in other organizations already"}, 400

        role = OrganizationRole.get_or_create(
            request.session,
            user=user,
            organization=request.organization_role.organization,
            role=form.valid_data["role"],
        )
        request.session.commit()
        return {"organization_role": role.export()}, 201

    @authorized(scopes=("admin",))
    @valid_uuid(field="organization_id")
    @organization_role(roles=("superuser",))
    def delete(self, organization_id, organization_role_id):
        """
        Delete a role from an organization.
        """

        organization_role = (
            request.session.query(OrganizationRole)
            .filter(
                and_(
                    OrganizationRole.organization
                    == request.organization_role.organization,
                    OrganizationRole.ext_id == organization_role_id,
                )
            )
            .one_or_none()
        )

        if organization_role is None:
            return {"message": "not found"}, 404

        if organization_role == request.organization_role:
            return (
                {
                    "message": "you cannot remove your own superuser role from your organization"
                },
                400,
            )

        request.session.delete(organization_role)
        request.session.commit()
        return {"message": "success"}, 200


class Organizations(Resource):

    """
    Create modify and retrieve organization details (for normal users).
    """

    @authorized(scopes=("admin",))
    @valid_uuid(field="organization_id")
    @organization_role(roles=("member", "admin", "superuser"))
    def get(self, organization_id):
        """
        Return organization details.
        """
        return {"organization": request.organization_role.export(org_view=True)}, 200

    @authorized(scopes=("admin",))
    def post(self):
        """
        Create a new organization.
        """
        form = OrganizationForm(request.get_json())

        if not form.validate():
            return {"message": "invalid data", "errors": form.errors}, 400
        organization = Organization()

        for key, value in form.valid_data.items():
            setattr(organization, key, value)

        organizations_count = (
            request.session.query(Organization.id)
            .distinct()
            .join(OrganizationRole)
            .filter(OrganizationRole.user == request.user)
            .count()
        )

        if organizations_count > 0:
            return {"message": "You are already associated with an organization."}, 400

        request.session.add(organization)
        organization_role = OrganizationRole(
            user=request.user, organization=organization, role="superuser"
        )
        request.session.add(organization_role)
        request.session.commit()
        return {"organization": organization.export()}, 201

    @authorized(scopes=("admin",))
    @valid_uuid(field="organization_id")
    @organization_role(roles=("superuser",))
    def patch(self, organization_id):
        """
        Update an organization.
        """
        organization = request.organization_role.organization
        form = OrganizationEditForm(request.get_json())
        if not form.validate():
            return {"message": "invalid data", "errors": form.errors}, 400
        params = {}
        for key, value in form.valid_data.items():
            setattr(organization, key, value)
        request.session.add(organization)
        # we explicitly commit this as we want to catch errors
        request.session.commit()
        return {"organization": organization.export()}, 200

    @authorized(scopes=("admin",))
    @valid_uuid(field="organization_id")
    @organization_role(roles=("superuser",))
    def delete(self, organization_id):
        """
        Delete an organization.
        """
        request.session.delete(request.organization_role.organization)
        return {"message": "success"}, 200
