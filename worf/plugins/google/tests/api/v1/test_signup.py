from worf.tests.helpers import ApiTest
from worf.settings import settings
import requests


class TestSignup(ApiTest):
    def test_valid_signup(self):
        response = requests.post(
            self.url("/signup/google"), json={"id_token": "1234", "language": "en"}
        )

        assert response.status_code == 201
        data = response.json()
        assert "access_token" in data

        response = requests.post(self.url("/login/google"), json={"id_token": "1234"})

        assert response.status_code == 201

    def test_invalid_signup(self):
        response = requests.post(
            self.url("/signup/google"), json={"id_token": "abcd", "language": "en"}
        )

        assert response.status_code == 400
