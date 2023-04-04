from .signup import GitlabSignup
from worf.models import LoginProvider


class GitlabLogin(GitlabSignup):
    def associate(self, data, user):
        result = self.validate(data)

        if result.get("error"):
            return result

        return self.finalize(user, result["data"])

    def login(self, data):
        """
        Performs the login via Gitlab.

        `data` contains the following information:

        - code: the auth code provided by Gitlab
        """

        # we need to validate the token by calling the Gitlab API

        result = self.validate(data)

        if result.get("error"):
            return result

        provider = LoginProvider.get_by_provider_id(
            self.session, "gitlab", result["data"]["id"]
        )

        if provider is None:
            return {"error": {"message": "not found"}, "status": 404}

        return {"user": provider.user}
