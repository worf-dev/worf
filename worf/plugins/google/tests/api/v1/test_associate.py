from worf.tests.fixtures.users import normal_user
from worf.tests.helpers import ApiTest
from worf.settings import settings
import requests


class TestAssociate(ApiTest):
    fixtures = [{"normal_user": normal_user}]

    def test_association(self):
        response = self.authenticated_post(
            self.normal_user,
            "/login/google",
            json={"id_token": "1234", "language": "en"},
        )

        assert response.status_code == 200
        data = response.json()

        response = requests.post(self.url("/login/google"), json={"id_token": "1234"})

        assert response.status_code == 201
