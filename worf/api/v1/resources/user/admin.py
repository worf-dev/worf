from ...forms.user import UsersForm, UserForm, SuperUserEditForm

from ....decorators.user import authorized
from ....decorators.uuid import valid_uuid
from worf.settings import settings
from worf.models import User
from worf.api.resource import Resource

from sqlalchemy.sql import and_

from flask import request


class Users(Resource):
    @authorized(superuser=True, scopes=("admin",))
    @valid_uuid(optional=True)
    def get(self, user_id=None):
        with settings.session() as session:
            if user_id is not None:
                user = session.query(User).filter(User.ext_id == user_id).one_or_none()
                if user is None:
                    return {"message": self.t("not-found")}, 404
                return {"user": user.export()}, 200

            form = UsersForm(request.args)

            if not form.validate():
                return {"message": self.t("invalid-data"), "errors": form.errors}, 400

            params = {"offset": 0, "limit": 1000}
            queries = []

            for key, value in form.valid_data.items():
                if value != "" and value is not None:
                    params[key] = value

            users = session.query(User).filter(and_(*queries))

            joins = []
            for join in joins:
                users = users.join(join)

            users = (
                users.order_by(User.email)
                .limit(params["limit"] + 1)
                .offset(params["offset"])
            )

            return (
                {
                    "users": [user.export() for user in users[: params["limit"]]],
                    "has_more": True if users.count() > params["limit"] else False,
                    "params": params,
                },
                200,
            )

    @authorized(superuser=True, scopes=("admin",))
    def post(self):
        form = UserForm(request.get_json())
        if not form.validate():
            return {"message": self.t("invalid-data"), "errors": form.errors}, 400
        user = User()
        for key, value in form.valid_data.items():
            setattr(user, key, value)

        with settings.session() as session:
            existing_user = User.get_by_email(session, user.email)
            if existing_user:
                return {"message": self.t("users.already-exists")}, 400
            session.add(user)
            # we explicitly commit to create IDs
            session.commit()
            return {"user": user.export()}, 201

    @authorized(superuser=True, scopes=("admin",))
    @valid_uuid
    def patch(self, user_id):
        with settings.session() as session:
            user = session.query(User).filter(User.ext_id == user_id).one_or_none()
            if user is None:
                return {"message": self.t("not-found")}, 404
            form = SuperUserEditForm(request.get_json())
            if not form.validate():
                return {"message": self.t("invalid-data"), "errors": form.errors}, 400
            params = {}
            for key, value in form.valid_data.items():
                if value is None:
                    continue
                if key == "disabled" and request.user == user:
                    return (
                        {
                            "errors": {
                                "superuser": self.t("users.cannot-disable-own-account")
                            }
                        },
                        400,
                    )
                if key == "superuser" and request.user == user:
                    return (
                        {
                            "errors": {
                                "superuser": self.t(
                                    "users.cannot-remove-own-superuser-status"
                                )
                            }
                        },
                        400,
                    )
                setattr(user, key, value)
            # we explicitly commit this to create IDs
            session.commit()
            return {"user": user.export()}, 200

    @authorized(superuser=True, scopes=("admin",))
    @valid_uuid
    def delete(self, user_id):
        with settings.session() as session:
            user = User.get_by_ext_id(session, user_id)
            if user is None:
                return {"message": self.t("not-found")}, 404
            if user == request.user:
                return {"message": self.t("users.cannot-delete-own-account")}, 400
            session.delete(user)
            return {"message": self.t("success")}, 200
