from worf.tests.helpers import ApiTest
from worf.models import User, AccessToken, SignupRequest, Invitation
from worf.settings import settings
from worf.tests.fixtures import super_user, normal_user
import requests
import queue
import re


class TestInvitations(ApiTest):
    fixtures = [{"super_user": super_user}, {"normal_user": normal_user}]

    @classmethod
    def setUpClass(cls):
        cls._orig_value = settings.get("api.signup.approve")
        settings.set("api.signup.approve", True)
        super().setUpClass()

    @classmethod
    def tearDownClass(cls):
        super().tearDownClass()
        settings.set("api.signup.approve", cls._orig_value)

    def test_get_invitations(self):
        response = self.authenticated_get(user=self.normal_user, url="/invitations")
        assert response.status_code == 403

        response = self.authenticated_get(user=self.super_user, url="/invitations")
        assert response.status_code == 200

    def test_create_invitation(self):
        invitation_data = {
            "email": "max.meier@mustermann.de",
            "message": "Hi Max, can you sign up for this please?",
        }

        response = self.authenticated_post(
            user=self.normal_user, url="/invitations", json=invitation_data
        )
        assert response.status_code == 403

        response = self.authenticated_post(
            user=self.super_user, url="/invitations", json=invitation_data
        )
        assert response.status_code == 201
        data = response.json()

        email = self.test_queue.get(True, timeout=2.0)

        assert email["type"] == "email"
        message = email["data"]

        invitation = (
            self.session.query(Invitation)
            .filter(Invitation.email == invitation_data["email"])
            .one()
        )

        for part in message.walk():
            text = part.get_payload(decode=True)
            if not text:
                continue
            # make sure the code is included in the e-mail
            code_match = re.match(
                r".*?signup\#invitation=([^\=\&\n\s\"]+)",
                text.decode("utf-8"),
                re.DOTALL,
            )
            assert code_match
            assert code_match.group(1) == invitation.token

        user_data = {
            "email": invitation_data["email"],
            "password": "test1234",
            "language": "en",
        }

        # without the invitation the user should need to wait for approval
        response = requests.post(self.url("/signup/password"), json=user_data)
        assert response.status_code == 202

        user_data["invitation"] = invitation.token
        user_data["email"] += "e"

        response = requests.post(self.url("/signup/password"), json=user_data)
        assert response.status_code == 200

        # using the invitation should only work once
        user_data["email"] += "f"
        response = requests.post(self.url("/signup/password"), json=user_data)
        assert response.status_code == 400
