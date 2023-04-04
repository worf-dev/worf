from worf.tests.fixtures.users import user as user_fixture
from worf.models import LoginProvider


def google_user(
    test, fixtures, email="test@testgoogle.com", google_id="1234", scopes=None
):
    user = user_fixture(test, fixtures, email=email, superuser=False, scopes=scopes)

    provider = LoginProvider(user_id=user.id, provider_id=google_id, provider="google")

    test.session.add(provider)
    test.session.commit()
    user.provider = provider

    return user
