from worf.tests.helpers import ApiTest
from worf.settings import settings
from ...fixtures import google_user
import requests


class TestLogin(ApiTest):
    fixtures = [{"google_user": google_user}]

    def test_google_login(self):
        response = requests.post(self.url("/login/google"), json={"id_token": "1234"})

        assert response.status_code == 201
        data = response.json()
        assert "access_token" in data

        # providing wrong credentials should not log in the user
        response = requests.post(self.url("/login/google"), json={"id_token": "abcd"})
        assert response.status_code == 400
