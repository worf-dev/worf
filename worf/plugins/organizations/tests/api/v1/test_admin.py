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


class TestAdminCreation(ApiTest):
    fixtures = [{"super_user": super_user}]

    def test_creation(self):
        data = {"name": "Test Org"}
        response = self.authenticated_post(
            url="/organizations/admin", user=self.super_user, json=data
        )
        assert response.status_code == 201

        org_id = response.json()["organization"]["id"]

        assert self.session.query(OrganizationRole).count() == 0


class TestAdminEditing(ApiTest):
    fixtures = [
        {
            "super_user": lambda test, fixtures: user(
                test, fixtures, email="super@example.com", superuser=True
            )
        },
        {"user": lambda test, fixtures: user(test, fixtures, email="user@example.com")},
        {"org": lambda test, fixtures: organization(test, fixtures, name="Test")},
        {
            "org_role": lambda test, fixtures: organization_role(
                test, fixtures, fixtures["user"], fixtures["org"], "superuser"
            )
        },
    ]

    def test_editing(self):
        data = {
            "name": "Test Org",
            "description": "This is my description",
            "active": "",
        }

        response = self.authenticated_patch(
            url="/organizations/admin/{}".format(self.org.ext_id),
            user=self.super_user,
            json=data,
        )
        assert response.status_code == 200

        self.session.refresh(self.org)
        assert self.org.name == data["name"]
        assert self.org.description == data["description"]
        assert self.org.active == (False if data["active"] is False else True)

        response = self.authenticated_patch(
            url="/organizations/admin/{}".format(self.org.ext_id),
            user=self.user,
            json=data,
        )
        assert response.status_code == 403


class TestAdminDeletion(ApiTest):
    fixtures = [
        {
            "super_user": lambda test, fixtures: user(
                test, fixtures, email="super@example.com", superuser=True
            )
        },
        {"user": lambda test, fixtures: user(test, fixtures, email="user@example.com")},
        {"org": lambda test, fixtures: organization(test, fixtures, name="Test")},
        {
            "org_role": lambda test, fixtures: organization_role(
                test, fixtures, fixtures["user"], fixtures["org"], "superuser"
            )
        },
    ]

    def test_deletion(self):
        response = self.authenticated_delete(
            url="/organizations/admin/{}".format(self.org.ext_id), user=self.user
        )
        assert response.status_code == 403

        response = self.authenticated_delete(
            url="/organizations/admin/{}".format(self.org.ext_id), user=self.super_user
        )
        assert response.status_code == 200

        assert self.session.query(Organization).count() == 0
        assert self.session.query(OrganizationRole).count() == 0
        assert self.session.query(User).count() == 2


class TestAdminListing(ApiTest):
    fixtures = [
        {
            "super_user": lambda test, fixtures: user(
                test, fixtures, email="super@example.com", superuser=True
            )
        },
        {"user": lambda test, fixtures: user(test, fixtures, email="user@example.com")},
        {"org": lambda test, fixtures: organization(test, fixtures, name="Test")},
        {
            "org_role": lambda test, fixtures: organization_role(
                test, fixtures, fixtures["user"], fixtures["org"], "superuser"
            )
        },
    ]

    def test_listing(self):
        response = self.authenticated_get(url="/organizations/admin", user=self.user)
        assert response.status_code == 403

        response = self.authenticated_get(
            url="/organizations/admin", user=self.super_user
        )
        assert response.status_code == 200

        data = response.json()

        assert "organizations" in data
        organizations = data["organizations"]
        assert len(organizations) == 1


class TestAdminOrganizationRoleCreationByEMail(ApiTest):
    fixtures = [
        {
            "super_user": lambda test, fixtures: user(
                test, fixtures, email="user1@example.com", superuser=True
            )
        },
        {
            "user": lambda test, fixtures: user(
                test, fixtures, email="user2@example.com"
            )
        },
        {"org_1": lambda test, fixtures: organization(test, fixtures, name="Test 1")},
        {"org_2": lambda test, fixtures: organization(test, fixtures, name="Test 2")},
    ]

    def test_organization_role_creation_by_mail(self):
        data = {"email": self.user.email, "role": "admin"}

        response = self.authenticated_post(
            self.user,
            "/organizations/admin/roles/{}".format(self.org_1.ext_id),
            json=data,
        )
        assert response.status_code == 403

        response = self.authenticated_post(
            self.super_user,
            "/organizations/admin/roles/{}".format(self.org_1.ext_id),
            json=data,
        )
        assert response.status_code == 201

        assert (
            self.session.query(OrganizationRole)
            .filter(
                and_(
                    OrganizationRole.user == self.user,
                    OrganizationRole.organization == self.org_1,
                    OrganizationRole.role == "admin",
                )
            )
            .one_or_none()
        )

        # a user should only be allowed to be in one organization
        response = self.authenticated_post(
            self.super_user,
            "/organizations/admin/roles/{}".format(self.org_2.ext_id),
            json=data,
        )
        assert response.status_code == 400


class TestAdminOrganizationRoleList(ApiTest):
    fixtures = [
        {
            "super_user": lambda test, fixtures: user(
                test, fixtures, email="user1@example.com", superuser=True
            )
        },
        {
            "user": lambda test, fixtures: user(
                test, fixtures, email="user2@example.com"
            )
        },
        {"org": lambda test, fixtures: organization(test, fixtures, name="Test")},
        {
            "org_role": lambda test, fixtures: organization_role(
                test, fixtures, fixtures["user"], fixtures["org"], "admin"
            )
        },
    ]

    def test_organization_role_list(self):
        response = self.authenticated_get(
            self.super_user, "/organizations/admin/roles/{}".format(self.org.ext_id)
        )
        assert response.status_code == 200
        response = self.authenticated_get(
            self.user, "/organizations/admin/roles/{}".format(self.org.ext_id)
        )
        assert response.status_code == 403


class TestAdminOrganizationRoleDuplication(ApiTest):
    fixtures = [
        {
            "super_user": lambda test, fixtures: user(
                test, fixtures, email="user1@example.com", superuser=True
            )
        },
        {
            "user": lambda test, fixtures: user(
                test, fixtures, email="user2@example.com"
            )
        },
        {"org_1": lambda test, fixtures: organization(test, fixtures, name="Test 1")},
        {"org_2": lambda test, fixtures: organization(test, fixtures, name="Test 2")},
        {
            "org_role": lambda test, fixtures: organization_role(
                test, fixtures, fixtures["user"], fixtures["org_2"], "superuser"
            )
        },
    ]

    def test_two_orgs(self):
        data = {"user_id": str(self.user.ext_id), "role": "admin"}
        response = self.authenticated_post(
            self.super_user,
            "/organizations/admin/roles/{}".format(self.org_2.ext_id),
            json=data,
        )
        assert response.status_code == 400

        response = self.authenticated_post(
            self.user,
            "/organizations/admin/roles/{}".format(self.org_2.ext_id),
            json=data,
        )
        assert response.status_code == 403


class TestAdminOrganizationRoleDeletion(ApiTest):
    fixtures = [
        {
            "super_user": lambda test, fixtures: user(
                test, fixtures, email="user1@example.com", superuser=True
            )
        },
        {
            "user": lambda test, fixtures: user(
                test, fixtures, email="user2@example.com"
            )
        },
        {"org": lambda test, fixtures: organization(test, fixtures, name="Test")},
        {
            "org_role": lambda test, fixtures: organization_role(
                test, fixtures, fixtures["user"], fixtures["org"], "superuser"
            )
        },
    ]

    def test_organization_role_deletion(self):
        response = self.authenticated_delete(
            self.super_user,
            "/organizations/admin/roles/{}/{}".format(
                self.org.ext_id, self.org_role.ext_id
            ),
        )
        assert response.status_code == 200
        assert (
            self.session.query(OrganizationRole)
            .filter(OrganizationRole.user == self.user)
            .one_or_none()
            is None
        )

        response = self.authenticated_delete(
            self.user,
            "/organizations/admin/roles/{}/{}".format(
                self.org.ext_id, self.org_role.ext_id
            ),
        )
        assert response.status_code == 403
