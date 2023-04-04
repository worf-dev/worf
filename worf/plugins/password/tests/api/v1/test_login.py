from worf.tests.helpers import ApiTest
from worf.models import User, AccessToken
from worf.settings import settings
from ...fixtures import super_user, normal_user
import requests


class TestLogin(ApiTest):
    fixtures = [{"super_user": super_user}, {"normal_user": normal_user}]

    def test_login_logout(self):
        response = requests.post(
            self.url("/login/password"),
            json={
                "email": self.normal_user.email,
                "password": self.normal_user.cleartext_password,
            },
        )

        assert response.status_code == 201
        data = response.json()

        # access token can be passed via X-Authorization header
        assert "access_token" in data
        headers = {"X-Authorization": "bearer {}".format(data["access_token"]["token"])}

        response = requests.get(self.url("/user"), headers=headers)
        assert response.status_code == 200

        # it can also be passed in the Authorization header
        headers = {"Authorization": "bearer {}".format(data["access_token"]["token"])}

        response = requests.get(self.url("/user"), headers=headers)
        assert response.status_code == 200

        # Logging out via POST should erase the access token
        response = requests.post(self.url("/logout"), headers=headers)
        assert response.status_code == 200

        # this request should return a 401
        response = requests.get(self.url("/user"), headers=headers)
        assert response.status_code == 401

        # providing wrong credentials should not log in the user
        response = requests.post(
            self.url("/login/password"),
            json={
                "email": self.normal_user.email,
                "password": self.normal_user.cleartext_password + "foobar",
            },
        )
        assert response.status_code == 403
        data = response.json()

        response = requests.post(
            self.url("/login/password"),
            json={
                "email": self.normal_user.email + "foo",
                "password": self.normal_user.cleartext_password,
            },
        )
        assert response.status_code == 404
        new_data = response.json()

        # error message for wrong password vs. wrong username should be idential,
        # so that it's impossible to learn which usernames are valid by trying differnt ones.
        assert data["message"] == new_data["message"]

    def test_trust_computer(self):
        response_a = requests.post(
            self.url("/login/password"),
            json={
                "email": self.normal_user.email,
                "trusted": "1",
                "password": self.normal_user.cleartext_password,
            },
        )

        assert response_a.status_code == 201
        data_a = response_a.json()

        response_b = requests.post(
            self.url("/login/password"),
            json={
                "email": self.normal_user.email,
                "password": self.normal_user.cleartext_password,
            },
        )

        assert response_b.status_code == 201
        data_b = response_b.json()

        access_token_a = (
            self.session.query(AccessToken)
            .filter(AccessToken.token == data_a["access_token"]["token"])
            .one()
        )
        access_token_b = (
            self.session.query(AccessToken)
            .filter(AccessToken.token == data_b["access_token"]["token"])
            .one()
        )

        assert access_token_a.valid_until > access_token_b.valid_until
