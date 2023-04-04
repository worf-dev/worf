from worf.tests.helpers import ApiTest
from worf.models import User, AccessToken, SignupRequest
from worf.settings import settings
from worf.tests.fixtures import super_user, normal_user
import requests
import queue
import re


class TestUserAdmin(ApiTest):
    fixtures = [{"super_user": super_user}, {"normal_user": normal_user}]

    def test_list_users(self):
        response = self.authenticated_get(url="/users", user=self.normal_user)
        assert response.status_code == 403

        response = self.authenticated_get(url="/users", user=self.super_user)
        assert response.status_code == 200
        data = response.json()
        assert "users" in data
        users = data["users"]
        assert len(users) == 2

        # invalid UUIDs should be rejected
        response = self.authenticated_get(
            url="/users/123456789012345678901234567890123456", user=self.super_user
        )
        assert response.status_code == 400

        response = self.authenticated_get(
            url="/users/{}".format(users[0]["id"]), user=self.super_user
        )
        assert response.status_code == 200
        data = response.json()
        assert "user" in data
        assert data["user"]["id"] == users[0]["id"]

    def test_create_user(self):
        user_data = {
            "email": "foobar@bar.com",
            "display_name": "max.mustermann",
            "language": "en",
        }

        response = self.authenticated_post(
            url="/users", user=self.normal_user, json=user_data
        )
        assert response.status_code == 403

        response = self.authenticated_post(
            url="/users", user=self.super_user, json=user_data
        )
        assert response.status_code == 201

        users = self.session.query(User).all()

        assert len(users) == 3

    def test_delete_user(self):
        # normal users can't delete users
        response = self.authenticated_delete(
            url="/users/{}".format(self.super_user.ext_id), user=self.normal_user
        )
        assert response.status_code == 403

        # super users can't delete themselves
        response = self.authenticated_delete(
            url="/users/{}".format(self.super_user.ext_id), user=self.super_user
        )
        assert response.status_code == 400

        response = self.authenticated_delete(
            url="/users/{}".format(self.normal_user.ext_id), user=self.super_user
        )
        assert response.status_code == 200

        users = self.session.query(User).all()
        assert len(users) == 1

    def test_update_user(self):
        user_data = {
            "email": "foobar@bar.com",
            "display_name": "max.mustermann",
            "language": "en",
        }

        response = self.authenticated_patch(
            url="/users/{}".format(self.normal_user.ext_id),
            user=self.super_user,
            json=user_data,
        )
        assert response.status_code == 200

        response = self.authenticated_get(url="/user", user=self.normal_user)
        assert response.status_code == 200

        data = response.json()["user"]

        for key in user_data.keys():
            assert data[key] == user_data[key]

    def test_disable_user(self):
        user_data = {"disabled": "1"}

        response = self.authenticated_patch(
            url="/users/{}".format(self.normal_user.ext_id),
            user=self.super_user,
            json=user_data,
        )
        assert response.status_code == 200

        self.session.refresh(self.normal_user)
        assert self.normal_user.disabled
