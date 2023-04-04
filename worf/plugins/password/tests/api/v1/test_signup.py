from worf.tests.helpers import ApiTest
from worf.models import User, AccessToken
from worf.settings import settings
import requests
import re

invalid_params = [
    {
        "data": {"email": "not-an-email", "password": "12345678", "language": "en"},
        "errors": set(["email"]),
    },
    {
        "data": {"email": "max@muster.de", "password": "1234567", "language": "en"},
        "errors": set(["password"]),
    },
    {
        "data": {"email": "max@muster", "password": "1234567", "language": "en"},
        "errors": set(["password", "email"]),
    },
]


class TestSignup(ApiTest):
    @classmethod
    def setUpClass(cls):
        cls._orig_notify_value = settings.get("api.signup.notify-email")
        cls._orig_approve_value = settings.get("api.signup.approve")
        settings.set("api.signup.notify-email", False)
        settings.set("api.signup.approve", False)
        super().setUpClass()

    @classmethod
    def tearDownClass(cls):
        settings.set("api.signup.approve", cls._orig_approve_value)
        settings.set("api.signup.notify-email", cls._orig_notify_value)
        super().tearDownClass()

    def test_valid_signup(self):
        """
        Check the valid signup flow
        """
        response = requests.post(
            self.url("/signup/password"),
            json={
                "email": "max@mustermann.de",
                "password": "mustergueltig",
                "display_name": "max-muster",
                "language": "en",
            },
        )
        assert response.status_code == 200
        data = response.json()

        email = self.test_queue.get(True, timeout=2.0)
        assert email["type"] == "email"
        message = email["data"]

        for part in message.walk():
            text = part.get_payload(decode=True)
            if not text:
                continue
            # make sure the code is included in the e-mail
            code_match = re.match(
                r".*?confirm-signup\#code=([^\=\&\n\s]+)",
                text.decode("utf-8"),
                re.DOTALL,
            )
            assert code_match

        code = code_match.group(1)
        response = requests.get(self.url("/confirm-signup?code={}".format(code)))

        assert response.status_code == 201
        data = response.json()

        # make sure a notification is sent out about the account creation
        email = self.test_queue.get(True, timeout=2.0)
        assert email["type"] == "email"

        # access token can be passed via X-Authorization header
        assert "access_token" in data

        headers = {"X-Authorization": "bearer {}".format(data["access_token"]["token"])}

        response = requests.get(self.url("/user"), headers=headers)
        assert response.status_code == 200

        profile = response.json()["user"]

        response = requests.post(
            self.url("/login/password"),
            json={"email": "max@mustermann.de", "password": "mustergueltig"},
        )

        assert response.status_code == 201

    def test_invalid_signup(self):
        """
        Check catching of various forms of invalid data
        """
        for params in invalid_params:
            response = requests.post(self.url("/signup/password"), json=params["data"])
            print(params["data"], response.status_code)
            assert response.status_code == 400
            data = response.json()
            assert "errors" in data
            for field in params["errors"]:
                assert field in data["errors"]

    def test_availability_check(self):
        """
        Check the availability checks (e-mail)
        """
        user = User(email="max@mustermann.de", display_name="max-muster")
        self.session.add(user)
        self.session.commit()

        response = requests.post(
            self.url("/signup/password"),
            json={
                "email": "max@mustermann.de",
                "password": "mustergueltig",
                "language": "en",
            },
        )

        assert response.status_code == 400
