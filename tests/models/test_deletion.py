from worf.tests.helpers import DatabaseTest
from worf.models import User, AccessToken, LoginProvider
from worf.tests.fixtures import super_user, normal_user


class TestDeletion(DatabaseTest):

    """
    Test the deletion of related objects.
    """

    fixtures = [{"normal_user": normal_user}]

    def test_deletion(self):
        login_provider = LoginProvider(
            user=self.normal_user, provider="test", provider_id="test"
        )
        self.session.add(login_provider)
        self.session.commit()

        self.session.delete(self.normal_user)
        self.session.commit()

        assert self.session.query(User).count() == 0
        assert self.session.query(AccessToken).count() == 0
        assert self.session.query(LoginProvider).count() == 0

    def test_related_deletion(self):
        login_provider = LoginProvider(
            user=self.normal_user, provider="test", provider_id="test"
        )
        self.session.add(login_provider)
        self.session.commit()

        self.session.delete(login_provider)
        self.session.commit()

        assert self.session.query(User).count() == 1
        assert self.session.query(LoginProvider).count() == 0

        self.session.delete(self.normal_user.access_token)
        self.session.commit()

        assert self.session.query(AccessToken).count() == 0
        assert self.session.query(User).count() == 1
