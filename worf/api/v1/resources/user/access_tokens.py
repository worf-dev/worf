from ...forms.access_token import AccessTokenForm
from ....decorators.user import authorized
from worf.settings import settings
from worf.models import AccessToken, User
from worf.api.resource import Resource
from ....decorators.uuid import valid_uuid

import datetime
import re

from flask import request
from sqlalchemy.sql import and_, or_, desc


class AccessTokenScopes(Resource):
    @authorized(scopes=("admin",))
    def get(self):
        superuser_scopes = set(settings.get("api.superuser_access_token_scopes").keys())
        return (
            {
                "scopes": {
                    name: description
                    for name, description in settings.get(
                        "api.access_token_scopes"
                    ).items()
                    if not name in superuser_scopes or request.user.superuser
                }
            },
            200,
        )


class SuperUserAccessTokens(Resource):

    """
    Allows a superuser to retrieve a list of access tokens for a given user
    and create a new access token at will, which is useful e.g. for maintenance.
    """

    @authorized(superuser=True, scopes=("admin",))
    @valid_uuid(field="user_id")
    def get(self, user_id):
        with settings.session() as session:
            user = User.get_by_ext_id(session, user_id)

            if user is None:
                return {"message": self.t("not-found")}, 404

            access_tokens = (
                session.query(AccessToken)
                .filter(
                    and_(
                        AccessToken.user_id == user.id,
                        AccessToken.valid == True,
                        or_(
                            AccessToken.valid_until == None,
                            AccessToken.valid_until >= datetime.datetime.utcnow(),
                        ),
                    )
                )
                .order_by(desc(AccessToken.created_at))
            )
            return (
                {
                    "access_tokens": [
                        access_token.export() for access_token in access_tokens
                    ]
                },
                200,
            )

    @authorized(superuser=True, scopes=("admin",))
    @valid_uuid(field="user_id")
    def post(self, user_id):
        form = AccessTokenForm(request.get_json(), superuser=True)

        with settings.session() as session:
            user = User.get_by_ext_id(session, user_id)

            if user is None:
                return {"message": self.t("not-found")}, 404

            if not form.validate():
                return {"message": self.t("invalid-data"), "errors": form.errors}, 400

            access_token = AccessToken(
                valid_until=form.valid_data["valid_until"],
                description=form.valid_data["description"],
            )

            access_token.scopes = ",".join([v for v in form.valid_data["scopes"] if v])

            access_token.user = user
            access_token.valid = True
            access_token.last_used_at = datetime.datetime.utcnow()
            access_token.last_used_from = request.headers.get(
                "X-Real-IP", request.remote_addr
            )
            access_token.renews_when_used = True
            access_token.is_api_token = True

            access_token.valid_until = datetime.datetime.utcnow() + datetime.timedelta(
                minutes=60
            )  # superuser-created access tokens are only valid for 60 minutes...

            session.add(access_token)
            # we explicitly commit it here as we export it...
            session.commit()

            return (
                {
                    "message": self.t("success"),
                    "access_token": access_token.export(with_token=True),
                },
                201,
            )


class UserAccessTokens(Resource):
    @authorized(scopes=("admin",))
    def get(self):
        with settings.session() as session:
            access_tokens = (
                session.query(AccessToken)
                .filter(
                    and_(
                        AccessToken.user_id == request.user.id,
                        AccessToken.valid == True,
                        or_(
                            AccessToken.valid_until == None,
                            AccessToken.valid_until >= datetime.datetime.utcnow(),
                        ),
                    )
                )
                .order_by(desc(AccessToken.created_at))
            )
            return (
                {
                    "access_tokens": [
                        access_token.export() for access_token in access_tokens
                    ]
                },
                200,
            )

    @authorized(scopes=("admin",))
    def post(self):
        form = AccessTokenForm(request.get_json(), superuser=request.user.superuser)

        with settings.session() as session:
            if not form.validate():
                return {"message": self.t("invalid-data"), "errors": form.errors}, 400

            access_tokens_count = (
                session.query(AccessToken)
                .filter(
                    and_(
                        AccessToken.user_id == request.user.id,
                        AccessToken.valid == True,
                        or_(
                            AccessToken.valid_until == None,
                            AccessToken.valid_until >= datetime.datetime.utcnow(),
                        ),
                    )
                )
                .count()
            )

            max_access_tokens = settings.get("api.max_access_tokens", 100)
            if access_tokens_count > max_access_tokens:
                return (
                    {"message": self.t("access-tokens.too-many", max_access_tokens)},
                    400,
                )

            access_token = AccessToken(
                valid_until=form.valid_data["valid_until"],
                description=form.valid_data["description"],
            )

            access_token.scopes = ",".join([v for v in form.valid_data["scopes"] if v])

            access_token.user = request.user
            access_token.valid = True
            access_token.last_used_at = datetime.datetime.utcnow()
            access_token.last_used_from = request.headers.get(
                "X-Real-IP", request.remote_addr
            )
            access_token.renews_when_used = False
            access_token.is_api_token = True
            session.add(access_token)
            # we explicitly commit it here as we export it...
            session.commit()

            return (
                {
                    "message": self.t("success"),
                    "access_token": access_token.export(with_token=True),
                },
                201,
            )

    @authorized(scopes=("admin",))
    @valid_uuid(field="access_token_id")
    def delete(self, access_token_id):
        with settings.session() as session:
            filters = [AccessToken.ext_id == access_token_id]
            # a superuser can delete any access token
            if not request.user.superuser:
                filters.append(AccessToken.user_id == request.user.id)
            access_token = (
                session.query(AccessToken).filter(and_(*filters)).one_or_none()
            )

            if access_token is None:
                return {"message": self.t("not-found")}, 404

            if access_token == request.access_token:
                return (
                    {"message": self.t("access-tokens.cannot-delete-current-token")},
                    404,
                )

            # instead of deleting the access token, we make it invalid
            access_token.valid = False
            access_token.valid_until = datetime.datetime.utcnow() - datetime.timedelta(
                minutes=1
            )

            return {"message": self.t("success")}, 200
