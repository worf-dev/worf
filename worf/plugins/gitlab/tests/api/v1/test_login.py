from worf.tests.helpers import ApiTest
from worf.settings import settings
from ...fixtures import gitlab_user
import requests


class TestLogin(ApiTest):
    fixtures = [{"gitlab_user": gitlab_user}]

    def test_google_login(self):
        response = requests.post(
            self.url("/login/gitlab"),
            json={
                "code": "1234",
                "state": "foo",
                "redirect_uri": "http://localhost:8080/login/gitlab",
            },
        )

        assert response.status_code == 201
        data = response.json()
        assert "access_token" in data

        # providing wrong credentials should not log in the user
        response = requests.post(
            self.url("/login/gitlab"),
            json={
                "code": "abcd",
                "state": "foo",
                "redirect_uri": "http://localhost:5000/login/gitlab",
            },
        )
        assert response.status_code == 403
