from ....decorators.user import authorized
from worf.settings import settings
from worf.api.resource import Resource
from ...forms.user import UserEditForm

from flask import request

import traceback
import logging

logger = logging.getLogger(__name__)


class UserProfile(Resource):
    @classmethod
    def profile(cls, user=None, access_token=None, with_token=False):
        if user is None:
            user = request.user

        if access_token is None:
            access_token = request.access_token

        profile = {
            "user": user.export(full=access_token.has_scope("admin")),
            "limits": {},
            "access_token": access_token.export(with_token=with_token),
        }

        # we add extra information to the profile via providers
        # (e.g. organization membership)

        # we add limits information
        for k, v in settings.get("limits", {}).items():
            if k in profile["limits"]:
                profile["limits"][k] += v
            profile["limits"][k] = v

        providers = settings.providers.get("profile", [])
        for provider in providers:
            try:
                provider(profile, user, access_token)
            except:
                # we ignore exceptions here to not break the profile endpoint
                # entirely if a single provider breaks...
                logger.error(traceback.format_exc())

        return profile

    @authorized()
    def get(self):
        return self.profile(), 200

    @authorized(scopes=("admin",))
    def patch(self):
        data = request.get_json() or {}
        form = UserEditForm(data)
        if not form.validate():
            return {"message": self.t("invalid-data"), "errors": form.errors}, 400
        with settings.session() as session:
            session.add(request.user)
            for k, v in form.valid_data.items():
                if v is None:
                    continue
                if k == "data":
                    # we partially update the data entry to avoid deleting important data
                    for dk, dv in v.items():
                        print(dk, dv)
                        request.user.set_data(dk, dv)
                else:
                    setattr(request.user, k, v)
            session.commit()
            return self.profile(), 200
