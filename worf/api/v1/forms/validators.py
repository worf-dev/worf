from worf.settings import settings
from worf.models import User
import datetime
import re


class InFuture:
    def __call__(self, name, value, form, field):
        if value < datetime.datetime.utcnow():
            return ["access token validity in the past"], None, True
        return [], value, False


class Scopes:
    def __call__(self, name, value, form):
        possible_scopes = settings.get("api.access_token_scopes", {})
        superuser_scopes = set(settings.get("api.superuser_access_token_scopes", []))
        if not value:
            return ["please choose at least one scope"], None, True
        if not isinstance(value, list):
            return ["scopes is not a list"], None, True
        scopes = []
        for scope_name in value:
            if not scope_name in possible_scopes:
                return (
                    [
                        "invalid scope. valid scopes: {}".format(
                            ", ".join(possible_scopes.keys())
                        )
                    ],
                    None,
                    True,
                )
            scopes.append(scope_name)
        if not form.superuser:
            for scope in scopes:
                if scope in superuser_scopes:
                    return (
                        [
                            "invalid scope. valid scopes: {}".format(
                                ", ".join(possible_scopes.keys())
                            )
                        ],
                        None,
                        True,
                    )
        return [], scopes, False


class DisplayName:
    regex = re.compile(r"^[a-z0-9\-\._]{4,30}$")

    def __call__(self, name, value, form):
        if not self.regex.match(value):
            return (
                ["invalid display name. regex: {}".format(self.regex.pattern)],
                None,
                True,
            )


class Code:
    regex = re.compile(r"^[a-z0-9]{16,32}$")

    def __call__(self, name, value, form):
        if not self.regex.match(value):
            return (["invalid code. regex: {}".format(self.regex.pattern)], None, True)


class Language:
    regex = re.compile(r"^[a-z]{2}$")

    def __call__(self, name, value, form):
        if not self.regex.match(value):
            return (
                ["invalid language. regex: {}".format(self.regex.pattern)],
                None,
                True,
            )
        if not value in settings.get("languages"):
            return (
                [
                    "invalid choice. choices: {}".format(
                        ", ".join(settings.get("languages"))
                    )
                ],
                None,
                True,
            )
