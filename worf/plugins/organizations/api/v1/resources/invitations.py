from flask import request

from worf.api.decorators.user import authorized
from worf.api.decorators.uuid import valid_uuid
from worf.api.resource import Resource
from worf.api.v1.resources.user.invitations import send_invitation
from worf.models import User, Invitation, EMailRequest
from worf.settings import settings
from ....models import Organization, OrganizationRole, OrganizationInvitation
from ..forms.organization import OrganizationInvitationForm
from ..decorators import organization_role


class OrganizationInvitations(Resource):

    """
    Invite users to organization.
    """

    @authorized(scopes=("admin",))
    @valid_uuid(field="organization_id")
    @organization_role(roles=("superuser",))
    def get(self, organization_id):
        """
        Get a list of invitations for an organization.
        """
        return (
            {
                "invitations": [
                    oi.export(with_org=False)
                    for oi in request.organization_role.organization.organization_invitations
                ]
            },
            200,
        )

    @authorized(scopes=("admin",))
    @organization_role(roles=("superuser",))
    @valid_uuid(field="organization_id")
    def post(self, organization_id):
        """
        Create a new invitation for an organization.
        """
        form = OrganizationInvitationForm(request.get_json())
        if not form.validate():
            return {"message": "invalid data", "errors": form.errors}, 400

        user = User.get_by_email(request.session, form.valid_data["email"])

        if user is not None:
            other_organizations = (
                request.session.query(Organization.id)
                .distinct()
                .join(OrganizationRole)
                .filter(
                    OrganizationRole.organization_id
                    != request.organization_role.organization_id,
                    OrganizationRole.user == user,
                )
                .count()
            )

            if other_organizations:
                return {"message": "user is in other organizations already"}, 400

            role = OrganizationRole.get_or_create(
                request.session,
                user=user,
                organization=organization_role.organization,
                role=form.valid_data["role"],
            )

            request.session.commit()
            return {"organization_role": role.export()}, 201

        invitation = Invitation()
        for key, value in form.valid_data.items():
            setattr(invitation, key, value)

        invitation.invitation_type = "organization"
        invitation.inviting_user_id = request.user.id

        existing_invitation = Invitation.get_by_email(request.session, invitation.email)

        if existing_invitation:
            return {"message": self.t("invitations.already-exists")}, 400

        if not EMailRequest.request(request.session, "invitation", invitation.email):
            return {"message": self.t("cannot-send-email")}, 400

        request.session.add(invitation)
        request.session.commit()

        org_invitation = OrganizationInvitation(
            invitation_id=invitation.id,
            organization_id=request.organization_role.organization_id,
            role=form.valid_data["role"],
        )

        request.session.add(org_invitation)
        request.session.commit()

        settings.delay(
            send_invitation,
            data={
                "token": invitation.token,
                "email": invitation.email,
                "inviting_user_email": invitation.inviting_user.email,
                "message": invitation.message,
            },
            language=request.user.language,
        )

        return org_invitation.export(), 201

    @authorized(scopes=("admin",))
    @valid_uuid(field="organization_id")
    @valid_uuid(field="organization_invitation_id")
    @organization_role(roles=("superuser",))
    def delete(self, organization_id, organization_invitation_id):
        """
        Delete an invtation from an organization.
        """

        org_invitation = OrganizationInvitation.get_by_ext_id(
            request.session, organization_invitation_id
        )
        # we check if the invitation exists and if it actually belongs to the
        # organization that the user has requested
        if (
            org_invitation is None
            or org_invitation.organization_id
            != request.organization_role.organization_id
        ):
            return {"message": self.t("not-found")}, 404
        request.session.delete(org_invitation.invitation)
        request.session.delete(org_invitation)
        return {"message": self.t("success")}, 200
