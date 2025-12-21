"""
Unit tests for core modules.

Tests for:
- Configuration settings
- Security utilities
- Password hashing
- JWT token handling
"""
from datetime import timedelta

import pytest


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

    def test_cors_origins_default_is_restrictive(self):
        """Test that default CORS origins is restrictive (not wildcard)."""
        from app.core.config import Settings

        settings = Settings()

        # Default should NOT contain wildcard
        assert "*" not in settings.CORS_ORIGINS
        # Default should be localhost for development
        assert any("localhost" in origin for origin in settings.CORS_ORIGINS)

    def test_cors_origins_wildcard_forbidden_in_production(self, monkeypatch):
        """Test that wildcard CORS is forbidden when DEBUG=False."""
        from app.core.config import Settings

        # Set production mode and wildcard CORS
        monkeypatch.setenv("DEBUG", "false")
        monkeypatch.setenv("CORS_ORIGINS", '["*"]')

        # Should raise ValueError in production
        with pytest.raises(ValueError, match="cannot contain wildcard"):
            Settings()

    def test_cors_origins_wildcard_allowed_in_debug(self, monkeypatch):
        """Test that wildcard CORS is allowed (with warning) when DEBUG=True."""
        from app.core.config import Settings

        # Set debug mode and wildcard CORS
        monkeypatch.setenv("DEBUG", "true")
        monkeypatch.setenv("CORS_ORIGINS", '["*"]')

        # Should succeed in debug mode (with warning)
        settings = Settings()
        assert "*" in settings.CORS_ORIGINS

    def test_cors_origins_multiple_explicit_allowed(self, monkeypatch):
        """Test that multiple explicit origins are allowed."""
        from app.core.config import Settings

        monkeypatch.setenv("DEBUG", "false")
        monkeypatch.setenv(
            "CORS_ORIGINS",
            '["https://scheduler.hospital.org","https://scheduler-staging.hospital.org"]'
        )

        settings = Settings()
        assert len(settings.CORS_ORIGINS) == 2
        assert "https://scheduler.hospital.org" in settings.CORS_ORIGINS

    def test_cors_origins_regex_support(self, monkeypatch):
        """Test that CORS_ORIGINS_REGEX is supported."""
        from app.core.config import Settings

        monkeypatch.setenv("CORS_ORIGINS_REGEX", r"^https://.*\.hospital\.org$")

        settings = Settings()
        assert settings.CORS_ORIGINS_REGEX == r"^https://.*\.hospital\.org$"


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
        import jwt

        from app.core.config import get_settings
        from app.core.security import create_access_token

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
        import jwt

        from app.core.config import get_settings
        from app.core.security import create_access_token

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


@pytest.mark.unit
class TestSecretValidation:
    """Test startup secret validation for all services."""

    def test_secret_key_rejects_weak_value_production(self, monkeypatch):
        """Test that SECRET_KEY rejects weak values in production."""
        from app.core.config import Settings

        monkeypatch.setenv("DEBUG", "false")
        monkeypatch.setenv("SECRET_KEY", "password")

        with pytest.raises(ValueError, match="known weak/default value"):
            Settings()

    def test_secret_key_rejects_short_value_production(self, monkeypatch):
        """Test that SECRET_KEY rejects short values in production."""
        from app.core.config import Settings

        monkeypatch.setenv("DEBUG", "false")
        monkeypatch.setenv("SECRET_KEY", "short")

        with pytest.raises(ValueError, match="at least 32 characters"):
            Settings()

    def test_secret_key_allows_weak_debug(self, monkeypatch, caplog):
        """Test that SECRET_KEY allows weak values in debug mode with warning."""
        from app.core.config import Settings

        monkeypatch.setenv("DEBUG", "true")
        monkeypatch.setenv("SECRET_KEY", "password_but_longer_than_32_characters_here")

        # Should succeed with warning
        settings = Settings()
        assert settings.SECRET_KEY == "password_but_longer_than_32_characters_here"

    def test_webhook_secret_rejects_weak_value_production(self, monkeypatch):
        """Test that WEBHOOK_SECRET rejects weak values in production."""
        from app.core.config import Settings

        monkeypatch.setenv("DEBUG", "false")
        monkeypatch.setenv("WEBHOOK_SECRET", "your-webhook-secret-change-in-production")

        with pytest.raises(ValueError, match="known weak/default value"):
            Settings()

    def test_redis_password_required_production(self, monkeypatch):
        """Test that REDIS_PASSWORD is required in production."""
        from app.core.config import Settings

        monkeypatch.setenv("DEBUG", "false")
        monkeypatch.setenv("REDIS_PASSWORD", "")

        with pytest.raises(ValueError, match="REDIS_PASSWORD must be set in production"):
            Settings()

    def test_redis_password_allows_empty_debug(self, monkeypatch):
        """Test that REDIS_PASSWORD allows empty in debug mode."""
        from app.core.config import Settings

        monkeypatch.setenv("DEBUG", "true")
        monkeypatch.setenv("REDIS_PASSWORD", "")

        # Should succeed in debug mode
        settings = Settings()
        assert settings.REDIS_PASSWORD == ""

    def test_redis_password_rejects_weak_production(self, monkeypatch):
        """Test that REDIS_PASSWORD rejects weak passwords in production."""
        from app.core.config import Settings

        monkeypatch.setenv("DEBUG", "false")
        monkeypatch.setenv("REDIS_PASSWORD", "password")

        with pytest.raises(ValueError, match="known weak/default value"):
            Settings()

    def test_redis_password_rejects_short_production(self, monkeypatch):
        """Test that REDIS_PASSWORD rejects short passwords in production."""
        from app.core.config import Settings

        monkeypatch.setenv("DEBUG", "false")
        monkeypatch.setenv("REDIS_PASSWORD", "short")

        with pytest.raises(ValueError, match="at least 16 characters"):
            Settings()

    def test_redis_password_allows_strong_production(self, monkeypatch):
        """Test that REDIS_PASSWORD allows strong passwords in production."""
        from app.core.config import Settings

        monkeypatch.setenv("DEBUG", "false")
        monkeypatch.setenv("REDIS_PASSWORD", "very_strong_random_password_here_123456")

        settings = Settings()
        assert settings.REDIS_PASSWORD == "very_strong_random_password_here_123456"

    def test_database_url_rejects_weak_password_production(self, monkeypatch):
        """Test that DATABASE_URL rejects weak passwords in production."""
        from app.core.config import Settings

        monkeypatch.setenv("DEBUG", "false")
        monkeypatch.setenv("DATABASE_URL", "postgresql://user:password@localhost:5432/db")

        with pytest.raises(ValueError, match="known weak/default password"):
            Settings()

    def test_database_url_rejects_default_scheduler_password_production(self, monkeypatch):
        """Test that DATABASE_URL rejects default 'scheduler' password in production."""
        from app.core.config import Settings

        monkeypatch.setenv("DEBUG", "false")
        monkeypatch.setenv("DATABASE_URL", "postgresql://scheduler:scheduler@localhost:5432/db")

        with pytest.raises(ValueError, match="known weak/default password"):
            Settings()

    def test_database_url_rejects_short_password_production(self, monkeypatch):
        """Test that DATABASE_URL rejects short passwords in production."""
        from app.core.config import Settings

        monkeypatch.setenv("DEBUG", "false")
        monkeypatch.setenv("DATABASE_URL", "postgresql://user:short@localhost:5432/db")

        with pytest.raises(ValueError, match="at least 12 characters"):
            Settings()

    def test_database_url_allows_weak_debug(self, monkeypatch):
        """Test that DATABASE_URL allows weak passwords in debug mode."""
        from app.core.config import Settings

        monkeypatch.setenv("DEBUG", "true")
        monkeypatch.setenv("DATABASE_URL", "postgresql://scheduler:scheduler@localhost:5432/db")

        # Should succeed in debug mode
        settings = Settings()
        assert "scheduler:scheduler" in settings.DATABASE_URL

    def test_database_url_allows_strong_production(self, monkeypatch):
        """Test that DATABASE_URL allows strong passwords in production."""
        from app.core.config import Settings

        monkeypatch.setenv("DEBUG", "false")
        monkeypatch.setenv(
            "DATABASE_URL",
            "postgresql://user:very_strong_db_password_123456@localhost:5432/db"
        )

        settings = Settings()
        assert "very_strong_db_password_123456" in settings.DATABASE_URL

    def test_database_url_requires_password(self, monkeypatch):
        """Test that DATABASE_URL requires a password."""
        from app.core.config import Settings

        monkeypatch.setenv("DEBUG", "false")
        monkeypatch.setenv("DATABASE_URL", "postgresql://user@localhost:5432/db")

        with pytest.raises(ValueError, match="must include a password"):
            Settings()

    def test_all_secrets_strong_production(self, monkeypatch):
        """Test that all secrets can be strong in production."""
        import secrets
        from app.core.config import Settings

        monkeypatch.setenv("DEBUG", "false")
        monkeypatch.setenv("SECRET_KEY", secrets.token_urlsafe(64))
        monkeypatch.setenv("WEBHOOK_SECRET", secrets.token_urlsafe(64))
        monkeypatch.setenv("REDIS_PASSWORD", secrets.token_urlsafe(32))
        monkeypatch.setenv(
            "DATABASE_URL",
            f"postgresql://user:{secrets.token_urlsafe(32)}@localhost:5432/db"
        )

        # Should succeed with all strong secrets
        settings = Settings()
        assert len(settings.SECRET_KEY) >= 32
        assert len(settings.WEBHOOK_SECRET) >= 32
        assert len(settings.REDIS_PASSWORD) >= 16
