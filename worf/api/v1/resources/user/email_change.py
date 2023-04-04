from ....decorators.user import authorized
from sqlalchemy.orm.exc import NoResultFound
from worf.settings import settings
from worf.models import User, EMailRequest
from worf.api.resource import Resource
from worf.utils.email import send_email, jinja_email
from ...forms.email_change import EMailChangeForm, EMailChangeRequestForm

from flask import request

import logging
import datetime
import os

logger = logging.getLogger(__name__)


@settings.register_task
def send_email_verification(user_id, update_code=True):
    with settings.session() as session:
        user = session.query(User).filter(User.id == user_id).one()
        if update_code:
            user.email_change_code = os.urandom(16).hex()
        context = {
            "code": user.email_change_code,
            "block_code": EMailRequest.generate_encrypted_block_code(
                settings, "email-change", user.new_email
            ),
        }
        message = jinja_email(
            "email/change-email.multipart",
            context,
            version="v1",
            language=user.language,
        )
        send_email(
            to=user.new_email,
            subject=message.subject,
            text=message.text,
            html=message.html,
        )


@settings.register_task
def send_email_changed_notification(email, language):
    message = jinja_email(
        "email/email-changed.multipart", {}, version="v1", language=language
    )
    send_email(to=email, subject=message.subject, text=message.text, html=message.html)


class EMailChange(Resource):
    @authorized(scopes=("admin",))
    def put(self):
        with settings.session() as session:
            form = EMailChangeForm(request.get_json())
            if not form.validate():
                return {"message": self.t("invalid-data"), "errors": form.errors}, 400
            if request.user.email_change_code == form.valid_data["code"]:
                request.user.email_change_code = None
                EMailRequest.reset(session, "email-change", request.user.new_email)
                if User.get_by_email(session, email=request.user.new_email) is not None:
                    return {"message": self.t("email-change.email-already-taken")}, 400
                # we send a notification to the old e-mail address
                settings.delay(
                    send_email_changed_notification,
                    email=request.user.email,
                    language=request.user.language,
                )
                request.user.email = request.user.new_email
                request.user.new_email = None
            else:
                return {"message": self.t("not-found")}, 404
        return {"message": self.t("success")}, 200

    @authorized(scopes=("admin",))
    def post(self):
        with settings.session() as session:
            form = EMailChangeRequestForm(request.get_json())
            if not form.validate():
                return {"message": self.t("invalid-data"), "errors": form.errors}, 400
            if User.get_by_email(session, email=form.valid_data["email"]) is not None:
                return {"message": self.t("email-change.email-already-taken")}, 400
            request.user.new_email = form.valid_data["email"]
            if not EMailRequest.request(
                session, "email-change", request.user.new_email
            ):
                return {"message": self.t("cannot-send-email")}, 400
            user_id = request.user.id
        settings.delay(send_email_verification, user_id=user_id, update_code=True)
        return {"message": self.t("email-change.verification-mail-sent")}, 200
