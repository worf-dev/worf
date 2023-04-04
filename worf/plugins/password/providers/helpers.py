from worf.models import LoginProvider
from passlib.context import CryptContext

import uuid


def get_pwd_context():
    return CryptContext(
        schemes=["pbkdf2_sha512"],
        default="pbkdf2_sha512",
        pbkdf2_sha512__default_rounds=150000,
    )


def generate_password():
    return "".join(
        random.choice(string.ascii_uppercase + string.ascii_lowercase + string.digits)
        for _ in range(10)
    )


def create_provider(session, user, password):
    provider = LoginProvider.get_or_create(session, "password", user, uuid.uuid4().hex)

    provider.data = {
        "password": encrypt_password(password),
        "password_reset_code": None,
        "force_password_change": False,
    }

    return provider


def encrypt_password(password):
    pwd_context = get_pwd_context()
    return pwd_context.hash(password)


def check_password(password, reference):
    pwd_context = get_pwd_context()
    return pwd_context.verify(password, reference)
