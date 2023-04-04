from worf.tests.helpers import ApiTest
from worf.settings import settings
import requests
import uuid
import re

from sqlalchemy.sql import and_

from worf.models import User
from worf.tests.fixtures import super_user, normal_user, user
from ...fixtures import organization, organization_role
from ....models import OrganizationRole, Organization


class TestProfile(ApiTest):
    fixtures = [
        {"user": lambda test, fixtures: user(test, fixtures, email="user@example.com")},
        {"org": lambda test, fixtures: organization(test, fixtures, name="Test")},
        {
            "org_role": lambda test, fixtures: organization_role(
                test, fixtures, fixtures["user"], fixtures["org"], "superuser"
            )
        },
    ]

    def test_profile(self):
        response = self.authenticated_get(url="/user", user=self.user)
        assert response.status_code == 200

        data = response.json()

        assert "organizations" in data
        assert isinstance(data["organizations"], list)
        assert len(data["organizations"]) == 1
        assert "roles" in data["organizations"][0]
        assert len(data["organizations"][0]["roles"]) == 1
        assert data["organizations"][0]["roles"][0]["role"] == "superuser"


class TestCreation(ApiTest):
    fixtures = [{"user": normal_user}]

    def test_creation(self):
        data = {"name": "Test Org"}
        response = self.authenticated_post(
            url="/organizations", user=self.user, json=data
        )
        assert response.status_code == 201

        org_id = response.json()["organization"]["id"]

        assert (
            self.session.query(OrganizationRole)
            .join(Organization)
            .filter(
                and_(
                    OrganizationRole.user == self.user,
                    OrganizationRole.role == "superuser",
                    Organization.ext_id == uuid.UUID(org_id),
                )
            )
            .one_or_none()
        )

        response = self.authenticated_post(
            url="/organizations", user=self.user, json=data
        )
        assert response.status_code == 400


class TestEditing(ApiTest):
    fixtures = [
        {
            "user_1": lambda test, fixtures: user(
                test, fixtures, email="user1@example.com"
            )
        },
        {
            "user_2": lambda test, fixtures: user(
                test, fixtures, email="user2@example.com"
            )
        },
        {"org_1": lambda test, fixtures: organization(test, fixtures, name="Test 1")},
        {"org_2": lambda test, fixtures: organization(test, fixtures, name="Test 2")},
        {
            "org_role_1": lambda test, fixtures: organization_role(
                test, fixtures, fixtures["user_1"], fixtures["org_1"], "superuser"
            )
        },
        {
            "org_role_2": lambda test, fixtures: organization_role(
                test, fixtures, fixtures["user_2"], fixtures["org_2"], "superuser"
            )
        },
    ]

    def test_editing(self):
        data = {"name": "Test Org", "description": "This is my description"}

        response = self.authenticated_patch(
            url="/organizations/{}".format(self.org_1.ext_id),
            user=self.user_1,
            json=data,
        )
        assert response.status_code == 200

        self.session.refresh(self.org_1)
        assert self.org_1.name == data["name"]
        assert self.org_1.description == data["description"]

        response = self.authenticated_patch(
            url="/organizations/{}".format(self.org_2.ext_id),
            user=self.user_1,
            json=data,
        )
        assert response.status_code == 404


class TestDetails(ApiTest):
    fixtures = [
        {
            "user_1": lambda test, fixtures: user(
                test, fixtures, email="user1@example.com"
            )
        },
        {
            "user_2": lambda test, fixtures: user(
                test, fixtures, email="user2@example.com"
            )
        },
        {"org": lambda test, fixtures: organization(test, fixtures, name="Test")},
        {
            "org_role_1": lambda test, fixtures: organization_role(
                test, fixtures, fixtures["user_1"], fixtures["org"], "superuser"
            )
        },
    ]

    def test_details(self):
        response = self.authenticated_get(
            url="/organizations/{}".format(self.org.ext_id), user=self.user_1
        )
        assert response.status_code == 200

        response = self.authenticated_get(
            url="/organizations/{}".format(self.org.ext_id), user=self.user_2
        )
        assert response.status_code == 404


class TestDeletion(ApiTest):
    fixtures = [
        {
            "user_1": lambda test, fixtures: user(
                test, fixtures, email="user1@example.com"
            )
        },
        {
            "user_2": lambda test, fixtures: user(
                test, fixtures, email="user2@example.com"
            )
        },
        {"org": lambda test, fixtures: organization(test, fixtures, name="Test")},
        {
            "org_role_1": lambda test, fixtures: organization_role(
                test, fixtures, fixtures["user_1"], fixtures["org"], "superuser"
            )
        },
        {
            "org_role_2": lambda test, fixtures: organization_role(
                test, fixtures, fixtures["user_2"], fixtures["org"], "admin"
            )
        },
    ]

    def test_deletion(self):
        response = self.authenticated_delete(
            url="/organizations/{}".format(self.org.ext_id), user=self.user_2
        )
        assert response.status_code == 404

        response = self.authenticated_delete(
            url="/organizations/{}".format(self.org.ext_id), user=self.user_1
        )
        assert response.status_code == 200

        assert self.session.query(Organization).count() == 0
        assert self.session.query(OrganizationRole).count() == 0
        assert self.session.query(User).count() == 2

        response = self.authenticated_delete(
            url="/organizations/{}".format(self.org.ext_id), user=self.user_1
        )
        assert response.status_code == 404


class TestOrganizationRoleCreationByEMail(ApiTest):
    fixtures = [
        {
            "user_1": lambda test, fixtures: user(
                test, fixtures, email="user1@example.com"
            )
        },
        {
            "user_2": lambda test, fixtures: user(
                test, fixtures, email="user2@example.com"
            )
        },
        {
            "user_3": lambda test, fixtures: user(
                test, fixtures, email="user3@example.com"
            )
        },
        {"org_1": lambda test, fixtures: organization(test, fixtures, name="Test 1")},
        {"org_2": lambda test, fixtures: organization(test, fixtures, name="Test 2")},
        {
            "org_role_1": lambda test, fixtures: organization_role(
                test, fixtures, fixtures["user_1"], fixtures["org_1"], "superuser"
            )
        },
        {
            "org_role_2": lambda test, fixtures: organization_role(
                test, fixtures, fixtures["user_2"], fixtures["org_2"], "superuser"
            )
        },
    ]

    def test_organization_role_creation_by_mail(self):
        data = {"email": self.user_3.email, "role": "admin"}
        response = self.authenticated_post(
            self.user_1, "/organizations/roles/{}".format(self.org_1.ext_id), json=data
        )
        assert response.status_code == 201

        assert (
            self.session.query(OrganizationRole)
            .filter(
                and_(
                    OrganizationRole.user == self.user_3,
                    OrganizationRole.organization == self.org_1,
                    OrganizationRole.role == "admin",
                )
            )
            .one_or_none()
        )

        # a user should only be allowed to be in one organization
        response = self.authenticated_post(
            self.user_2, "/organizations/roles/{}".format(self.org_2.ext_id), json=data
        )
        assert response.status_code == 400


class TestOrganizationRoleList(ApiTest):
    fixtures = [
        {
            "user_1": lambda test, fixtures: user(
                test, fixtures, email="user1@example.com"
            )
        },
        {
            "user_2": lambda test, fixtures: user(
                test, fixtures, email="user2@example.com"
            )
        },
        {"org": lambda test, fixtures: organization(test, fixtures, name="Test")},
        {
            "org_role_1": lambda test, fixtures: organization_role(
                test, fixtures, fixtures["user_1"], fixtures["org"], "superuser"
            )
        },
        {
            "org_role_2": lambda test, fixtures: organization_role(
                test, fixtures, fixtures["user_2"], fixtures["org"], "admin"
            )
        },
    ]

    def test_organization_role_list(self):
        response = self.authenticated_get(
            self.user_1, "/organizations/roles/{}".format(self.org.ext_id)
        )
        assert response.status_code == 200
        data = response.json()
        assert "users" in data
        users = data["users"]
        assert isinstance(users, list) and len(users) == 2
        user_1 = next(
            filter(
                lambda user: uuid.UUID(user["user"]["id"]) == self.user_1.ext_id, users
            ),
            None,
        )
        assert user_1
        assert user_1["role"] == "superuser"
        user_2 = next(
            filter(
                lambda user: uuid.UUID(user["user"]["id"]) == self.user_2.ext_id, users
            ),
            None,
        )
        assert user_2
        assert user_2["role"] == "admin"


class TestOrganizationRoleDuplication(ApiTest):
    fixtures = [
        {
            "user_1": lambda test, fixtures: user(
                test, fixtures, email="user1@example.com"
            )
        },
        {
            "user_2": lambda test, fixtures: user(
                test, fixtures, email="user2@example.com"
            )
        },
        {"org_1": lambda test, fixtures: organization(test, fixtures, name="Test 1")},
        {"org_2": lambda test, fixtures: organization(test, fixtures, name="Test 2")},
        {
            "org_role_1": lambda test, fixtures: organization_role(
                test, fixtures, fixtures["user_1"], fixtures["org_1"], "superuser"
            )
        },
        {
            "org_role_2": lambda test, fixtures: organization_role(
                test, fixtures, fixtures["user_2"], fixtures["org_2"], "superuser"
            )
        },
    ]

    def test_two_orgs(self):
        data = {"user_id": str(self.user_2.ext_id), "role": "admin"}
        response = self.authenticated_post(
            self.user_1, "/organizations/roles/{}".format(self.org_1.ext_id), json=data
        )
        assert response.status_code == 400
        data = {"user_id": str(self.user_1.ext_id), "role": "admin"}
        response = self.authenticated_post(
            self.user_2, "/organizations/roles/{}".format(self.org_2.ext_id), json=data
        )
        assert response.status_code == 400


class TestOrganizationRoleDeletion(ApiTest):
    fixtures = [
        {
            "user_1": lambda test, fixtures: user(
                test, fixtures, email="user1@example.com"
            )
        },
        {
            "user_2": lambda test, fixtures: user(
                test, fixtures, email="user2@example.com"
            )
        },
        {"org": lambda test, fixtures: organization(test, fixtures, name="Test")},
        {
            "org_role_1": lambda test, fixtures: organization_role(
                test, fixtures, fixtures["user_1"], fixtures["org"], "superuser"
            )
        },
        {
            "org_role_2": lambda test, fixtures: organization_role(
                test, fixtures, fixtures["user_2"], fixtures["org"], "admin"
            )
        },
    ]

    def test_organization_role_deletion(self):
        response = self.authenticated_delete(
            self.user_1,
            "/organizations/roles/{}/{}".format(
                self.org.ext_id, self.org_role_2.ext_id
            ),
        )
        assert response.status_code == 200
        assert (
            self.session.query(OrganizationRole)
            .filter(OrganizationRole.user == self.user_2)
            .one_or_none()
            is None
        )

        response = self.authenticated_delete(
            self.user_1,
            "/organizations/roles/{}/{}".format(
                self.org.ext_id, self.org_role_1.ext_id
            ),
        )
        assert response.status_code == 400
