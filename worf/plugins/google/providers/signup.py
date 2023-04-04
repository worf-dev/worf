from worf.settings import settings

from ..forms import GoogleForm, GoogleIDTokenForm
from worf.models import LoginProvider


class GoogleSignup(object):

    """
    Example ID Token
    {
        'iss': 'accounts.google.com',
        'azp': '1094985475488-[...].apps.googleusercontent.com',
        'aud': '1094985475488-[...].apps.googleusercontent.com',
        'sub': '[number]',
        'email': 'max.mustermann@googlemail.com',
        'email_verified': True,
        'at_hash': '[hash]',
        'name': 'Max',
        'picture': 'https://lh3.googleusercontent.com/[...]/photo.jpg',
        'given_name': 'Mustermann',
        'locale': 'de',
        'iat': 1347947492,
        'exp': 1943351292,
        'jti': '[numerical value]'
    }
    """

    def __init__(self, session, resource):
        self.session = session
        self.resource = resource

    def finalize(self, user, data):
        provider = LoginProvider.get_by_provider_id(self.session, "google", data["sub"])

        if provider is not None:
            return {"error": {"message": "already exists"}, "status": 400}

        provider = LoginProvider(provider="google", user=user, provider_id=data["sub"])
        self.session.add(provider)
        self.session.commit()

        return {}

    def validate(self, data):
        form = GoogleForm(data=data)
        if not form.validate():
            return {
                "error": {"errors": form.errors, "message": "invalid data"},
                "status": 400,
            }
        id_token_form = GoogleIDTokenForm(data=form.valid_data["id_token"])

        if not id_token_form.validate():
            return {
                "error": {"errors": id_token_form.errors, "message": "invalid data"},
                "status": 400,
            }

        return {"data": id_token_form.valid_data}
