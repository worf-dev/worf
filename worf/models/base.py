from sqlalchemy.orm import declarative_base
from sqlalchemy_utils import UUIDType, JSONType
from sqlalchemy import Column, DateTime, Unicode, BigInteger, Integer
from sqlalchemy.sql import func
from worf.settings import settings
from sqlalchemy.dialects import sqlite, postgresql
from sqlalchemy.orm.attributes import flag_modified
import sqlalchemy.types as types
import datetime


BigIntegerType = BigInteger()
BigIntegerType = BigIntegerType.with_variant(postgresql.BIGINT(), "postgresql")
BigIntegerType = BigIntegerType.with_variant(sqlite.INTEGER(), "sqlite")

DeclarativeBase = declarative_base()
PkType = BigIntegerType
ExtPkType = UUIDType(binary=False)

import uuid


class EncryptedData(types.TypeDecorator):

    """
    Transparently encrypt and decrypts structured data
    """

    impl = types.LargeBinary

    def process_bind_param(self, value, dialect):
        return settings.encrypt(value)

    def process_result_value(self, value, dialect):
        return settings.decrypt(value)


class Base(DeclarativeBase):  # type: ignore
    __abstract__ = True

    id = Column(PkType, primary_key=True)
    ext_id = Column(
        ExtPkType, default=lambda: uuid.uuid4(), nullable=False, unique=True
    )
    created_at = Column(DateTime(timezone=False), default=datetime.datetime.utcnow)
    updated_at = Column(DateTime(timezone=False), onupdate=datetime.datetime.utcnow)
    data = Column(JSONType, index=False, nullable=True)

    def set_data(self, key, value):
        if self.data is None:
            self.data = {}
        if value is None and key in self.data:
            del self.data[key]
        else:
            self.data[key] = value
        flag_modified(self, "data")

    def get_data(self, key):
        if self.data is None:
            return None
        return self.data.get(key)
