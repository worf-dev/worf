from .signup import GithubSignup
from worf.models import LoginProvider


class GithubLogin(GithubSignup):
    def associate(self, data, user):
        result = self.validate(data)

        if result.get("error"):
            return result

        return self.finalize(user, result["data"])

    def login(self, data):
        """
        Performs the login via Github.

        `data` contains the following information:

        - code: the auth code provided by Github
        """

        # we need to validate the token by calling the Github API

        result = self.validate(data)

        if result.get("error"):
            return result

        provider = LoginProvider.get_by_provider_id(
            self.session, "github", result["data"]["id"]
        )

        if provider is None:
            return {"error": {"message": "not found"}, "status": 404}

        return {"user": provider.user}
