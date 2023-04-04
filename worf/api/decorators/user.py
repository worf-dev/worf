import datetime
import logging
import time
import re

from worf.settings import settings
from worf.models import AccessToken, User

from flask import request
from functools import wraps

from sqlalchemy.orm.exc import NoResultFound
from sqlalchemy.orm import joinedload
from sqlalchemy.sql import and_

logger = logging.getLogger(__name__)


def authorized(
    f=None, anon_ok=False, scopes=None, session_token=False, superuser=False
):
    """
    Ensures that the request originates from a valid user.
    """

    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            @wraps(f)
            def process_anonymously():
                request.user = None
                request.access_token = None
                return f(*args, **kwargs)

            access_token_key = None
            for header_name in ("Authorization", "X-Authorization"):
                if header_name not in request.headers:
                    continue
                authorization = request.headers[header_name]
                match = re.match(r"^Bearer\s+([\w\d]+)$", authorization, re.I)
                if not match:
                    continue
                access_token_key = match.group(1)
                break
            if access_token_key is None and session_token:
                access_token_key = request.cookies.get("access_token")

            if access_token_key is None:
                if anon_ok:
                    return process_anonymously()
                return {"message": "Authorization header not present / not valid"}, 401

            request.access_token_key = access_token_key
            invalid_response = (
                {"message": "Invalid / expired access token: %s" % access_token_key},
                401,
            )

            with settings.session() as session:
                try:
                    access_token = (
                        session.query(AccessToken)
                        .filter(
                            and_(
                                AccessToken.token == access_token_key,
                                AccessToken.valid == True,
                            )
                        )
                        .one()
                    )
                    user = (
                        session.query(User)
                        .filter(User.id == access_token.user_id)
                        .one()
                    )
                except NoResultFound:
                    if anon_ok:
                        return process_anonymously()
                    # redirect to login
                    return invalid_response

                if not access_token.valid:
                    return invalid_response

                if superuser and not user.superuser:
                    return (
                        {"message": "This endpoint requires super-user privileges."},
                        403,
                    )

                if scopes is not None:
                    access_token_scopes = access_token.scopes.split(",")
                    if access_token_scopes is None or (
                        not set(scopes).issubset(set(access_token_scopes))
                    ):
                        return (
                            {
                                "message": "You are not authorized to use this endpoint. Sorry!"
                            },
                            403,
                        )
                if (
                    access_token.valid_until
                    and access_token.valid_until < datetime.datetime.utcnow()
                ):
                    if anon_ok:
                        return process_anonymously()
                    return (
                        {
                            "message": "This access token has expired, please log in again to create a new one"
                        },
                        403,
                    )

                # if this access_token is stored in the staging DB, we update the last_used_at field.
                access_token.last_used_at = datetime.datetime.utcnow()
                access_token.last_used_from = request.headers.get(
                    "X-Client-IP",
                    request.headers.get("X-Originating-IP", request.remote_addr),
                )

                if (
                    access_token.renews_when_used
                    and access_token.default_expiration_minutes
                ):
                    access_token.valid_until = (
                        datetime.datetime.utcnow()
                        + datetime.timedelta(
                            minutes=access_token.default_expiration_minutes
                        )
                    )

                session.add(access_token)
                session.commit()

                request.session = session
                request.access_token = access_token
                request.user = user

                result = f(*args, **kwargs)
                return result

        return decorated_function

    if f:
        return decorator(f)
    else:
        return decorator
