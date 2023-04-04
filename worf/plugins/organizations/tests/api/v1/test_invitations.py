from worf.api.v1.resources.user.signup import finalize
from worf.models import Invitation
from worf.settings import settings
from worf.tests.helpers import ApiTest
from worf.tests.fixtures import super_user, user
from ...fixtures import organization, organization_role
from ....models import OrganizationInvitation
from datetime import datetime, timedelta
import requests


class TestInvitations(ApiTest):
    fixtures = [
        {
            "org_super_user": lambda test, fixtures: user(
                test, fixtures, email="superuser@example.com"
            )
        },
        {"user": lambda test, fixtures: user(test, fixtures, email="user@example.com")},
        {"org": lambda test, fixtures: organization(test, fixtures, name="Test")},
        {
            "org_role": lambda test, fixtures: organization_role(
                test, fixtures, fixtures["org_super_user"], fixtures["org"], "superuser"
            )
        },
    ]

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

    def test_permissions(self):
        response = self.authenticated_get(
            self.user, "/organizations/invitations/{}".format(self.org.ext_id)
        )
        assert response.status_code == 404
        response = self.authenticated_post(
            self.user, "/organizations/invitations/{}".format(self.org.ext_id), json={}
        )
        assert response.status_code == 404

        response = self.authenticated_get(
            url="/organizations/invitations/{}".format(self.org.ext_id),
            user=self.org_super_user,
        )
        assert response.status_code == 200
        assert response.json()["invitations"] == []

    def test_creation(self):
        data = {"email": "test@tester.com", "message": "Join my org!", "role": "member"}

        response = self.authenticated_post(
            url="/organizations/invitations/{}".format(self.org.ext_id),
            user=self.org_super_user,
            json=data,
        )
        assert response.status_code == 201

        assert response.json()["email"] == data["email"]
        assert response.json()["role"] == data["role"]
        assert response.json()["message"] == data["message"]

        response = self.authenticated_get(
            url="/organizations/invitations/{}".format(self.org.ext_id),
            user=self.org_super_user,
        )
        assert response.status_code == 200
        assert len(response.json()["invitations"]) == 1
        invitation = (
            self.session.query(Invitation)
            .filter(Invitation.email == data["email"])
            .one()
        )
        assert invitation is not None

    def test_confirmation(self):
        data = {"email": "test@tester.com", "message": "Join my org!", "role": "member"}
        response = self.authenticated_post(
            url="/organizations/invitations/{}".format(self.org.ext_id),
            user=self.org_super_user,
            json=data,
        )

        invitation = (
            self.session.query(Invitation)
            .filter(Invitation.email == data["email"])
            .one()
        )

        user_data = {
            "email": data["email"],
            "password": "test1234",
            "language": "en",
            "email_verified": True,
            "invitation": invitation.token,
        }

        response = requests.post(self.url("/signup/password"), json=user_data)
        assert response.status_code == 200

        # confirm email
        finalize(self.session, self, user_data, generate_token=False)

        response = self.authenticated_get(
            self.org_super_user, "/organizations/roles/{}".format(self.org.ext_id)
        )
        user_obj = [
            uo["user"] for uo in response.json()["users"] if uo["role"] == "member"
        ]
        assert len(user_obj) == 1
        assert data["email"] == user_obj[0]["email"]

    def test_deletion(self):
        data = {"email": "test@tester.com", "message": "Join my org!", "role": "member"}

        response = self.authenticated_post(
            url="/organizations/invitations/{}".format(self.org.ext_id),
            user=self.org_super_user,
            json=data,
        )

        ext_id = response.json()["id"]

        response = self.authenticated_delete(
            url="/organizations/invitations/{}/{}".format(self.org.ext_id, ext_id),
            user=self.org_super_user,
        )
        assert response.status_code == 200

        invitation = (
            self.session.query(Invitation)
            .filter(Invitation.email == data["email"])
            .one_or_none()
        )
        assert invitation is None
        assert OrganizationInvitation.get_by_ext_id(self.session, ext_id) is None
