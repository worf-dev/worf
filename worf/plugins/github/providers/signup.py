from worf.settings import settings

from ..forms import GithubForm
from worf.models import LoginProvider
import requests
import logging

logger = logging.getLogger(__name__)


class GithubSignup(object):

    """ """

    def __init__(self, session, resource):
        self.session = session
        self.resource = resource

    def finalize(self, user, data):
        provider = LoginProvider.get_by_provider_id(self.session, "github", data["id"])

        if provider is not None:
            return {"error": {"message": "already exists"}, "status": 400}

        provider = LoginProvider(provider="github", user=user, provider_id=data["id"])
        self.session.add(provider)
        self.session.commit()

        return {}

    def validate(self, data):
        form = GithubForm(data=data)

        gh_settings = settings.get("github", {})
        host = gh_settings["host"]
        client_id = gh_settings["client_id"]
        client_secret = gh_settings["client_secret"]
        redirect_uri = gh_settings["redirect_uri"]

        if not form.validate():
            return {
                "error": {"errors": form.errors, "message": "invalid data"},
                "status": 400,
            }
        err = {"error": {"message": "authentication failed"}}

        test = settings.get("test")
        if test:
            if (
                form.valid_data["code"] != gh_settings["code"]
                or form.valid_data["state"] != gh_settings["state"]
            ):
                return err
            return {"data": gh_settings["user_response_data"]}

        # we retrieve an access token
        access_token_response = requests.post(
            f"https://{host}/login/oauth/access_token",
            data={
                "client_id": client_id,
                "client_secret": client_secret,
                "redirect_uri": redirect_uri,
                "code": form.valid_data["code"],
                "state": form.valid_data["state"],
            },
            headers={"Accept": "application/json"},
        )

        if access_token_response.status_code != 200:
            return err

        access_token_data = access_token_response.json()

        if access_token_data.get("error"):
            return err

        access_token = access_token_data["access_token"]

        headers = {"Authorization": f"token {access_token}"}

        user_response = requests.get(f"https://api.{host}/user", headers=headers)

        if user_response.status_code != 200:
            return err

        email_response = requests.get(
            f"https://api.{host}/user/emails", headers=headers
        )

        user_data = user_response.json()

        data = {
            "id": str(user_data["id"]),
            "token": settings.encrypt(access_token).decode("ascii"),
        }

        if email_response.status_code != 200:
            return err

        email_data = email_response.json()

        for email in email_data:
            if email["primary"]:
                data["email"] = email["email"]
                data["email_verified"] = email["verified"]

        # we immediately delete the access token again
        return {"data": data}
