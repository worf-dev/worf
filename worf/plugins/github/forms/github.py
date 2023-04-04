from worf.utils.forms import Form, Field
from worf.settings import settings
from worf.utils.forms.validators import (
    String,
    Optional,
    Required,
    EMail,
    Boolean,
    Equal,
    Choices,
    Regex,
)


class GithubForm(Form):
    code = Field([Required(), String()])
    state = Field([Required(), String()])
