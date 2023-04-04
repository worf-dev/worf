from worf.tests.helpers import ApiTest
from worf.settings import settings
import requests


class TestSignup(ApiTest):
    def test_valid_signup(self):
        response = requests.post(
            self.url("/signup/gitlab"),
            json={
                "code": "1234",
                "state": "foo",
                "language": "en",
                "redirect_uri": "http://localhost:8080/signup/gitlab",
            },
        )

        assert response.status_code == 201
        data = response.json()
        assert "access_token" in data

        response = requests.post(
            self.url("/login/gitlab"),
            json={
                "code": "1234",
                "state": "foo",
                "redirect_uri": "http://localhost:8080/signup/gitlab",
            },
        )

        assert response.status_code == 201

    def test_invalid_signup(self):
        response = requests.post(
            self.url("/signup/gitlab"),
            json={
                "code": "abcd",
                "state": "foo",
                "language": "en",
                "redirect_uri": "http://localhost:8080/signup/gitlab",
            },
        )

        assert response.status_code == 400
