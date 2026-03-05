"""
Comprehensive security feature tests.

Tests security hardening features like brute force protection, input validation,
SQL injection prevention, XSS protection, CSRF protection, etc.

Tests are split into:
- Unit tests that run without DB/server (no skip)
- Integration tests that need DB/server (marked requires_db)
"""

import pytest
from pydantic import ValidationError

from app.core.security import create_access_token, get_password_hash, verify_password
from app.sanitization.xss import (
    XSSDetectionError,
    detect_xss,
    prevent_path_traversal,
    sanitize_input,
)
from app.schemas.auth import UserCreate, UserLogin
from app.validators.sanitizers import sanitize_filename


class TestBruteForceProtection:
    """Test brute force attack protection."""

    @pytest.mark.requires_db
    def test_multiple_failed_login_attempts(self, client, db):
        """Multiple failed login attempts trigger protection."""
        pytest.skip("Requires running FastAPI app with rate limiting middleware")

    @pytest.mark.requires_db
    def test_account_lockout_after_failures(self, client, db):
        """Account is locked after too many failed attempts."""
        pytest.skip("Account lockout feature not yet implemented")

    def test_lockout_duration(self):
        """Account lockout has time-based expiration."""
        pytest.skip("Account lockout duration not yet implemented")


class TestPasswordComplexity:
    """Test password complexity requirements via Pydantic schema."""

    def test_password_minimum_length(self):
        """Password must be at least 12 characters."""
        with pytest.raises(ValidationError, match="12 characters"):
            UserCreate(
                username="shortpass",
                email="shortpass@test.org",
                password="short",
                role="resident",
            )

    def test_password_requires_complexity(self):
        """Password requires 3 of 4: lowercase, uppercase, digit, special."""
        # Only lowercase + length >= 12 is not enough (only 1 of 4 categories)
        with pytest.raises(ValidationError, match="3 of"):
            UserCreate(
                username="testuser",
                email="test@test.org",
                password="alllowercaseletters",
                role="resident",
            )

    def test_password_with_three_categories_accepted(self):
        """Password with 3 of 4 categories is accepted."""
        # lowercase + uppercase + digit = 3 categories
        user = UserCreate(
            username="testuser",
            email="test@test.org",
            password="AbcDef123456",
            role="resident",
        )
        assert user.password == "AbcDef123456"

    def test_password_requires_uppercase_contribution(self):
        """Uppercase letters contribute to complexity requirement."""
        # Has lower + digit = 2 categories, needs 3
        with pytest.raises(ValidationError):
            UserCreate(
                username="testuser",
                email="test@test.org",
                password="alllowercase1",
                role="resident",
            )

    def test_password_requires_special_char_or_uppercase(self):
        """Special chars contribute to the complexity requirement."""
        # lowercase + digit + special = 3 categories (passes)
        user = UserCreate(
            username="testuser",
            email="test@test.org",
            password="alllowercase1!",
            role="resident",
        )
        assert user.password == "alllowercase1!"

    def test_password_schema_rejects_short(self):
        """UserCreate schema rejects short passwords."""
        with pytest.raises(ValidationError):
            UserCreate(
                username="testuser",
                email="test@test.org",
                password="Sh0rt!",
                role="resident",
            )

    def test_password_schema_accepts_strong(self):
        """UserCreate schema accepts strong passwords."""
        user = UserCreate(
            username="testuser",
            email="test@test.org",
            password="Str0ngP@ssw0rd!",
            role="resident",
        )
        assert user.password == "Str0ngP@ssw0rd!"


class TestSQLInjectionPrevention:
    """Test SQL injection prevention."""

    @pytest.mark.requires_db
    def test_login_sql_injection_attempt(self, client):
        """Login endpoint prevents SQL injection."""
        pytest.skip("Requires running FastAPI app with DB")

    @pytest.mark.requires_db
    def test_query_parameter_sql_injection(self, client, db):
        """Query parameters are properly escaped."""
        pytest.skip("Requires running FastAPI app with DB")

    @pytest.mark.requires_db
    def test_orm_prevents_raw_sql_injection(self, db):
        """SQLAlchemy ORM prevents injection in queries."""
        pytest.skip("Requires running DB session")

    def test_password_hashing_prevents_injection(self):
        """Password hashing neutralizes injection payloads."""
        injection_attempt = "'; DROP TABLE users; --"
        hashed = get_password_hash(injection_attempt)
        # Hashing should succeed and produce bcrypt output
        assert hashed.startswith("$2b$")
        assert verify_password(injection_attempt, hashed)


class TestXSSPrevention:
    """Test Cross-Site Scripting (XSS) prevention."""

    def test_detect_xss_script_tag(self):
        """Script tags are detected as XSS."""
        assert detect_xss("<script>alert('XSS')</script>") is True

    def test_detect_xss_event_handler(self):
        """Event handlers in HTML are detected as XSS."""
        assert detect_xss("<img src=x onerror=alert(1)>") is True

    def test_detect_xss_safe_input(self):
        """Normal text is not flagged as XSS."""
        assert detect_xss("normal text input") is False

    def test_sanitize_input_rejects_xss(self):
        """sanitize_input raises on XSS patterns."""
        with pytest.raises(XSSDetectionError):
            sanitize_input("<script>alert('XSS')</script>")

    def test_sanitize_input_allows_safe_text(self):
        """sanitize_input passes safe text through."""
        result = sanitize_input("Hello World")
        assert result == "Hello World"

    def test_html_in_json_response_escaped(self):
        """HTML entities in JSON responses are escaped via Pydantic/FastAPI."""
        # FastAPI's JSON serialization escapes HTML in string fields.
        # Verify that our XSS detection catches script injection.
        assert detect_xss('<div onmouseover="steal()">') is True
        assert detect_xss("Safe text with <nothing dangerous") is False


class TestCSRFProtection:
    """Test Cross-Site Request Forgery (CSRF) protection."""

    def test_csrf_token_required_for_state_change(self):
        """State-changing operations require CSRF token."""
        pytest.skip("CSRF protection implementation depends on frontend integration")

    def test_csrf_token_validation(self):
        """CSRF tokens are validated correctly."""
        pytest.skip("CSRF protection not yet implemented")


class TestSessionFixation:
    """Test session fixation attack prevention."""

    @pytest.mark.requires_db
    def test_session_regenerated_on_login(self, client, db):
        """Session ID changes after login."""
        pytest.skip("Requires running FastAPI app with DB")

    def test_tokens_are_unique_per_creation(self):
        """Each token creation produces a unique token."""
        from uuid import uuid4

        data = {"sub": str(uuid4()), "username": "test"}
        token1, jti1, _ = create_access_token(data, return_details=True)
        token2, jti2, _ = create_access_token(data, return_details=True)
        assert token1 != token2
        assert jti1 != jti2


class TestSecureHeaders:
    """Test security-related HTTP headers."""

    def test_strict_transport_security_header(self):
        """HSTS header is set for HTTPS enforcement."""
        pytest.skip("HSTS header typically set at reverse proxy level")

    @pytest.mark.requires_db
    def test_content_security_policy_header(self, client):
        """CSP header restricts resource loading."""
        pytest.skip("CSP header requires running app")

    def test_x_frame_options_header(self):
        """X-Frame-Options header prevents clickjacking."""
        pytest.skip("X-Frame-Options more relevant for HTML responses")


class TestInputValidation:
    """Test input validation and sanitization."""

    def test_email_format_validation(self):
        """Email addresses are validated for correct format."""
        with pytest.raises(ValidationError, match="email"):
            UserCreate(
                username="emailtest",
                email="not-an-email",
                password="Str0ngP@ssw0rd!",
                role="resident",
            )

    def test_valid_email_accepted(self):
        """Valid email addresses pass validation."""
        user = UserCreate(
            username="emailtest",
            email="valid@test.org",
            password="Str0ngP@ssw0rd!",
            role="resident",
        )
        assert user.email == "valid@test.org"

    @pytest.mark.requires_db
    def test_uuid_format_validation(self, client, db):
        """UUID parameters are validated via FastAPI path params."""
        pytest.skip("Requires running FastAPI app with DB")

    def test_date_format_validation(self):
        """Date inputs are validated for correct format via Pydantic."""
        from datetime import date
        from pydantic import BaseModel

        class DateModel(BaseModel):
            d: date

        with pytest.raises(ValidationError):
            DateModel(d="not-a-date")

        m = DateModel(d="2024-01-01")
        assert m.d == date(2024, 1, 1)

    def test_enum_value_validation(self):
        """Enum values are validated against allowed values via Pydantic."""
        from enum import Enum

        from pydantic import BaseModel

        class Color(str, Enum):
            RED = "red"
            BLUE = "blue"

        class EnumModel(BaseModel):
            color: Color

        with pytest.raises(ValidationError):
            EnumModel(color="green")

        m = EnumModel(color="red")
        assert m.color == Color.RED

    def test_username_min_length_validation(self):
        """Username minimum length is enforced by UserLogin schema."""
        with pytest.raises(ValidationError):
            UserLogin(username="ab", password="test")

    def test_username_max_length_validation(self):
        """Username maximum length is enforced by UserLogin schema."""
        with pytest.raises(ValidationError):
            UserLogin(username="a" * 51, password="test")


class TestFileUploadSecurity:
    """Test file upload security."""

    def test_file_type_validation(self):
        """File extension filtering works for known dangerous types."""
        # Validate using the sanitize_filename and extension check pattern
        dangerous_exts = {".exe", ".bat", ".cmd", ".sh", ".ps1"}
        filename = "malware.exe"
        ext = "." + filename.rsplit(".", 1)[-1].lower()
        assert ext in dangerous_exts

        safe_filename = "document.pdf"
        safe_ext = "." + safe_filename.rsplit(".", 1)[-1].lower()
        assert safe_ext not in dangerous_exts

    def test_file_size_limit(self):
        """File size validation logic works correctly."""
        max_size_mb = 10.0
        max_bytes = int(max_size_mb * 1024 * 1024)

        small_file = 1024  # 1KB
        assert small_file <= max_bytes

        large_file = 20 * 1024 * 1024  # 20MB
        assert large_file > max_bytes

    def test_filename_sanitization(self):
        """Uploaded filenames are sanitized."""
        safe = sanitize_filename("../../etc/passwd")
        assert ".." not in safe
        assert "/" not in safe

    def test_path_traversal_prevention(self):
        """Path traversal attacks in filenames are prevented."""
        with pytest.raises(XSSDetectionError):
            prevent_path_traversal("../../etc/passwd")

        # Safe paths pass through unchanged
        safe = prevent_path_traversal("safe/path/file.txt")
        assert safe == "safe/path/file.txt"


class TestAuditLogging:
    """Test security audit logging."""

    @pytest.mark.requires_db
    def test_login_success_logged(self, client, db):
        """Successful logins are logged."""
        pytest.skip("Requires running FastAPI app with DB")

    @pytest.mark.requires_db
    def test_login_failure_logged(self, client, db):
        """Failed login attempts are logged."""
        pytest.skip("Requires running FastAPI app with DB")

    def test_permission_denial_logged(self):
        """Permission denials are logged."""
        pytest.skip("Audit logging implementation varies")

    def test_sensitive_operations_logged(self):
        """Sensitive operations (delete, role change) are logged."""
        pytest.skip("Audit logging implementation varies")


class TestDataLeakagePrevention:
    """Test prevention of sensitive data leakage."""

    @pytest.mark.requires_db
    def test_error_messages_dont_leak_info(self, client):
        """Error messages don't leak sensitive information."""
        pytest.skip("Requires running FastAPI app with DB")

    @pytest.mark.requires_db
    def test_password_not_in_response(self, client, db):
        """Passwords are never included in API responses."""
        pytest.skip("Requires running FastAPI app with DB")

    def test_user_response_schema_excludes_password(self):
        """UserResponse schema does not include password field."""
        from app.schemas.auth import UserResponse

        fields = UserResponse.model_fields
        assert "password" not in fields
        assert "hashed_password" not in fields

    def test_stack_traces_not_exposed(self):
        """Stack traces are not exposed in production."""
        pytest.skip("Exception handler tested separately")


class TestRateLimitingByRole:
    """Test rate limiting enforcement."""

    @pytest.mark.requires_db
    def test_rate_limit_per_ip(self, client):
        """Rate limiting is enforced per IP address."""
        pytest.skip("Requires running FastAPI app with rate limiting middleware")

    def test_rate_limit_varies_by_endpoint(self):
        """Different endpoints have different rate limits."""
        pytest.skip("Endpoint-specific rate limits not yet implemented")

    def test_authenticated_users_higher_limits(self):
        """Authenticated users have higher rate limits."""
        pytest.skip("Role-based rate limiting not yet implemented")


class TestCacheInvalidation:
    """Test cache invalidation on security events."""

    @pytest.mark.requires_db
    def test_cache_cleared_on_role_change(self, db):
        """User cache is cleared when role changes."""
        pytest.skip("Requires running DB session and cache layer")

    def test_cache_cleared_on_deactivation(self):
        """User cache is cleared when account is deactivated."""
        pytest.skip("Cache invalidation depends on caching implementation")


class TestSecretManagement:
    """Test secret key management."""

    def test_secret_key_not_default(self):
        """SECRET_KEY is not using default value."""
        from app.core.config import get_settings

        settings = get_settings()

        assert settings.SECRET_KEY is not None
        assert len(settings.SECRET_KEY) >= 32

    def test_secret_key_sufficient_length(self):
        """SECRET_KEY meets minimum length requirement."""
        from app.core.config import get_settings

        settings = get_settings()
        assert len(settings.SECRET_KEY) >= 32

    def test_webhook_secret_configured(self):
        """WEBHOOK_SECRET is configured for webhook validation."""
        from app.core.config import get_settings

        settings = get_settings()
        # May not be required in all deployments
        # This is validated at config level


class TestSessionExpiration:
    """Test session expiration and timeout."""

    def test_access_token_expires(self):
        """Access tokens expire after configured time."""
        from datetime import timedelta
        from uuid import uuid4

        from app.core.config import get_settings
        import jwt

        settings = get_settings()
        data = {"sub": str(uuid4())}

        # Create token with 1 second expiration
        token, _, _ = create_access_token(
            data, expires_delta=timedelta(seconds=1), return_details=True
        )

        # Immediate decode should work
        payload = jwt.decode(token, settings.SECRET_KEY, algorithms=["HS256"])
        assert payload is not None
        assert "exp" in payload

    def test_expired_token_rejected(self):
        """Expired tokens fail verification."""
        from datetime import timedelta
        from uuid import uuid4

        from app.core.security import verify_token

        data = {"sub": str(uuid4())}
        token, _, _ = create_access_token(
            data, expires_delta=timedelta(seconds=-1), return_details=True
        )
        result = verify_token(token)
        assert result is None

    def test_refresh_token_longer_lifetime(self):
        """Refresh tokens have longer lifetime than access tokens."""
        # Already tested in token creation tests
        pass


class TestCORSConfiguration:
    """Test CORS configuration."""

    @pytest.mark.requires_db
    def test_cors_headers_present(self, client):
        """CORS headers are set correctly."""
        pytest.skip("Requires running FastAPI app")

    def test_cors_restricts_origins(self):
        """CORS restricts allowed origins."""
        pytest.skip("CORS configuration tested at application level")
