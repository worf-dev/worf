from worf.tests.helpers import ApiTest
from worf.models import User, AccessToken
from worf.settings import settings
from ...fixtures import super_user, normal_user
import requests


class TestPasswordReset(ApiTest):

    """
    Test the password reset flow
    """

    fixtures = [{"normal_user": normal_user}]

    def test_correct_workflow(self):
        new_password = "this-is-a-good-password"
        response = self.authenticated_post(
            user=self.normal_user,
            url="/password/reset",
            json={"email": self.normal_user.email},
        )

        assert response.status_code == 200

        email = self.test_queue.get(True, timeout=2.0)
        assert email["type"] == "email"

        message = email["data"]
        assert message["to"] == self.normal_user.email

        # we refresh the provider data
        self.session.refresh(self.normal_user.provider)

        password_reset_code = self.normal_user.provider.data["password_reset_code"]

        for part in message.walk():
            text = part.get_payload(decode=True)
            if not text:
                continue

            # make sure the code is included in the e-mail
            assert text.decode("utf-8").find(password_reset_code) != -1
            assert text.decode("utf-8").find(str(self.normal_user.ext_id)) != -1

        # providing the code and a new password should reset it
        response = requests.put(
            self.url("/password/reset"),
            json={
                "code": password_reset_code,
                "id": str(self.normal_user.ext_id),
                "password": "new-password",
            },
        )

        assert response.status_code == 200

        # a given code should only work once
        response = requests.put(
            self.url("/password/reset"),
            json={
                "code": password_reset_code,
                "id": str(self.normal_user.ext_id),
                "password": "new-password",
            },
        )

        assert response.status_code == 404

        response = requests.post(
            self.url("/login/password"),
            json={"email": self.normal_user.email, "password": "new-password"},
        )

        assert response.status_code == 201
