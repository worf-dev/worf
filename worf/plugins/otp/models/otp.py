from worf.models.base import Base, PkType
from sqlalchemy import Column, Unicode, ForeignKey, Boolean, UniqueConstraint

from sqlalchemy.orm import relationship, backref

import pyotp


class OTP(Base):
    __tablename__ = "otp"

    user_id = Column(PkType, ForeignKey("user.id"), nullable=False)
    enforce_otp = Column(Boolean, default=False, server_default="FALSE", nullable=False)
    otp_enabled = Column(Boolean, default=False, server_default="FALSE", nullable=False)
    otp_secret = Column(Unicode, nullable=True)
    new_otp_secret = Column(Unicode, nullable=True)
    otp_backup_codes = Column("otp_backup_codes", Unicode)

    # There can be only one entry for a given user
    UniqueConstraint("user_id", name="unique_user_id")
    user = relationship(
        "User", backref=backref("otp_tokens", cascade="all,delete,delete-orphan")
    )

    def generate_backup_code(self):
        return "".join(random.choice(string.digits) for i in range(6))

    def generate_otp_secret(self):
        chars = "".join("{}".format(i) for i in range(2, 8)) + string.ascii_lowercase
        return "".join(
            [random.choice(chars) for i in range(settings.get("otp.secret_length", 16))]
        )

    def get_otp_qr_code(self, token, format="PNG"):
        qr = qrcode.QRCode(version=1)
        qr.add_data(token)
        qr.make(fit=True)
        output = BytesIO()
        img = qr.make_image().save(output, format=format)
        img_string = output.getvalue()
        output.close()
        return img_string

    def validate_otp(self, code, use_new=False):
        return code == self.generate_otp(use_new=use_new)

    def generate_otp(self, use_new=False):
        if use_new:
            secret = self.new_otp_secret
        else:
            secret = self.otp_secret
        totp = pyotp.TOTP(secret)
        return totp.now()
