from ...forms.invitation import InvitationForm
from worf.settings import settings
from ....decorators.user import authorized
from worf.models import Invitation, EMailRequest
from worf.api.resource import Resource

from worf.utils.email import send_email, jinja_email

from flask import request
from sqlalchemy.sql import desc


@settings.register_task
def send_invitation(data, language):
    context = {
        "token": data["token"],
        "email": data["inviting_user_email"],
        "message": data["message"],
        "block_code": EMailRequest.generate_encrypted_block_code(
            settings, "invitation", data["email"]
        ),
    }
    message = jinja_email(
        "email/invitation.multipart", context, version="v1", language=language
    )
    send_email(
        to=data["email"], subject=message.subject, text=message.text, html=message.html
    )


class Invitations(Resource):
    @authorized(scopes=("admin",), superuser=True)
    def get(self, invitation_id=None):
        with settings.session() as session:
            if invitation_id is not None:
                invitation = Invitation.get_by_ext_id(session, invitation_id)
                if invitation is None:
                    return {"message": self.t("not-found")}, 404
                return {"invitation": invitation.export()}, 200
            invitations = (
                session.query(Invitation).order_by(desc(Invitation.created_at)).all()
            )
            return (
                {"invitations": [invitation.export() for invitation in invitations]},
                200,
            )

    @authorized(scopes=("admin",), superuser=True)
    def delete(self, invitation_id):
        with settings.session() as session:
            invitation = Invitation.get_by_ext_id(session, invitation_id)
            if invitation is None:
                return {"message": self.t("not-found")}, 404
            session.delete(invitation)
        return {"message": self.t("success")}, 200

    @authorized(superuser=True, scopes=("admin",))
    def post(self):
        form = InvitationForm(request.get_json())

        if not form.validate():
            return {"message": "invalid data", "errors": form.errors}, 400

        invitation = Invitation()
        for key, value in form.valid_data.items():
            setattr(invitation, key, value)

        invitation.inviting_user_id = request.user.id

        with settings.session() as session:
            existing_invitation = Invitation.get_by_email(session, invitation.email)

            if existing_invitation:
                return {"message": self.t("invitations.already-exists")}, 400

            if not EMailRequest.request(session, "invitation", invitation.email):
                return {"message": self.t("cannot-send-email")}, 400

            session.add(invitation)
            session.commit()

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

            return {"invitation": invitation.export()}, 201
