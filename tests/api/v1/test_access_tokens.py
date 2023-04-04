from worf.tests.helpers import ApiTest
from worf.models import User, AccessToken
from worf.settings import settings
from worf.tests.fixtures import super_user, access_token, normal_user
import requests


class TestAccessTokens(ApiTest):

    """
    Test the access token endpoints
    """

    fixtures = [
        {"normal_user": normal_user},
        {
            "access_token": lambda test, fixtures: access_token(
                test, fixtures, fixtures["normal_user"]
            )
        },
    ]

    @classmethod
    def tearDownClass(cls):
        settings.set("api.access_token_scopes.test:api", None)
        super().tearDownClass()

    @classmethod
    def setUpClass(cls):
        settings.set("api.access_token_scopes.test:api", "A Test API token")
        super().setUpClass()

    def test_get_access_tokens(self):
        response = self.authenticated_get(url="/access-tokens", user=self.normal_user)

        assert response.status_code == 200

        data = response.json()

        assert "access_tokens" in data
        assert len(data["access_tokens"]) == 2

    def test_create_access_token(self):
        response = self.authenticated_post(
            url="/access-tokens", json={"scopes": ["test:api"]}, user=self.normal_user
        )
        assert response.status_code == 201

        data = response.json()

        assert "access_token" in data

    def test_delete_access_token(self):
        response = self.authenticated_delete(
            url="/access-tokens/{}".format(self.access_token.ext_id),
            user=self.normal_user,
        )

        assert response.status_code == 200
