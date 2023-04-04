from worf.models.base import Base
from sqlalchemy import Column, Unicode, Boolean

import hashlib


class CryptoToken(Base):
    __tablename__ = "crypto_token"

    hash = Column(Unicode, nullable=False, unique=True)
    used = Column(Boolean, nullable=False, default=False)

    @classmethod
    def get_hash(cls, token):
        return hashlib.sha256(token.encode("utf-8")).hexdigest()

    @classmethod
    def get(cls, session, hash):
        return session.query(cls).filter(cls.hash == hash).one_or_none()

    @classmethod
    def get_or_create(cls, session, hash):
        existing_token = cls.get(session, hash)
        if existing_token is not None:
            return existing_token
        token = cls(hash=hash)
        session.add(token)
        return token
