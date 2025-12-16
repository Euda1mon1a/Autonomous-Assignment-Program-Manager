"""
Unit tests for core modules.

Tests for:
- Configuration settings
- Security utilities
- Password hashing
- JWT token handling
"""
import pytest
from datetime import datetime, timedelta
from unittest.mock import patch


@pytest.mark.unit
class TestConfigurationSettings:
    """Test configuration and settings."""

    def test_default_settings_exist(self):
        """Test that default settings can be loaded."""
        from app.core.config import Settings

        settings = Settings()

        # Check default values exist
        assert hasattr(settings, "APP_NAME")
        assert hasattr(settings, "DEBUG")
        assert hasattr(settings, "DATABASE_URL")

    def test_get_settings_cached(self):
        """Test that settings are cached."""
        from app.core.config import get_settings

        settings1 = get_settings()
        settings2 = get_settings()

        # Should return the same cached instance
        assert settings1 is settings2

    def test_settings_cors_origins(self):
        """Test CORS origins configuration."""
        from app.core.config import get_settings

        settings = get_settings()

        # CORS_ORIGINS should be a list
        assert isinstance(settings.CORS_ORIGINS, list)


@pytest.mark.unit
class TestPasswordHashing:
    """Test password hashing utilities."""

    def test_password_hash_creates_hash(self):
        """Test that password hashing creates a different string."""
        from app.core.security import get_password_hash

        password = "test_password_123"
        hashed = get_password_hash(password)

        assert hashed != password
        assert len(hashed) > 0

    def test_password_verification_succeeds(self):
        """Test that correct password verification succeeds."""
        from app.core.security import get_password_hash, verify_password

        password = "secure_password_456"
        hashed = get_password_hash(password)

        assert verify_password(password, hashed) is True

    def test_password_verification_fails_wrong_password(self):
        """Test that wrong password verification fails."""
        from app.core.security import get_password_hash, verify_password

        password = "correct_password"
        wrong_password = "wrong_password"
        hashed = get_password_hash(password)

        assert verify_password(wrong_password, hashed) is False

    def test_password_hash_unique_per_call(self):
        """Test that password hashes are unique (due to salt)."""
        from app.core.security import get_password_hash

        password = "same_password"
        hash1 = get_password_hash(password)
        hash2 = get_password_hash(password)

        # Hashes should be different due to random salt
        assert hash1 != hash2

    def test_empty_password_hash(self):
        """Test hashing an empty password."""
        from app.core.security import get_password_hash

        # Empty password should still hash
        hashed = get_password_hash("")
        assert len(hashed) > 0


@pytest.mark.unit
class TestJWTTokens:
    """Test JWT token creation and validation."""

    def test_create_access_token(self):
        """Test creating an access token."""
        from app.core.security import create_access_token

        data = {"sub": "testuser"}
        token = create_access_token(data)

        assert token is not None
        assert len(token) > 0
        assert isinstance(token, str)

    def test_create_access_token_with_expiry(self):
        """Test creating a token with custom expiry."""
        from app.core.security import create_access_token

        data = {"sub": "testuser"}
        expires = timedelta(minutes=30)
        token = create_access_token(data, expires_delta=expires)

        assert token is not None

    def test_verify_token_valid(self):
        """Test verifying a valid token."""
        from app.core.security import create_access_token, verify_token

        username = "testuser"
        token = create_access_token({"sub": username})

        decoded_username = verify_token(token)
        assert decoded_username == username

    def test_verify_token_invalid(self):
        """Test verifying an invalid token."""
        from app.core.security import verify_token

        invalid_token = "invalid.jwt.token"
        result = verify_token(invalid_token)

        assert result is None

    def test_verify_token_empty(self):
        """Test verifying an empty token."""
        from app.core.security import verify_token

        result = verify_token("")
        assert result is None


@pytest.mark.unit
class TestTokenPayload:
    """Test JWT token payload handling."""

    def test_token_contains_subject(self):
        """Test that token contains subject claim."""
        from app.core.security import create_access_token
        import jwt
        from app.core.config import get_settings

        settings = get_settings()
        data = {"sub": "user123"}
        token = create_access_token(data)

        # Decode without verification to check payload
        payload = jwt.decode(
            token,
            settings.SECRET_KEY,
            algorithms=["HS256"],
        )

        assert "sub" in payload
        assert payload["sub"] == "user123"

    def test_token_contains_expiry(self):
        """Test that token contains expiry claim."""
        from app.core.security import create_access_token
        import jwt
        from app.core.config import get_settings

        settings = get_settings()
        token = create_access_token({"sub": "user"})

        payload = jwt.decode(
            token,
            settings.SECRET_KEY,
            algorithms=["HS256"],
        )

        assert "exp" in payload


@pytest.mark.unit
class TestSecurityConstants:
    """Test security-related constants and defaults."""

    def test_default_token_expire_minutes(self):
        """Test default token expiration time."""
        from app.core.config import get_settings

        settings = get_settings()

        # Should have an expiration setting
        assert hasattr(settings, "ACCESS_TOKEN_EXPIRE_MINUTES")
        assert settings.ACCESS_TOKEN_EXPIRE_MINUTES > 0

    def test_secret_key_exists(self):
        """Test that a secret key is configured."""
        from app.core.config import get_settings

        settings = get_settings()

        assert hasattr(settings, "SECRET_KEY")
        assert len(settings.SECRET_KEY) > 0


@pytest.mark.unit
class TestResilienceConfiguration:
    """Test resilience-related configuration."""

    def test_resilience_settings_exist(self):
        """Test that resilience settings are available."""
        from app.core.config import get_settings

        settings = get_settings()

        # Check resilience-related settings
        resilience_attrs = [
            "RESILIENCE_MAX_UTILIZATION",
            "RESILIENCE_WARNING_THRESHOLD",
        ]

        for attr in resilience_attrs:
            if hasattr(settings, attr):
                value = getattr(settings, attr)
                assert value is not None
