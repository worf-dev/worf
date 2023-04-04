from .validators import Code
from worf.utils.forms import Form, Field
from worf.utils.forms.validators import (
    Optional,
    Length,
    DateTime,
    String,
    Required,
    EMail,
)


class EMailChangeForm(Form):
    code = Field([Required(), Code()])


class EMailChangeRequestForm(Form):
    email = Field([Required(), EMail()])
