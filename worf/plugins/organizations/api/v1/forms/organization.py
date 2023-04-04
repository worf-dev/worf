from worf.utils.forms import Form, Field, Optional
from worf.api.v1.forms.validators import DisplayName, InFuture
from worf.utils.forms.validators import (
    String,
    ToLower,
    DateTime,
    Required,
    Integer,
    Boolean,
    Choices,
    UUID,
    EMail,
    Length,
)

from worf.settings import settings


class Role:
    def __init__(self):
        self.choices = set(settings.get("organizations.roles", []))

    def __call__(self, name, value, form):
        if not value in self.choices:
            return ["not a valid choice. choices: {}".format(self.choices)], None, True


class OrganizationForm(Form):
    name = Field([Required(), String(), Length(max=50)])
    description = Field([Optional(), String(), Length(max=600)])


class OrganizationEditForm(Form):
    name = Field([Required(), String(), Length(max=50)])
    description = Field([Optional(), String(), Length(max=600)])


class OrganizationAdminEditForm(OrganizationEditForm):
    name = Field([Required(), String(), Length(max=50)])
    description = Field([Optional(), String(), Length(max=600)])
    active = Field([Optional(default=True), Boolean(convert=True)])


class OrganizationRoleEditForm(Form):
    def __init__(self, roles, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.roles = roles

    role = Field([Required(), String(), Role()])
    user_id = Field([Required(), UUID()])


class OrganizationRoleForm(Form):
    role = Field([Required(), String(), Role()])
    email = Field([Required(), String(), EMail()])


class OrganizationsForm(Form):
    offset = Field([Optional(default=0), Integer(convert=True, min=0)])
    limit = Field([Optional(default=20), Integer(convert=True, min=1, max=1000)])
    direction = Field(
        [Optional(default="desc"), String(), Choices(set(["desc", "asc"]))]
    )
    order_by = Field(
        [
            Optional(default="email"),
            String(),
            Choices(set(["created", "updated", "name"])),
        ]
    )
    query = Field([Optional(), String(), Length(max=40)])


class OrganizationInvitationForm(Form):
    email = Field([Required(), String(), EMail(), ToLower()])
    message = Field([Optional(), String()])
    role = Field([Required(), String(), Role()])
    valid_until = Field([Optional(), DateTime(), InFuture()])
    tied_to_email = Field([Optional(default=False), Boolean(convert=True)])
