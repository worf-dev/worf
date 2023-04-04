from worf.utils.forms import Form, Field
from worf.utils.forms.validators import (
    ToLower,
    String,
    Required,
    EMail,
    Dict,
    Boolean,
    Optional,
    Integer,
    Choices,
)
from .validators import DisplayName, Language


class UserForm(Form):
    display_name = Field([Optional(), String(), DisplayName()])
    email = Field([Optional(), String(), Required(), EMail(), ToLower()])
    language = Field([Required(), String(), Language()])

    superuser = Field([Optional(default=False), Boolean(convert=True)])
    disabled = Field([Optional(default=False), Boolean(convert=True)])


class UserEditForm(Form):
    """
    Fields editable by a normal user.
    """

    display_name = Field([Optional(), DisplayName()])
    language = Field([Optional(), String(), Language()])
    data = Field([Optional(), Dict()])


class SuperUserEditForm(Form):
    """
    Fields editable by a superuser.
    """

    display_name = Field([Optional(), DisplayName()])
    data = Field([Optional(), DisplayName()])
    email = Field([Optional(), String(), EMail(), ToLower()])
    superuser = Field([Optional(default=False), Boolean(convert=True)])
    disabled = Field([Optional(default=False), Boolean(convert=True)])


class UsersForm(Form):
    offset = Field([Optional(default=0), Integer(convert=True, min=0)])
    limit = Field([Optional(default=20), Integer(convert=True, min=1, max=1000)])
    direction = Field(
        [Optional(default="desc"), String(), Choices(set(["desc", "asc"]))]
    )
    order_by = Field(
        [
            Optional(default="email"),
            String(),
            Choices(set(["created", "updated", "email"])),
        ]
    )
