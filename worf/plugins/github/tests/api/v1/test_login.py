from worf.tests.helpers import ApiTest
from worf.settings import settings
from ...fixtures import github_user
import requests


class TestLogin(ApiTest):
    fixtures = [{"github_user": github_user}]

    def test_google_login(self):
        response = requests.post(
            self.url("/login/github"), json={"code": "1234", "state": "foo"}
        )

        assert response.status_code == 201
        data = response.json()
        assert "access_token" in data

        # providing wrong credentials should not log in the user
        response = requests.post(
            self.url("/login/github"), json={"code": "abcd", "state": "foo"}
        )
        assert response.status_code == 403
