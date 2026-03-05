"""Tests for field-level encryption types."""

import os
from unittest.mock import MagicMock

import pytest


class TestEncryptedString:
    def setup_method(self):
        # Reset cached fernet between tests
        from app.db.types import EncryptedString

        EncryptedString._fernet = None
        EncryptedString._warned = False

    def test_roundtrip(self):
        from app.db.types import EncryptedString

        col = EncryptedString()
        dialect = MagicMock()
        encrypted = col.process_bind_param("secret data", dialect)
        assert encrypted != "secret data"
        assert isinstance(encrypted, str)

        decrypted = col.process_result_value(encrypted, dialect)
        assert decrypted == "secret data"

    def test_none_passthrough(self):
        from app.db.types import EncryptedString

        col = EncryptedString()
        dialect = MagicMock()
        assert col.process_bind_param(None, dialect) is None
        assert col.process_result_value(None, dialect) is None

    def test_unicode(self):
        from app.db.types import EncryptedString

        col = EncryptedString()
        dialect = MagicMock()
        text = "日本語テスト 🏥"
        encrypted = col.process_bind_param(text, dialect)
        decrypted = col.process_result_value(encrypted, dialect)
        assert decrypted == text

    def test_explicit_key(self, monkeypatch):
        from cryptography.fernet import Fernet

        from app.db.types import EncryptedString

        key = Fernet.generate_key().decode()
        monkeypatch.setenv("FIELD_ENCRYPTION_KEY", key)
        EncryptedString._fernet = None

        col = EncryptedString()
        dialect = MagicMock()
        encrypted = col.process_bind_param("test", dialect)
        decrypted = col.process_result_value(encrypted, dialect)
        assert decrypted == "test"


class TestEncryptedJSON:
    def setup_method(self):
        from app.db.types import EncryptedString

        EncryptedString._fernet = None
        EncryptedString._warned = False

    def test_roundtrip(self):
        from app.db.types import EncryptedJSON

        col = EncryptedJSON()
        dialect = MagicMock()
        data = {"question_1": "answer_a", "score": 42, "nested": [1, 2, 3]}

        encrypted = col.process_bind_param(data, dialect)
        assert isinstance(encrypted, str)
        assert "question_1" not in encrypted  # encrypted, not plaintext

        decrypted = col.process_result_value(encrypted, dialect)
        assert decrypted == data

    def test_none_passthrough(self):
        from app.db.types import EncryptedJSON

        col = EncryptedJSON()
        dialect = MagicMock()
        assert col.process_bind_param(None, dialect) is None
        assert col.process_result_value(None, dialect) is None
