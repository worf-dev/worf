from worf.models import User, AccessToken
from worf.settings import settings as settings


def user(test, fixtures, email, superuser=False, display_name=None, scopes=None):
    if scopes is None:
        scopes = settings.get("api.access_token_default_scopes", ["admin"])

    user = User(email=email, superuser=superuser, display_name=display_name)

    test.session.add(user)
    test.session.commit()

    user.access_token = AccessToken(user_id=user.id, scopes=",".join(scopes))

    test.session.add(user.access_token)
    test.session.commit()

    return user


def access_token(test, fixtures, user, scopes=["admin"]):
    access_token = AccessToken(user=user, scopes=",".join(scopes))
    test.session.add(access_token)
    test.session.commit()
    return access_token


def normal_user(test, fixtures, email="test@test.com", scopes=None):
    return user(test, fixtures, email=email, superuser=False, scopes=scopes)


def super_user(test, fixtures, email="super@super.com", scopes=None):
    return user(test, fixtures, email=email, superuser=True, scopes=scopes)


def internal_user(test, fixtures):
    return user(test, fixtures, email="internal@internal.com", superuser=False)
