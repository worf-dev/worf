from worf.models import User, LoginProvider

from .helpers import check_password, create_provider
from ..forms.password import SignupForm, AssociateForm


class PasswordSignup:
    def __init__(self, session, resource):
        self.session = session
        self.resource = resource

    def finalize(self, user, data):
        provider = create_provider(self.session, user, data["password"])
        return {}

    def validate(self, data, associate=False):
        if associate:
            form = AssociateForm(data)
        else:
            form = SignupForm(data)

        if not form.validate():
            return {
                "error": {"errors": form.errors, "message": "invalid data"},
                "status": 400,
            }

        return {"data": form.valid_data}

    def check_password(self, password, provider):
        return check_password(password, provider.data.get("password", ""))
