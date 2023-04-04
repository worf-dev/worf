from worf.tests.helpers import ApiTest
from worf.models import User, AccessToken
from worf.settings import settings
from ...fixtures import super_user, normal_user
import requests


class TestPasswordChange(ApiTest):

    """
    Test the password change flow
    """

    fixtures = [{"normal_user": normal_user}]

    def test_wrong_password(self):
        response = self.authenticated_post(
            user=self.normal_user,
            url="/password/change",
            json={
                "current_password": self.normal_user.cleartext_password + "foo",
                "password": "this-is-a-good-password",
            },
        )
        assert response.status_code == 400

    def test_invalid_new_password(self):
        response = self.authenticated_post(
            user=self.normal_user,
            url="/password/change",
            json={
                "current_password": self.normal_user.cleartext_password,
                "password": "short",
            },
        )

        assert response.status_code == 400

    def test_correct_workflow(self):
        new_password = "this-is-a-good-password"
        response = self.authenticated_post(
            user=self.normal_user,
            url="/password/change",
            json={
                "current_password": self.normal_user.cleartext_password,
                "password": new_password,
            },
        )
        assert response.status_code == 200

        # we make sure the new password actually works
        response = requests.post(
            self.url("/login/password"),
            json={"email": self.normal_user.email, "password": new_password},
        )

        assert response.status_code == 201
