from worf.settings import settings
from worf.models import User, AccessToken, LoginProvider
from worf.api.resource import Resource
from worf.api.exc import LoginError
from ....decorators.user import authorized
from .profile import UserProfile

from sqlalchemy.orm.exc import NoResultFound, MultipleResultsFound

from flask import request, url_for

import traceback
import datetime
import logging

logger = logging.getLogger(__name__)


def generate_access_token(user, session, trusted=False):
    access_token = AccessToken(
        user_id=user.id,
        renews_when_used=True,
        scopes=",".join(settings.get("api.access_token_default_scopes", ["admin"])),
    )
    access_token.description = "Login from IP {} with user agent {}".format(
        request.anon_ip, request.headers.get("User-Agent", "(unknown user agent)")
    )

    if not trusted:
        minutes = settings.get("api.access_token_short_validity_minutes", 30)
        access_token.valid_until = datetime.datetime.utcnow() + datetime.timedelta(
            minutes=minutes
        )
        access_token.default_expiration_minutes = minutes
    else:
        validity_days = settings.get("api.access_token_long_validity_days", 7)
        if validity_days:
            access_token.valid_until = datetime.datetime.utcnow() + datetime.timedelta(
                days=validity_days
            )
            access_token.default_expiration_minutes = validity_days * 24 * 60
    session.add(access_token)
    session.commit()
    return access_token


def generate_and_return_token(user, provider, session, trusted=False, extra_data=None):
    access_token = generate_access_token(user, session, trusted=trusted)
    access_token.set_data("provider", provider)
    if extra_data:
        access_token.set_data("login", extra_data)
    logger.info(
        "Successful login attempt from user {} and IP {}.".format(
            user.id, request.anon_ip
        )
    )

    return (UserProfile.profile(user, access_token, with_token=True), 201)


class Login(Resource):
    @authorized(scopes=("admin",))
    def get(self):
        with settings.session() as session:
            providers = (
                session.query(LoginProvider)
                .filter(LoginProvider.user == request.user)
                .all()
            )
            return {"providers": [provider.export() for provider in providers]}, 200

    @authorized(scopes=("admin",))
    def delete(self, provider_id):
        with settings.session() as session:
            provider = (
                session.query(LoginProvider)
                .filter(
                    LoginProvider.user == request.user,
                    LoginProvider.ext_id == provider_id,
                )
                .one_or_none()
            )

            if not provider:
                return {"message": "not found"}, 404

            remaining_providers = (
                session.query(LoginProvider)
                .filter(LoginProvider.user == request.user)
                .count()
            )

            if remaining_providers == 1:
                return {"message": "cannot delete last login provider"}, 400

            session.delete(provider)
            session.commit()
            return {"message": "success"}, 200

    @authorized(scopes=("admin",), anon_ok=True)
    def post(self, provider_name):
        """
        Login workflow:

        * Retrieve the provider for the login
        * Let it validate the data
        * Let it retrieve the user
        * Let is log in the user

        We also allow this endpoint to be called for a logged-in user. In that
        case, the provider can associate a third-party account with the logged
        in user, which is useful e.g. for adding a third-party login provider.
        """
        data = request.get_json() or {}
        trusted = data.get("trusted")
        extra_data = data.get("extra_data")
        with settings.session() as session:
            provider = settings.providers.get("login.{}".format(provider_name))
            if not provider:
                return {"message": self.t("login.invalid-provider")}, 400

            provider = provider[0](session, self)

            if request.user:
                result = provider.associate(data, request.user)
            else:
                result = provider.login(data)

            if result.get("error"):
                return result["error"], result.get("status", 403)

            if request.user:
                return {"message": "success"}, 200

            return generate_and_return_token(
                result["user"],
                provider_name,
                session,
                trusted=trusted,
                extra_data=extra_data,
            )
