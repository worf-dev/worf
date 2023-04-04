from worf.tests.helpers import ApiTest
from worf.tests.fixtures import super_user, normal_user, user
from ....models import Features


class TestUserFeatures(ApiTest):
    fixtures = [{"super_user": super_user}, {"normal_user": normal_user}]

    def test_features(self):
        features = ["a", "b", "c"]
        data = {"features": features}
        response = self.authenticated_post(
            url="/features/user/{}".format(self.normal_user.ext_id),
            user=self.super_user,
            json=data,
        )
        assert response.status_code == 200
        self.session.refresh(self.normal_user)
        assert self.normal_user.features is not None
        assert set(self.normal_user.features.features) == set(features)

        response = self.authenticated_post(
            url="/features/user/{}".format(self.normal_user.ext_id),
            user=self.super_user,
            json={"features": []},
        )
        assert response.status_code == 200

        self.session.refresh(self.normal_user)
        assert self.normal_user.features is not None
        assert set(self.normal_user.features.features) == set([])


class TestUserProfileWithFeatures(ApiTest):
    fixtures = [{"normal_user": normal_user}]

    def test_user_profile(self):
        features = ["a", "b", "c"]
        self.normal_user.features = Features(features=features)
        self.session.add(self.normal_user)
        self.session.commit()
        response = self.authenticated_get(url="/user", user=self.normal_user)
        assert response.status_code == 200
        assert set(response.json()["user"]["features"]) == set(features)
