from flask import request
from .forms.features import FeaturesForm

from worf.api.decorators.user import authorized
from worf.api.decorators.uuid import valid_uuid
from worf.api.resource import Resource
from worf.settings import settings
from worf.models import User
from ...models import Features


class UserFeatures(Resource):

    """
    Manage user features.
    """

    @authorized(scopes=("admin",), superuser=True)
    @valid_uuid(field="user_id")
    def post(self, user_id):
        """
        Add the given features to the user
        """
        user = User.get_by_ext_id(request.session, user_id)
        if not user:
            return {"message": "not found"}, 404
        form = FeaturesForm(request.get_json())
        if not form.validate():
            return {"message": "invalid data", "errors": form.errors}, 400
        if user.features is None:
            user.features = Features(user=user)
            request.session.add(user.features)
        user.features.features = form.valid_data["features"]
        request.session.add(user)
        return ({"message": "success"}, 200)
