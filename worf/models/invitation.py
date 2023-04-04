from .base import Base, PkType
from sqlalchemy import Column, Unicode, UnicodeText, ForeignKey, DateTime, Boolean
from sqlalchemy.orm import relationship, backref

import datetime
import uuid


class Invitation(Base):

    """
    Describes an invitation to use our service
    """

    __tablename__ = "invitation"

    message = Column(UnicodeText, nullable=True, index=False)
    inviting_user_id = Column(PkType, ForeignKey("user.id"), nullable=False)
    invited_user_id = Column(PkType, ForeignKey("user.id"), nullable=True)
    accepted_at = Column(DateTime, nullable=True)
    valid_until = Column(DateTime, nullable=True)
    token = Column(Unicode, nullable=False, default=lambda: uuid.uuid4().hex)
    valid = Column(Boolean, nullable=False, default=True)
    sent = Column(Boolean, nullable=False, default=False)
    email = Column(Unicode, nullable=False, unique=True)
    # we can tie the invitation to a specific e-mail as well
    tied_to_email = Column(Boolean, nullable=False, default=False)

    inviting_user = relationship(
        "User",
        backref=backref("invitations", cascade="all,delete,delete-orphan"),
        foreign_keys=[inviting_user_id],
    )
    invited_user = relationship(
        "User",
        backref=backref("accepted_invitations", cascade="all,delete,delete-orphan"),
        foreign_keys=[invited_user_id],
    )

    @property
    def is_valid(self):
        return (
            True
            if self.valid
            and (
                self.valid_until is None
                or self.valid_until > datetime.datetime.utcnow()
            )
            else False
        )

    @classmethod
    def get_by_email(cls, session, email):
        return session.query(cls).filter(cls.email == email).one_or_none()

    @classmethod
    def get_by_ext_id(cls, session, ext_id):
        return session.query(cls).filter(cls.ext_id == ext_id).one_or_none()

    @classmethod
    def get_by_token(cls, session, token):
        return session.query(cls).filter(cls.token == token).one_or_none()

    @classmethod
    def filter_by_type(cls, session, invitation_type):
        return session.query(cls).filter(cls.invitation_type == invitation_type)

    @classmethod
    def get(cls, session, token):
        return session.query(cls).filter(cls.token == token).one_or_none()

    def export(self, with_token=False):
        d = {
            "id": self.ext_id,
            "valid": self.valid,
            "data": self.data,
            "valid_until": self.valid_until,
            "created_at": self.created_at,
            "accepted_at": self.accepted_at,
            "email": self.email,
            "tied_to_email": self.tied_to_email,
            "message": self.message,
            "inviting_user": self.inviting_user.export(),
            "invited_user": self.invited_user.export()
            if self.invited_user is not None
            else None,
        }
        if with_token:
            d["token"] = self.token
        return d
