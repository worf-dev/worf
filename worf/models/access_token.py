from .base import Base, PkType
from sqlalchemy import (
    Column,
    Unicode,
    UnicodeText,
    ForeignKey,
    DateTime,
    Integer,
    Boolean,
)
from sqlalchemy.orm import relationship, backref

import uuid


class AccessToken(Base):

    """
    Describes an access token for a given user.
    """

    __tablename__ = "access_token"

    description = Column(UnicodeText, nullable=True, index=False)
    user_id = Column(PkType, ForeignKey("user.id"), nullable=False)
    last_used_at = Column(DateTime, nullable=True)
    valid_until = Column(DateTime, nullable=True)
    default_expiration_minutes = Column(Integer, nullable=True)
    scopes = Column(Unicode, nullable=False)
    last_used_from = Column(Unicode, nullable=True)
    token = Column(Unicode, nullable=False, default=lambda: uuid.uuid4().hex)
    valid = Column(Boolean, nullable=False, default=True)
    renews_when_used = Column(Boolean, nullable=False, default=True)

    user = relationship(
        "User", backref=backref("access_tokens", cascade="all,delete,delete-orphan")
    )

    def has_scope(self, scope):
        return scope in self.scopes.split(",")

    def export(self, with_token=False):
        d = {
            "id": self.ext_id,
            "valid_until": self.valid_until,
            "last_used_at": self.last_used_at,
            "last_used_from": self.last_used_from,
            "created_at": self.created_at,
            "scopes": self.scopes.split(","),
            "data": self.data,
            "description": self.description,
            "renews_when_used": self.renews_when_used,
        }
        if with_token:
            d["token"] = self.token
        return d
