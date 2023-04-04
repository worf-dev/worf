from worf.settings import settings

from ..forms import GitlabForm
from worf.models import LoginProvider
import requests
import logging


class GitlabSignup(object):

    """ """

    def __init__(self, session, resource):
        self.session = session
        self.resource = resource

    def finalize(self, user, data):
        provider = LoginProvider.get_by_provider_id(self.session, "gitlab", data["id"])

        if provider is not None:
            return {"error": {"message": "already exists"}, "status": 400}

        provider = LoginProvider(provider="gitlab", user=user, provider_id=data["id"])
        self.session.add(provider)
        self.session.commit()

        return {}

    def validate(self, data):
        form = GitlabForm(data=data)

        gl_settings = settings.get("gitlab", {})
        host = gl_settings["host"]
        client_id = gl_settings["client_id"]
        client_secret = gl_settings["client_secret"]
        redirect_uri = gl_settings["redirect_uri"]

        if not form.validate():
            return {
                "error": {"errors": form.errors, "message": "invalid data"},
                "status": 400,
            }
        err = {"error": {"message": "authentication failed"}}

        test = settings.get("test")
        if test:
            if (
                form.valid_data["code"] != gl_settings["code"]
                or form.valid_data["state"] != gl_settings["state"]
            ):
                return err
            return {"data": gl_settings["user_response_data"]}

        # we retrieve an access token
        access_token_response = requests.post(
            f"https://{host}/oauth/token",
            data={
                "client_id": client_id,
                "client_secret": client_secret,
                "redirect_uri": form.valid_data["redirect_uri"],
                "code": form.valid_data["code"],
                "grant_type": "authorization_code",
            },
            headers={"Accept": "application/json"},
        )

        if access_token_response.status_code != 200:
            return err

        access_token_data = access_token_response.json()

        if access_token_data.get("error"):
            return err

        access_token = access_token_data["access_token"]

        headers = {"Authorization": f"Bearer {access_token}"}

        user_response = requests.get(f"https://{host}/api/v4/user", headers=headers)

        if user_response.status_code != 200:
            return err

        user_data = user_response.json()
        data = {
            "id": str(user_data["id"]),
            "email": user_data["email"],
            "email_verified": True,
        }

        return {"data": data}
