from ....forms.password import (
    ChangePasswordForm,
    RequestPasswordResetForm,
    ResetPasswordForm,
)
from worf.api.decorators.user import authorized
from worf.settings import settings
from worf.models import User, EMailRequest, LoginProvider
from worf.api.resource import Resource
from worf.utils.email import send_email, jinja_email
from ....providers.helpers import check_password, encrypt_password

from flask import request
import datetime
import os

### CELERY TASKS ###


@settings.register_task
def send_password_reset_code(email, code, id, language):
    with settings.session() as session:
        context = {
            "code": code,
            "id": id,
            "block_code": EMailRequest.generate_encrypted_block_code(
                settings, "password-reset", email
            ),
        }
        message = jinja_email(
            "email/reset-password.multipart", context, version="v1", language=language
        )
        send_email(
            to=email, subject=message.subject, text=message.text, html=message.html
        )


@settings.register_task
def send_password_changed_notification(email, language):
    message = jinja_email(
        "email/password-changed.multipart", {}, version="v1", language=language
    )
    send_email(to=email, subject=message.subject, text=message.text, html=message.html)


### CELERY TASKS ###


def get_provider(session, user):
    return (
        session.query(LoginProvider)
        .filter(LoginProvider.provider == "password", LoginProvider.user == user)
        .one_or_none()
    )


class PasswordChange(Resource):
    @authorized(scopes=("admin",))
    def post(self):
        with settings.session() as session:
            form = ChangePasswordForm(request.get_json())
            if not form.validate():
                return {"message": self.t("invalid-data"), "errors": form.errors}, 400

            provider = get_provider(session, request.user)

            if not provider:
                return {"message": "no password set"}, 404
            current_password = provider.data["password"]

            if not check_password(
                form.valid_data["current_password"], current_password
            ):
                return (
                    {
                        "message": self.t("invalid-data"),
                        "errors": {
                            "current_password": self.t(
                                "password-change.invalid-current-password"
                            )
                        },
                    },
                    400,
                )
            provider.set_data("password", encrypt_password(form.valid_data["password"]))
            return {"message": self.t("success")}, 200


class PasswordReset(Resource):
    def put(self):
        """
        Reset the password with a code
        """
        with settings.session() as session:
            form = ResetPasswordForm(request.get_json())
            if not form.validate():
                return {"message": self.t("invalid-data"), "errors": form.errors}, 400
            user = (
                session.query(User)
                .filter(User.ext_id == form.valid_data["id"])
                .one_or_none()
            )
            if not user:
                return {"message": self.t("not-found")}, 404

            provider = get_provider(session, user)

            if not provider:
                return {"message": "no password set"}, 404

            password_reset_code = provider.data.get("password_reset_code")

            if password_reset_code != form.valid_data["code"]:
                return {"message": self.t("not-found")}, 404

            provider.set_data("password", encrypt_password(form.valid_data["password"]))
            provider.set_data("password_reset_code", None)
            session.commit()

            EMailRequest.reset(session, "password-reset", user.email)
            settings.delay(
                send_password_changed_notification,
                email=user.email,
                language=user.language,
            )

            return {"message": self.t("success")}, 200

    def post(self):
        """
        Request a password reset code
        """
        with settings.session() as session:
            form = RequestPasswordResetForm(request.get_json())
            if not form.validate():
                return {"message": self.t("invalid-data"), "errors": form.errors}, 400
            user = (
                session.query(User)
                .filter(User.email == form.valid_data["email"])
                .one_or_none()
            )

            if not user:
                return {"message": self.t("not-found")}, 404

            provider = get_provider(session, user)

            if not provider:
                return {"message": "no password set"}, 404

            if not EMailRequest.request(session, "password-reset", user.email):
                return {"message": self.t("cannot-send-email")}, 400

            code = os.urandom(16).hex()
            provider.set_data("password_reset_code", code)
            session.commit()

            settings.delay(
                send_password_reset_code,
                email=user.email,
                code=code,
                id=str(user.ext_id),
                language=user.language,
            )
            return {"message": self.t("password-reset.reset-email-sent")}, 200
