from worf.tests.helpers import ApiTest
from worf.models import User, AccessToken, LoginProvider
from worf.settings import settings
from worf.tests.fixtures import normal_user
import requests
import queue
import re


def provider(test, fixtures, user, name, id):
    provider = LoginProvider(user=user, provider=name, provider_id=id)
    test.session.add(provider)
    test.session.commit()
    return provider


class TestProviders(ApiTest):
    fixtures = [
        {"normal_user": normal_user},
        {
            "provider_a": lambda test, fixtures: provider(
                test, fixtures, fixtures["normal_user"], "a_provider", "a_id"
            )
        },
        {
            "provider_b": lambda test, fixtures: provider(
                test, fixtures, fixtures["normal_user"], "b_provider", "b_id"
            )
        },
    ]

    def test_list(self):
        """
        List providers
        """

        response = self.authenticated_get(url="/login", user=self.normal_user)
        assert response.status_code == 200

        data = response.json()
        assert "providers" in data
        providers = data["providers"]
        assert len(providers) == 2

    def test_delete(self):
        response = self.authenticated_delete(
            url="/login/{}".format(self.provider_a.ext_id), user=self.normal_user
        )
        assert response.status_code == 200

        response = self.authenticated_delete(
            url="/login/{}".format(self.provider_b.ext_id), user=self.normal_user
        )
        assert response.status_code == 400
