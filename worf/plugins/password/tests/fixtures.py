from worf.tests.fixtures.users import user as user_fixture
from worf.plugins.password.providers.helpers import create_provider


def user_with_password(test, fixtures, password, *args, **kwargs):
    user = user_fixture(test, fixtures, *args, **kwargs)
    provider = create_provider(test.session, user, password)
    user.provider = provider
    test.session.commit()
    user.cleartext_password = password
    return user


def normal_user(
    test, fixtures, email="test@test.com", password="test1234", scopes=None
):
    return user_with_password(
        test, fixtures, password, email=email, superuser=False, scopes=scopes
    )


def super_user(
    test, fixtures, email="super@super.com", password="test1234", scopes=None
):
    return user_with_password(
        test, fixtures, password, email=email, superuser=True, scopes=scopes
    )
