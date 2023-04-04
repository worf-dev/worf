from .base import Base

from sqlalchemy import Column, Unicode, Boolean


class User(Base):
    __tablename__ = "user"

    # WARNING: These fields are user-editable, do not rely on the data that's stored in them
    # for security-critical functionality!
    display_name = Column(Unicode(30), nullable=True)
    email = Column(Unicode, nullable=True, unique=True)
    language = Column(Unicode, server_default="en", nullable=False)

    superuser = Column(Boolean, default=False, server_default="FALSE", nullable=False)
    account_verified = Column(
        Boolean, default=False, server_default="FALSE", nullable=False
    )
    new_email = Column(Unicode, nullable=True)
    email_change_code = Column(Unicode, nullable=True)

    disabled = Column(Boolean, default=False, server_default="FALSE", nullable=False)

    def export(self, full=True):
        return {
            "email": self.email if full else "",
            "id": self.ext_id,
            "data": self.data if full else "",
            "display_name": self.display_name if full else "",
            "disabled": self.disabled,
            "new_email": self.new_email if full else "",
            "superuser": self.superuser,
            "created_at": self.created_at,
            "updated_at": self.updated_at,
            "language": self.language,
        }

    @classmethod
    def get_by_email(cls, session, email):
        return session.query(User).filter(User.email == email).one_or_none()

    @classmethod
    def get_by_ext_id(cls, session, ext_id):
        return session.query(User).filter(User.ext_id == ext_id).one_or_none()
