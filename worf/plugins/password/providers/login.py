from .signup import PasswordSignup
from worf.models import LoginProvider, User


class PasswordLogin(PasswordSignup):
    def associate(self, data, user):
        result = self.validate(data, associate=True)

        if result.get("error"):
            return result

        return self.finalize(user, result["data"])

    def get_providers(self, data):
        return (
            self.session.query(LoginProvider)
            .join(User)
            .filter(LoginProvider.provider == "password", User.email == data["email"])
            .all()
        )

    def login(self, data):
        result = self.validate(data)

        if result.get("error"):
            return result

        user_data = result["data"]

        providers = self.get_providers(user_data)

        if not providers:
            return {"error": {"message": "login failed"}, "status": 404}

        for provider in providers:
            if self.check_password(user_data["password"], provider):
                return {"user": provider.user}

        return {"error": {"message": "login failed"}, "status": 403}
