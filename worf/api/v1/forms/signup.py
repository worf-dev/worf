from worf.utils.forms import Form, Field
from worf.utils.forms.validators import String, Required, Boolean, Optional, Dict
from .validators import Language, Code


class SignupForm(Form):
    language = Field([Required(), String(), Language()])
    trusted = Field([Optional(), Boolean(convert=True)])
    invitation = Field([Optional(), String(), Code()])
    extra_data = Field([Optional(), Dict()])
