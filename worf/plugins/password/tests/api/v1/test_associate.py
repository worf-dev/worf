from worf.tests.helpers import ApiTest
from worf.models import User
from worf.settings import settings
from worf.tests.fixtures.users import normal_user

import requests


class TestAssociate(ApiTest):
    fixtures = [{"normal_user": normal_user}]

    def test_associate(self):
        data = {"password": "test1234"}

        response = self.authenticated_post(
            self.normal_user, "/login/password", json=data
        )

        assert response.status_code == 200

        response = requests.post(
            self.url("/login/password"),
            json={"email": self.normal_user.email, "password": data["password"]},
        )

        assert response.status_code == 201

        new_data = {"password": "1234test"}

        # we should be able to associate more than one password with a user
        # account (e.g. useful for application passwords)
        response = self.authenticated_post(
            self.normal_user, "/login/password", json=new_data
        )

        assert response.status_code == 200

        for d in (data, new_data):
            response = requests.post(
                self.url("/login/password"),
                json={"email": self.normal_user.email, "password": d["password"]},
            )
            assert response.status_code == 201
