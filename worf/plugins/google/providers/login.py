from .signup import GoogleSignup
from worf.models import LoginProvider


class GoogleLogin(GoogleSignup):
    def associate(self, data, user):
        result = self.validate(data)

        if result.get("error"):
            return result

        return self.finalize(user, result["data"])

    def login(self, data):
        result = self.validate(data)

        if result.get("error"):
            return result

        provider = LoginProvider.get_by_provider_id(
            self.session, "google", result["data"]["sub"]
        )

        if provider is None:
            return {"error": {"message": "not found"}, "status": 404}

        return {"user": provider.user}
