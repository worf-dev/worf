from worf.tests.fixtures.users import normal_user
from worf.tests.helpers import ApiTest
from worf.settings import settings
import requests


class TestAssociate(ApiTest):
    fixtures = [{"normal_user": normal_user}]

    def test_association(self):
        # we associate the user with a Gitlab account
        response = self.authenticated_post(
            self.normal_user,
            "/login/gitlab",
            json={
                "code": "1234",
                "state": "foo",
                "language": "en",
                "redirect_uri": "http://localhost:8080/associate/gitlab",
            },
        )

        assert response.status_code == 200
        data = response.json()

        response = requests.post(
            self.url("/login/gitlab"),
            json={
                "code": "1234",
                "state": "foo",
                "redirect_uri": "http://localhost:8080/login/gitlab",
            },
        )

        assert response.status_code == 201
