from ....decorators.user import authorized

from worf.api.resource import Resource
from worf.settings import settings
from flask import jsonify, request


class Logout(Resource):
    @authorized()
    def post(self):
        with settings.session() as session:
            request.access_token.valid = False
            session.add(request.access_token)
        # we explicitly construct the response as we delete the cookie
        response = jsonify({"message": self.t("success")})
        response.delete_cookie("access_token")
        return response
