from worf.tests.helpers import ApiTest
from worf.models import User, AccessToken
from worf.settings import settings
from worf.tests.fixtures import super_user, normal_user
import requests


class TestEMailVerification(ApiTest):
    fixtures = [{"normal_user": normal_user}]

    def test_email_change(self):
        """
        Check e-mail change flow
        """
        self.session.add(self.normal_user)

        response = self.authenticated_post(
            url="/change-email",
            user=self.normal_user,
            json={"email": "foomanchu@usa.gov"},
        )
        assert response.status_code == 200

        self.session.refresh(self.normal_user)
        assert self.normal_user.email_change_code is not None

        email = self.test_queue.get(True, timeout=2.0)
        assert email["type"] == "email"

        message = email["data"]
        assert message["from"] == settings.get("smtp.from")
        assert message["to"] == self.normal_user.new_email

        for part in message.walk():
            text = part.get_payload(decode=True)
            if not text:
                continue
            # make sure the code is included in the e-mail
            assert text.decode("utf-8").find(self.normal_user.email_change_code) != -1

        # unauthenticated requests should not work
        response = requests.put(
            self.url("/change-email"), json={"code": self.normal_user.email_change_code}
        )

        assert response.status_code == 401

        # the wrong code should not work
        response = self.authenticated_put(
            url="/change-email",
            user=self.normal_user,
            json={"code": "1234567890123456"},
        )

        assert response.status_code == 404

        old_email = self.normal_user.email

        # with an authorized user and the correct code it should work
        response = self.authenticated_put(
            url="/change-email",
            user=self.normal_user,
            json={"code": self.normal_user.email_change_code},
        )

        assert response.status_code == 200

        # make sure a notification is sent out about the email change
        email = self.test_queue.get(True, timeout=2.0)
        assert email["type"] == "email"
        message = email["data"]
        # make sure it goes to the OLD address
        assert message["To"] == old_email

        # the code shouldn't be usable more than once
        response = self.authenticated_put(
            url="/change-email",
            user=self.normal_user,
            json={"code": self.normal_user.email_change_code},
        )

        assert response.status_code == 404
