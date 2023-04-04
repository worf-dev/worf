from worf.tests.fixtures.users import user as user_fixture
from worf.models import LoginProvider
from worf.settings import settings


def github_user(
    test, fixtures, email="test@testgoogle.com", github_id=None, scopes=None
):
    if github_id is None:
        github_id = settings.get("github.user_response_data.id")

    user = user_fixture(test, fixtures, email=email, superuser=False, scopes=scopes)

    provider = LoginProvider(user_id=user.id, provider_id=github_id, provider="github")

    test.session.add(provider)
    test.session.commit()
    user.provider = provider

    return user
