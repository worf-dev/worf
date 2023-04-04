from worf.utils.forms import Form, Field
from worf.utils.forms.validators import String, Required

import re


class OTP:
    def __call__(self, name, value, form):
        if not re.match(r"^\d{6,12}$", value):
            return ["invalid OTP token"], None, True


class ActivateOTPForm(Form):
    otp = Field([Required(), String(), OTP()])


class OTPForm(Form):
    password = Field([String()])
