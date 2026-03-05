"""Cross-database compatible type definitions.

These types work with both PostgreSQL (production) and SQLite (testing).
"""

import json
import logging
import os
import uuid

from sqlalchemy import String, Text
from sqlalchemy.dialects.postgresql import ARRAY as PG_ARRAY
from sqlalchemy.dialects.postgresql import JSONB as PG_JSONB
from sqlalchemy.dialects.postgresql import UUID as PG_UUID
from sqlalchemy.types import CHAR, TypeDecorator

logger = logging.getLogger(__name__)


class GUID(TypeDecorator):
    """
    Platform-independent GUID type.

    Uses PostgreSQL's UUID type when available, otherwise uses CHAR(36)
    for SQLite or other databases.
    """

    impl = CHAR
    cache_ok = True

    def load_dialect_impl(self, dialect):
        if dialect.name == "postgresql":
            return dialect.type_descriptor(PG_UUID(as_uuid=True))
        else:
            return dialect.type_descriptor(CHAR(36))

    def process_bind_param(self, value, dialect):
        if value is None or dialect.name == "postgresql":
            return value
        else:
            if isinstance(value, uuid.UUID):
                return str(value)
            return value

    def process_result_value(self, value, dialect):
        if value is None or dialect.name == "postgresql":
            return value
        else:
            if not isinstance(value, uuid.UUID):
                return uuid.UUID(value)
            return value


class JSONType(TypeDecorator):
    """
    Platform-independent JSON type.

    Uses PostgreSQL's JSONB type when available, otherwise uses TEXT
    with JSON serialization for SQLite.
    """

    impl = Text
    cache_ok = True

    def load_dialect_impl(self, dialect):
        if dialect.name == "postgresql":
            return dialect.type_descriptor(PG_JSONB())
        else:
            return dialect.type_descriptor(Text())

    def process_bind_param(self, value, dialect):
        if value is None or dialect.name == "postgresql":
            return value
        else:
            return json.dumps(value)

    def process_result_value(self, value, dialect):
        if value is None or dialect.name == "postgresql":
            return value
        else:
            if isinstance(value, str):
                return json.loads(value)
            return value


class StringArrayType(TypeDecorator):
    """
    Platform-independent array of strings type.

    Uses PostgreSQL's ARRAY type when available, otherwise uses TEXT
    with JSON serialization for SQLite.
    """

    impl = Text
    cache_ok = True

    def load_dialect_impl(self, dialect):
        if dialect.name == "postgresql":
            return dialect.type_descriptor(PG_ARRAY(String))
        else:
            return dialect.type_descriptor(Text())

    def process_bind_param(self, value, dialect):
        if value is None or dialect.name == "postgresql":
            return value
        else:
            return json.dumps(value)

    def process_result_value(self, value, dialect):
        if value is None or dialect.name == "postgresql":
            return value
        else:
            if isinstance(value, str):
                return json.loads(value)
            return value


class EncryptedString(TypeDecorator):
    """
    Field-level encryption using Fernet symmetric encryption.

    Transparently encrypts on write and decrypts on read. Stored as
    base64-encoded ciphertext in a Text column.

    Key source: FIELD_ENCRYPTION_KEY env var (Fernet key, base64-encoded 32 bytes).
    Generates ephemeral key with warning if not set (development only).

    Generate a production key:
        python -c 'from cryptography.fernet import Fernet; print(Fernet.generate_key().decode())'
    """

    impl = Text
    cache_ok = True

    _fernet = None
    _warned = False

    @classmethod
    def _get_fernet(cls):
        if cls._fernet is not None:
            return cls._fernet

        from cryptography.fernet import Fernet

        key = os.environ.get("FIELD_ENCRYPTION_KEY")
        if key:
            cls._fernet = Fernet(key.encode() if isinstance(key, str) else key)
        else:
            if not cls._warned:
                logger.warning(
                    "FIELD_ENCRYPTION_KEY not set — generating ephemeral key. "
                    "Data will NOT survive process restarts. Set this in production."
                )
                cls._warned = True
            cls._fernet = Fernet(Fernet.generate_key())

        return cls._fernet

    def process_bind_param(self, value, dialect):
        if value is None:
            return None
        f = self._get_fernet()
        return f.encrypt(value.encode("utf-8")).decode("utf-8")

    def process_result_value(self, value, dialect):
        if value is None:
            return None
        f = self._get_fernet()
        return f.decrypt(value.encode("utf-8")).decode("utf-8")


class EncryptedJSON(TypeDecorator):
    """
    Field-level encryption for JSON data.

    Serializes to JSON, then encrypts. Stored as encrypted Text.
    Uses the same Fernet key as EncryptedString.
    """

    impl = Text
    cache_ok = True

    def process_bind_param(self, value, dialect):
        if value is None:
            return None
        plaintext = json.dumps(value)
        f = EncryptedString._get_fernet()
        return f.encrypt(plaintext.encode("utf-8")).decode("utf-8")

    def process_result_value(self, value, dialect):
        if value is None:
            return None
        f = EncryptedString._get_fernet()
        plaintext = f.decrypt(value.encode("utf-8")).decode("utf-8")
        return json.loads(plaintext)
