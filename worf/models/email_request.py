from worf.models.base import Base
from sqlalchemy import Column, Unicode, Boolean, Integer, DateTime, UniqueConstraint

import datetime
import hashlib

from sqlalchemy.sql import and_


class EMailRequest(Base):
    __tablename__ = "email_request"

    email_hash = Column(Unicode, nullable=False, unique=False)
    last_request_at = Column(DateTime, nullable=True)
    purpose = Column(Unicode, nullable=False)
    total_requests = Column(Integer, index=False, nullable=False, default=0)
    blocked = Column(Boolean, nullable=False, default=False)

    __table_args__ = (
        UniqueConstraint("purpose", "email_hash", name="unique_email_purpose"),
    )

    @classmethod
    def get_sha256(cls, email=None, sha256=None):
        return hashlib.sha256(email.lower().strip().encode("utf-8")).hexdigest()

    @classmethod
    def request(cls, session, purpose, email):
        request = cls.get_or_create(session, purpose, email=email)
        if request.blocked:
            return False
        if request.total_requests >= 4:
            return False
        if (
            request.last_request_at is not None
            and (datetime.datetime.utcnow() - request.last_request_at).total_seconds()
            < 60 * 60
        ):
            return False
        request.total_requests += 1
        request.last_request_at = datetime.datetime.utcnow()
        return True

    @classmethod
    def generate_encrypted_block_code(cls, settings, purpose, email):
        block_data = {"sha256": cls.get_sha256(email), "purpose": purpose}
        return settings.encrypt(block_data).decode("ascii")

    @classmethod
    def reset(cls, session, purpose, email):
        request = cls.get(session, purpose, email=email)
        if not request:
            return
        request.last_request_at = None
        request.total_requests = 0

    @classmethod
    def get(cls, session, purpose, email=None, sha256=None):
        if sha256 is None:
            if email is None:
                raise ValueError("email or sha256 must be given!")
            sha256 = cls.get_sha256(email)
        return (
            session.query(cls)
            .filter(and_(cls.email_hash == sha256, cls.purpose == purpose))
            .one_or_none()
        )

    @classmethod
    def get_or_create(cls, session, purpose, email=None, sha256=None):
        if sha256 is None:
            if email is None:
                raise ValueError("email or sha256 must be given!")
            sha256 = cls.get_sha256(email)
        existing_request = cls.get(session, purpose, sha256=sha256)
        if existing_request is not None:
            return existing_request
        request = cls(
            email_hash=sha256, total_requests=0, blocked=False, purpose=purpose
        )
        session.add(request)
        return request
