from ..forms.otp import ActivateOTPForm, OTPForm
from worf.api.decorators.user import authorized

from worf.api.resource import Resource
from worf.settings import settings
from urllib.parse import quote_plus

try:
    import pyotp

    otp_enabled = True
except ImportError:
    otp_enabled = False


def with_otp(f):
    def decorator(*args, **kwargs):
        if not otp_enabled:
            return {"message": "OTP is not enabled"}, 500
        return f(*args, **kwargs)

    return decorator


class ActivateOTP(Resource):
    @with_otp
    @authorized(scopes=("admin",))
    def post(self):
        with settings.session() as session:
            form = ActivateOTPForm(request.get_json())

            if not form.validate():
                return {"message": "invalid data", "errors": form.errors}, 400

            if not request.user.validate_otp(form.otp.data, use_new=True):
                return {"message": "failed to validate the OTP token"}, 400

            request.user.otp_secret = request.user.new_otp_secret
            request.user.new_otp_secret = None
            request.user.otp_enabled = True

            request.user.otp_backup_codes = [
                request.user.generate_backup_code() for i in range(10)
            ]

            session.add(request.user)

            return {"backup_codes": request.user.otp_backup_codes}, 201


class OTP(Resource):
    def get_otp_info(self, secret, email):
        d = {
            "user": email,
            "secret": secret,
            "issuer": quote_plus(settings.get("company.name")),
            "algorithm": settings.get("otp.algorithm", "SHA1"),
            "period": settings.get("otp.period", 30),
            "digits": settings.get("otp.digits", 6),
        }
        token = (
            "otpauth://totp/{user}?secret={secret}&issuer={issuer}"
            "&algorithm={algorithm}&digits={digits}&period={period}".format(**d)
        )
        qr_code = request.user.get_otp_qr_code(token)
        return {
            "otp": {
                "token": token,
                "secret": secret,
                "qr_code": base64.b64encode(qr_code).decode("ascii"),
            }
        }

    @with_otp
    @authorized(scopes=("admin",))
    def delete(self):
        """
        Resets/removes the OTP secrets.
        """
        with settings.session() as session:
            form = OTPForm(request.get_json())

            if not form.validate():
                return {"message": "invalid data", "errors": form.errors}, 400

            if not request.user.check_password(form.password.data):
                return (
                    {
                        "message": "authentication error",
                        "errors": {"password": "invalid password"},
                    },
                    400,
                )

            if request.user.enforce_otp:
                return (
                    {
                        "message": "cannot disable OTP because"
                        " policy enforces it for you"
                    },
                    401,
                )

            request.user.otp_enabled = False
            session.add(request.user)

            return {"message": "otp was successfully disabled."}, 200

    @with_otp
    @authorized(scopes=("admin",))
    def post(self):
        """
        Returns the current OTP secrets.
        """

        with settings.session() as session:
            form = OTPForm(request.get_json())

            if not form.validate():
                return {"message": "invalid data", "errors": form.errors}, 400

            if not request.user.check_password(form.password.data):
                return (
                    {
                        "message": "authentication error",
                        "errors": {"password": "invalid password"},
                    },
                    400,
                )

            info = self.get_otp_info(request.user.otp_secret, request.user.email)
            info["otp"]["backup_codes"] = request.user.otp_backup_codes
            return info, 200

    @with_otp
    @authorized(scopes=("admin",))
    def put(self):
        """
        Creates new OTP secrets.
        """

        with settings.session() as session:
            form = OTPForm(request.get_json())

            if not form.validate():
                return {"message": "invalid data", "errors": form.errors}, 400

            if not request.user.check_password(form.password.data):
                return (
                    {
                        "message": "authentication error",
                        "errors": {"password": "invalid password"},
                    },
                    400,
                )

            request.user.new_otp_secret = request.user.generate_otp_secret()
            session.add(request.user)

            return (
                self.get_otp_info(request.user.new_otp_secret, request.user.email),
                201,
            )
