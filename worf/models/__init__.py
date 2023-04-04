from .base import Base, DeclarativeBase
from .access_token import AccessToken
from .user import User
from .email_request import EMailRequest
from .signup_request import SignupRequest
from .crypto_token import CryptoToken
from .invitation import Invitation
from .login_provider import LoginProvider


def clean_db(session):
    for model in [
        AccessToken,
        EMailRequest,
        SignupRequest,
        CryptoToken,
        Invitation,
        LoginProvider,
        User,
    ]:
        session.query(model).delete()
