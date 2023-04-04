from flask import request

from ..forms.organization import (
    OrganizationAdminEditForm,
    OrganizationRoleEditForm,
    OrganizationsForm,
    OrganizationForm,
    OrganizationRoleForm,
)

from worf.api.decorators.user import authorized
from worf.api.decorators.uuid import valid_uuid
from worf.api.resource import Resource
from worf.models import User
from ....models import Organization, OrganizationRole
from ..decorators.organization import organization

from sqlalchemy.sql import and_


class OrganizationRolesAdmin(Resource):

    """
    Administrate organization roles (for superusers).
    """

    @authorized(scopes=("admin",), superuser=True)
    @valid_uuid(field="organization_id")
    @organization()
    def get(self, organization_id):
        """
        Get a list of users for an organization.
        """
        return (
            {
                "roles": [
                    uo.export(with_org=False)
                    for uo in request.organization.organization_roles
                ]
            },
            200,
        )

    @authorized(scopes=("admin",), superuser=True)
    @valid_uuid(field="organization_id")
    @organization()
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
                OrganizationRole.organization != request.organization,
                OrganizationRole.user == user,
            )
            .count()
        )

        if other_organizations:
            return {"message": "user is in other organizations already"}, 400

        role = OrganizationRole.get_or_create(
            request.session,
            user=user,
            organization=request.organization,
            role=form.valid_data["role"],
        )

        request.session.commit()
        return {"organization_role": role.export()}, 201

    @authorized(scopes=("admin",), superuser=True)
    @valid_uuid(field="organization_role_id")
    @valid_uuid(field="organization_id")
    @organization()
    def delete(self, organization_id, organization_role_id):
        """
        Delete a role from an organization.
        """

        organization_role = (
            request.session.query(OrganizationRole)
            .filter(
                OrganizationRole.organization == request.organization,
                OrganizationRole.ext_id == organization_role_id,
            )
            .one_or_none()
        )

        if organization_role is None:
            return {"message": "not found"}, 404

        request.session.delete(organization_role)
        request.session.commit()
        return {"message": "success"}, 200


class OrganizationsAdmin(Resource):

    """
    Administrate organizations (for superusers).
    """

    @authorized(superuser=True, scopes=("admin",))
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

        request.session.add(organization)
        request.session.commit()

        return {"organization": organization.export()}, 201

    @authorized(superuser=True, scopes=("admin",))
    def get(self):
        """
        Get a list of all organizations.
        """
        form = OrganizationsForm(request.args)
        if not form.validate():
            return {"message": "invalid data", "errors": form.errors}, 400

        params = {}

        for key, value in form.valid_data.items():
            if value != "" and value is not None:
                params[key] = value

        queries = []
        if form.valid_data["query"]:
            queries.append(
                Organization.name.ilike("%{}%".format(form.valid_data["query"].strip()))
            )
        organizations = (
            request.session.query(Organization)
            .filter(*queries)
            .order_by(Organization.name)
            .limit(params["limit"] + 1)
            .offset(params["offset"])
        )
        return (
            {
                "organizations": [
                    organization.export()
                    for organization in organizations[: params["limit"]]
                ],
                "has_more": True if organizations.count() > params["limit"] else False,
                "params": params,
            },
            200,
        )

    @authorized(scopes=("admin",), superuser=True)
    @valid_uuid(field="organization_id")
    @organization()
    def patch(self, organization_id):
        """
        Update an organization.
        """
        form = OrganizationAdminEditForm(request.get_json())
        if not form.validate():
            return {"message": "invalid data", "errors": form.errors}, 400
        for key, value in form.valid_data.items():
            setattr(request.organization, key, value)
        request.session.add(request.organization)
        request.session.commit()
        return {"organization": request.organization.export()}, 200

    @authorized(scopes=("admin",), superuser=True)
    @valid_uuid(field="organization_id")
    @organization()
    def delete(self, organization_id):
        """
        Delete an organization.
        """
        request.session.delete(request.organization)
        request.session.commit()
        return {"message": "success"}, 200
