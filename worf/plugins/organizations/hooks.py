from worf.settings import settings
from .models import OrganizationRole, OrganizationInvitation


def confirm_invite_and_setup_role(invitation):
    with settings.session() as session:
        org_invite = OrganizationInvitation.get_by_invitation_id(session, invitation.id)
        if org_invite:
            org_invite.confirmed = True

            role = OrganizationRole.get_or_create(
                session,
                user=invitation.invited_user,
                organization=org_invite.organization,
                role=org_invite.role,
            )

            session.commit()
