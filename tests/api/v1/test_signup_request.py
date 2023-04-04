from worf.tests.helpers import ApiTest
from worf.models import User, AccessToken, SignupRequest
from worf.settings import settings
from worf.tests.fixtures import super_user, normal_user
import requests
import queue
import re


class TestSignupRequests(ApiTest):
    fixtures = [{"super_user": super_user}, {"normal_user": normal_user}]

    @classmethod
    def setUpClass(cls):
        cls._orig_value = settings.get("api.signup.approve")
        settings.set("api.signup.approve", True)
        settings.set("api.signup.notify-email", False)
        super().setUpClass()

    @classmethod
    def tearDownClass(cls):
        super().tearDownClass()
        settings.set("api.signup.approve", cls._orig_value)

    def test_list_requests(self):
        response = self.authenticated_get(url="/signup-requests", user=self.normal_user)
        assert response.status_code == 403

        response = self.authenticated_get(url="/signup-requests", user=self.super_user)
        assert response.status_code == 200

    def test_confirm_request(self):
        """
        Check the valid signup flow
        """
        user_data = {"email": "max@mustermann.de", "language": "en"}

        request = SignupRequest(
            encrypted_data=user_data,
            email_hash=settings.salted_hash(user_data["email"]),
        )
        self.session.add(request)
        self.session.commit()

        response = self.authenticated_post(
            url="/signup-requests/{}".format(request.ext_id), user=self.super_user
        )
        assert response.status_code == 200

        email = self.test_queue.get(True, timeout=1.0)
        assert email

        assert self.session.query(SignupRequest).count() == 0

    def test_delete_request(self):
        """
        Check the valid signup flow

        """
        user_data = {"email": "max@mustermann-2.de", "language": "en", "trusted": ""}

        request = SignupRequest(encrypted_data=user_data)
        self.session.add(request)
        self.session.commit()

        response = self.authenticated_delete(
            url="/signup-requests/{}".format(request.ext_id), user=self.super_user
        )
        assert response.status_code == 200

        with self.assertRaises(queue.Empty):
            email = self.test_queue.get(True, timeout=1.0)

        assert self.session.query(SignupRequest).count() == 0
