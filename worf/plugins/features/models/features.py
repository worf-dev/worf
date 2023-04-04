from worf.models.base import Base, PkType
from sqlalchemy import Column, Unicode, ForeignKey

from sqlalchemy.dialects import postgresql
from sqlalchemy.orm import relationship, backref


class Features(Base):
    __tablename__ = "features"

    def export(self):
        return d

    @classmethod
    def get_or_create(cls, session, user, features):
        features = session.query(cls).filter(cls.user == user).one_or_none()
        if features is None:
            features = cls(user=user)
            session.add(features)
        return features

    user_id = Column(PkType, ForeignKey("user.id"), unique=True, nullable=False)
    features = Column(postgresql.ARRAY(Unicode, dimensions=1), nullable=False)

    user = relationship(
        "User",
        backref=backref("features", cascade="all,delete,delete-orphan", uselist=False),
    )
