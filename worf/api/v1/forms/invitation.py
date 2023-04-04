from worf.utils.forms import Form, Field
from worf.utils.forms.validators import (
    ToLower,
    String,
    Required,
    EMail,
    Boolean,
    Optional,
    DateTime,
)
from .validators import InFuture


class InvitationForm(Form):
    email = Field([Required(), String(), EMail(), ToLower()])
    message = Field([Optional(), String()])
    valid_until = Field([Optional(), DateTime(), InFuture()])
    tied_to_email = Field([Optional(default=False), Boolean(convert=True)])
