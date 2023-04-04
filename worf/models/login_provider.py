from .base import Base
from sqlalchemy import Column, Unicode, ForeignKey, UniqueConstraint

from sqlalchemy.orm import relationship, backref


class LoginProvider(Base):
    __tablename__ = "login_provider"
    __table_args__ = (
        UniqueConstraint("provider_id", "provider", name="_provider_id_uc"),
    )

    provider_id = Column(Unicode, nullable=False)

    user_id = Column(ForeignKey("user.id"), nullable=False)  # type: ignore
    provider = Column(Unicode, nullable=False)
    user = relationship(
        "User", backref=backref("login_providers", cascade="all,delete,delete-orphan")
    )

    @classmethod
    def get_or_create(cls, session, provider, user, provider_id):
        prov = (
            session.query(cls)
            .filter(
                cls.provider == provider,
                cls.user == user,
                cls.provider_id == provider_id,
            )
            .one_or_none()
        )
        if prov is None:
            prov = cls(provider=provider, user=user, provider_id=provider_id)
            session.add(prov)
        return prov

    @classmethod
    def get_by_provider_id(cls, session, provider, provider_id):
        return (
            session.query(cls)
            .filter(cls.provider == provider, cls.provider_id == provider_id)
            .one_or_none()
        )

    def export(self):
        return {
            "id": self.ext_id,
            "data": self.data,
            "provider": self.provider,
            "provider_id": self.provider_id,
            "created_at": self.created_at,
            "updated_at": self.updated_at,
        }
