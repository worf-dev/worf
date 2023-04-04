from worf.tests.fixtures.users import user as user_fixture
from worf.models import LoginProvider
from worf.settings import settings


def gitlab_user(
    test, fixtures, email="test@testgoogle.com", gitlab_id=None, scopes=None
):
    if gitlab_id is None:
        gitlab_id = settings.get("gitlab.user_response_data.id")

    user = user_fixture(test, fixtures, email=email, superuser=False, scopes=scopes)

    provider = LoginProvider(user_id=user.id, provider_id=gitlab_id, provider="gitlab")

    test.session.add(provider)
    test.session.commit()
    user.provider = provider

    return user
