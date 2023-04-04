from worf.utils.forms import Form, Field
from worf.utils.forms.validators import ToLower, String, Required, EMail, UUID
from worf.api.v1.forms.validators import Code


class Password:
    def __call__(self, name, value, form):
        if len(value) < 8:
            return ["password is too short (minimum 8 characters)"], None, True


class SignupForm(Form):
    email = Field([Required(), String(), EMail(), ToLower()])
    password = Field([Required(), String(), Password()])


class AssociateForm(Form):
    password = Field([Required(), String(), Password()])


class ChangePasswordForm(Form):
    current_password = Field([Required(), String(), Password()])
    password = Field([Required(), String(), Password()])


class RequestPasswordResetForm(Form):
    email = Field([Required(), String(), EMail(), ToLower()])


class ResetPasswordForm(Form):
    password = Field([Required(), String(), Password()])
    id = Field([Required(), String(), UUID()])
    code = Field([Required(), String(), Code()])
