from ...forms.signup import SignupForm
from worf.settings import settings
from ....decorators.user import authorized
from ....decorators.uuid import valid_uuid
from worf.models import (
    User,
    AccessToken,
    EMailRequest,
    SignupRequest as SignupRequestModel,
    CryptoToken,
    Invitation,
)
from worf.api.resource import Resource
from worf.api.exc import LoginError

from .login import generate_and_return_token
from worf.utils.email import send_email, jinja_email

from flask import request
import datetime
import logging
from sqlalchemy.sql import desc

logger = logging.getLogger(__name__)

### JINJA TASKS ###


@settings.register_task
def send_request_email(email, language):
    message = jinja_email(
        "email/signup-requested.multipart", {}, version="v1", language=language
    )
    send_email(to=email, subject=message.subject, text=message.text, html=message.html)


@settings.register_task
def send_confirm_email(data, language):
    encrypted_data = settings.encrypt(data).decode("ascii")
    context = {
        "code": encrypted_data,
        "block_code": EMailRequest.generate_encrypted_block_code(
            settings, "signup", data["email"]
        ),
    }
    message = jinja_email(
        "email/confirm-signup.multipart", context, version="v1", language=language
    )
    send_email(
        to=data["email"], subject=message.subject, text=message.text, html=message.html
    )


@settings.register_task
def send_welcome_email(email, language):
    message = jinja_email(
        "email/signup-complete.multipart", {}, version="v1", language=language
    )
    send_email(to=email, subject=message.subject, text=message.text, html=message.html)


### JINJA TASKS ###

### HELPER FUNCTIONS ###


def get_provider(name, session, resource):
    providers = settings.providers.get("signup.{}".format(name))
    if not providers:
        return None
    return providers[0](session, resource)


def confirm_signup(data):
    settings.delay(send_confirm_email, data=data, language=data["language"])
    return {"message": "please confirm"}, 200


def create_signup_request(session, resource, data):
    signup_request = SignupRequestModel.get_or_create(
        session, settings.salted_hash(data["email"])
    )
    signup_request.encrypted_data = data
    session.commit()

    notify_email = settings.get("api.signup.notify-email")
    if notify_email:
        settings.delay(send_request_email, email=notify_email, language="en")

    return {"message": "approval pending"}, 202


def finalize(session, resource, data, generate_token=True):
    provider_name = data.get("provider", "password")

    provider = get_provider(provider_name, session, resource)
    if not provider:
        return {"message": "invalid provider"}, 404

    if User.get_by_email(session, data["email"]):
        return {"message": resource.t("signup.email-already-taken")}, 400

    user = User(email=data["email"], language=data.get("language"))

    extra_data = data.get("extra_data")
    # we store the signup data in the user object for future reference
    # we also include it in the access token below
    if extra_data:
        user.set_data("signup", extra_data)

    session.add(user)
    session.commit()

    result = provider.finalize(user, data)

    if result.get("error"):
        session.delete(user)
        session.commit()
        return result["error"], result.get("status", 400)

    if data.get("invitation"):
        invitation = Invitation.get_by_token(session, data["invitation"])
        if invitation:
            invitation.invited_user = user
        invite_hooks = settings.hooks.get("invitation.confirm")
        for ih_f in invite_hooks:
            try:
                ih_f(invitation)
            except BaseException as be:
                logger.error(
                    f"Error running 'invitation.confirm' hook {ih_f.__module__}.{ih_f.__name__}:"
                )
                logger.error(be)

    settings.delay(send_welcome_email, email=user.email, language=user.language)

    if not generate_token:
        return {"message": "success"}, 200

    return generate_and_return_token(
        user, provider_name, session, trusted=data.get("trusted"), extra_data=extra_data
    )


### HELPER FUNCTIONS ###


class ConfirmSignup(Resource):
    def get(self):
        code = request.args.get("code")
        if not code:
            return {"message": "code missing"}, 400
        try:
            data = settings.decrypt(code.encode("ascii"), ttl=60 * 60 * 24)
        except:
            return {"message": "invalid / expired code"}, 400

        hash = CryptoToken.get_hash(code)

        with settings.session() as session:
            token = CryptoToken.get_or_create(session, hash)
            if token.used:
                return {"message": self.t("signup.token-already-used")}, 200
            token.used = True
            return finalize(session, self, data)


class SignupRequests(Resource):
    def _handle_request(self, request_id, confirm):
        with settings.session() as session:
            request = SignupRequestModel.get_by_ext_id(session, request_id)
            if request is None:
                return {"message": self.t("not-found")}, 404
            data = request.encrypted_data
            session.delete(request)
            if confirm:
                if data.get("email_verified"):
                    return finalize(session, self, data, generate_token=False)
                return confirm_signup(data)
        return {"message": self.t("success")}, 200

    @authorized(scopes=("admin",), superuser=True)
    def get(self):
        with settings.session() as session:
            requests = (
                session.query(SignupRequestModel)
                .order_by(desc(SignupRequestModel.created_at))
                .all()
            )
            return {"requests": [request.export() for request in requests]}, 200

    @authorized(scopes=("admin",), superuser=True)
    @valid_uuid(field="request_id")
    def post(self, request_id):
        return self._handle_request(request_id, True)

    @authorized(scopes=("admin",), superuser=True)
    @valid_uuid(field="request_id")
    def delete(self, request_id):
        return self._handle_request(request_id, False)


class Signup(Resource):
    def post(self, provider_name):
        data = request.get_json() or {}
        approve = settings.get("api.signup.approve")

        with settings.session() as session:
            form = SignupForm(data)

            if not form.validate():
                return {"message": self.t("invalid-data"), "errors": form.errors}, 400

            provider = get_provider(provider_name, session, self)
            if not provider:
                return {"message": "invalid provider"}, 404

            result = provider.validate(data)

            if result.get("error"):
                return result["error"], result.get("status", 400)

            data = form.valid_data
            data["provider"] = provider_name
            data.update(result["data"])

            if User.get_by_email(session, data["email"]):
                return {"message": self.t("signup.email-already-taken")}, 400

            if data.get("invitation"):
                invitation = Invitation.get_by_token(session, data["invitation"])
                if invitation:
                    if not invitation.valid:
                        return {"message": "invitation is invalid"}, 400
                    invitation.valid = False
                    invitation.accepted_at = datetime.datetime.utcnow()
                    approve = False

            if approve:
                return create_signup_request(session, self, data)

            if result["data"].get("email_verified"):
                return finalize(session, self, data)

            return confirm_signup(data)
