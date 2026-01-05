"""Test suite for the impersonation service.

Tests the ImpersonationService class which handles the business logic for
user impersonation, allowing administrators to temporarily assume the
identity of other users for troubleshooting and support purposes.

Security Test Coverage:
- Only admins can impersonate
- Cannot self-impersonate
- Cannot impersonate inactive users
- Short-lived tokens
- Full audit trail via ActivityLog
- Token blacklisting on end-impersonation
"""

from datetime import datetime, timedelta
from uuid import uuid4

import pytest
from jose import jwt
from sqlalchemy.orm import Session

from app.core.config import get_settings
from app.core.security import ALGORITHM, get_password_hash
from app.models.activity_log import ActivityActionType, ActivityLog
from app.models.token_blacklist import TokenBlacklist
from app.models.user import User
from app.services.impersonation_service import (
    IMPERSONATION_TOKEN_TTL_MINUTES,
    ImpersonationForbiddenError,
    ImpersonationService,
    ImpersonationTokenError,
)

settings = get_settings()


class TestImpersonationService:
    """Test suite for the ImpersonationService class."""

    @pytest.fixture
    def impersonation_service(self, db: Session) -> ImpersonationService:
        """Create an impersonation service instance."""
        return ImpersonationService(db)

    @pytest.fixture
    def admin_user_for_impersonation(self, db: Session) -> User:
        """Create an admin user for impersonation tests."""
        user = User(
            id=uuid4(),
            username="impersonate_admin",
            email="impersonate_admin@test.org",
            hashed_password=get_password_hash("Admin@Pass123"),
            role="admin",
            is_active=True,
        )
        db.add(user)
        db.commit()
        db.refresh(user)
        return user

    @pytest.fixture
    def regular_user(self, db: Session) -> User:
        """Create a regular (non-admin) user."""
        user = User(
            id=uuid4(),
            username="regular_user",
            email="regular_user@test.org",
            hashed_password=get_password_hash("User@Pass123"),
            role="coordinator",
            is_active=True,
        )
        db.add(user)
        db.commit()
        db.refresh(user)
        return user

    @pytest.fixture
    def target_user(self, db: Session) -> User:
        """Create a target user to be impersonated."""
        user = User(
            id=uuid4(),
            username="target_user",
            email="target_user@test.org",
            hashed_password=get_password_hash("Target@Pass123"),
            role="resident",
            is_active=True,
        )
        db.add(user)
        db.commit()
        db.refresh(user)
        return user

    @pytest.fixture
    def inactive_user(self, db: Session) -> User:
        """Create an inactive user."""
        user = User(
            id=uuid4(),
            username="inactive_user",
            email="inactive_user@test.org",
            hashed_password=get_password_hash("Inactive@Pass123"),
            role="resident",
            is_active=False,
        )
        db.add(user)
        db.commit()
        db.refresh(user)
        return user

    # ========================================================================
    # Start Impersonation Tests
    # ========================================================================

    def test_start_impersonation_success(
        self,
        impersonation_service: ImpersonationService,
        admin_user_for_impersonation: User,
        target_user: User,
    ):
        """Test that admin can successfully impersonate another user."""
        result = impersonation_service.start_impersonation(
            admin_user=admin_user_for_impersonation,
            target_user_id=target_user.id,
            ip_address="192.168.1.100",
            user_agent="Test Browser/1.0",
        )

        assert result.impersonation_token is not None
        assert isinstance(result.impersonation_token, str)
        assert result.impersonation_token.count(".") == 2  # Valid JWT format
        assert result.target_user.id == target_user.id
        assert result.target_user.username == target_user.username
        assert result.expires_at is not None
        assert result.expires_at > datetime.utcnow()

    def test_start_impersonation_self_forbidden(
        self,
        impersonation_service: ImpersonationService,
        admin_user_for_impersonation: User,
    ):
        """Test that admin cannot impersonate themselves."""
        with pytest.raises(ImpersonationForbiddenError) as exc_info:
            impersonation_service.start_impersonation(
                admin_user=admin_user_for_impersonation,
                target_user_id=admin_user_for_impersonation.id,
            )

        assert "Cannot impersonate yourself" in str(exc_info.value)

    def test_start_impersonation_inactive_user_forbidden(
        self,
        impersonation_service: ImpersonationService,
        admin_user_for_impersonation: User,
        inactive_user: User,
    ):
        """Test that admin cannot impersonate inactive users."""
        with pytest.raises(ImpersonationForbiddenError) as exc_info:
            impersonation_service.start_impersonation(
                admin_user=admin_user_for_impersonation,
                target_user_id=inactive_user.id,
            )

        assert "Cannot impersonate inactive users" in str(exc_info.value)

    def test_start_impersonation_non_admin_forbidden(
        self,
        impersonation_service: ImpersonationService,
        regular_user: User,
        target_user: User,
    ):
        """Test that non-admin users cannot impersonate others."""
        with pytest.raises(ImpersonationForbiddenError) as exc_info:
            impersonation_service.start_impersonation(
                admin_user=regular_user,
                target_user_id=target_user.id,
            )

        assert "Only administrators can impersonate" in str(exc_info.value)

    def test_start_impersonation_target_not_found(
        self,
        impersonation_service: ImpersonationService,
        admin_user_for_impersonation: User,
    ):
        """Test that impersonation fails when target user doesn't exist."""
        nonexistent_id = uuid4()

        with pytest.raises(ValueError) as exc_info:
            impersonation_service.start_impersonation(
                admin_user=admin_user_for_impersonation,
                target_user_id=nonexistent_id,
            )

        assert "Target user not found" in str(exc_info.value)

    # ========================================================================
    # End Impersonation Tests
    # ========================================================================

    def test_end_impersonation_success(
        self,
        impersonation_service: ImpersonationService,
        admin_user_for_impersonation: User,
        target_user: User,
        db: Session,
    ):
        """Test that impersonation session can be ended successfully."""
        # Start impersonation
        start_result = impersonation_service.start_impersonation(
            admin_user=admin_user_for_impersonation,
            target_user_id=target_user.id,
        )

        # End impersonation
        end_result = impersonation_service.end_impersonation(
            token=start_result.impersonation_token,
            ip_address="192.168.1.100",
            user_agent="Test Browser/1.0",
        )

        assert end_result is True

        # Verify token is blacklisted
        payload = jwt.decode(
            start_result.impersonation_token,
            settings.SECRET_KEY,
            algorithms=[ALGORITHM],
        )
        jti = payload.get("jti")
        assert TokenBlacklist.is_blacklisted(db, jti) is True

    def test_end_impersonation_invalid_token(
        self,
        impersonation_service: ImpersonationService,
    ):
        """Test that ending impersonation with invalid token fails gracefully."""
        invalid_token = "invalid.jwt.token"

        with pytest.raises(ImpersonationTokenError) as exc_info:
            impersonation_service.end_impersonation(token=invalid_token)

        assert "Invalid or expired token" in str(exc_info.value)

    def test_end_impersonation_already_ended(
        self,
        impersonation_service: ImpersonationService,
        admin_user_for_impersonation: User,
        target_user: User,
    ):
        """Test that ending an already-ended impersonation returns True."""
        # Start impersonation
        start_result = impersonation_service.start_impersonation(
            admin_user=admin_user_for_impersonation,
            target_user_id=target_user.id,
        )

        # End impersonation twice
        first_end = impersonation_service.end_impersonation(
            token=start_result.impersonation_token
        )
        second_end = impersonation_service.end_impersonation(
            token=start_result.impersonation_token
        )

        assert first_end is True
        assert second_end is True  # Should still return True

    # ========================================================================
    # Impersonation Status Tests
    # ========================================================================

    def test_get_impersonation_status_active(
        self,
        impersonation_service: ImpersonationService,
        admin_user_for_impersonation: User,
        target_user: User,
    ):
        """Test that status correctly shows when impersonating."""
        # Start impersonation
        start_result = impersonation_service.start_impersonation(
            admin_user=admin_user_for_impersonation,
            target_user_id=target_user.id,
        )

        # Get status
        status = impersonation_service.get_impersonation_status(
            token=start_result.impersonation_token
        )

        assert status.is_impersonating is True
        assert status.target_user is not None
        assert status.target_user.id == target_user.id
        assert status.original_user is not None
        assert status.original_user.id == admin_user_for_impersonation.id
        assert status.expires_at is not None

    def test_get_impersonation_status_not_impersonating(
        self,
        impersonation_service: ImpersonationService,
    ):
        """Test that status shows not impersonating for invalid token."""
        # Status with invalid token
        status = impersonation_service.get_impersonation_status(
            token="invalid.jwt.token"
        )

        assert status.is_impersonating is False
        assert status.target_user is None
        assert status.original_user is None

    def test_get_impersonation_status_after_end(
        self,
        impersonation_service: ImpersonationService,
        admin_user_for_impersonation: User,
        target_user: User,
    ):
        """Test that status shows not impersonating after session ended."""
        # Start impersonation
        start_result = impersonation_service.start_impersonation(
            admin_user=admin_user_for_impersonation,
            target_user_id=target_user.id,
        )

        # End impersonation
        impersonation_service.end_impersonation(
            token=start_result.impersonation_token
        )

        # Get status
        status = impersonation_service.get_impersonation_status(
            token=start_result.impersonation_token
        )

        assert status.is_impersonating is False

    # ========================================================================
    # Verify Impersonation Token Tests
    # ========================================================================

    def test_verify_impersonation_token_valid(
        self,
        impersonation_service: ImpersonationService,
        admin_user_for_impersonation: User,
        target_user: User,
    ):
        """Test that valid token returns correct users."""
        # Start impersonation
        start_result = impersonation_service.start_impersonation(
            admin_user=admin_user_for_impersonation,
            target_user_id=target_user.id,
        )

        # Verify token
        result = impersonation_service.verify_impersonation_token(
            token=start_result.impersonation_token
        )

        assert result is not None
        assert len(result) == 2
        verified_target, verified_admin = result
        assert verified_target.id == target_user.id
        assert verified_admin.id == admin_user_for_impersonation.id

    def test_verify_impersonation_token_expired(
        self,
        impersonation_service: ImpersonationService,
        db: Session,
        admin_user_for_impersonation: User,
        target_user: User,
    ):
        """Test that expired token returns None."""
        # Create an already-expired token
        import uuid

        expires_at = datetime.utcnow() - timedelta(minutes=1)
        jti = str(uuid.uuid4())

        token_payload = {
            "sub": str(target_user.id),
            "username": target_user.username,
            "type": "impersonation",
            "original_admin_id": str(admin_user_for_impersonation.id),
            "target_user_id": str(target_user.id),
            "exp": expires_at,
            "iat": datetime.utcnow() - timedelta(minutes=31),
            "jti": jti,
        }

        expired_token = jwt.encode(
            token_payload, settings.SECRET_KEY, algorithm=ALGORITHM
        )

        # Verify token - should return None due to expiration
        result = impersonation_service.verify_impersonation_token(token=expired_token)

        assert result is None

    def test_verify_impersonation_token_blacklisted(
        self,
        impersonation_service: ImpersonationService,
        admin_user_for_impersonation: User,
        target_user: User,
    ):
        """Test that blacklisted token returns None."""
        # Start impersonation
        start_result = impersonation_service.start_impersonation(
            admin_user=admin_user_for_impersonation,
            target_user_id=target_user.id,
        )

        # End impersonation (which blacklists the token)
        impersonation_service.end_impersonation(
            token=start_result.impersonation_token
        )

        # Verify blacklisted token
        result = impersonation_service.verify_impersonation_token(
            token=start_result.impersonation_token
        )

        assert result is None

    def test_verify_impersonation_token_non_impersonation_type(
        self,
        impersonation_service: ImpersonationService,
    ):
        """Test that non-impersonation token type returns None."""
        # Create a regular access token (not impersonation type)
        token_payload = {
            "sub": str(uuid4()),
            "type": "access",  # Not "impersonation"
            "exp": datetime.utcnow() + timedelta(minutes=30),
        }

        regular_token = jwt.encode(
            token_payload, settings.SECRET_KEY, algorithm=ALGORITHM
        )

        result = impersonation_service.verify_impersonation_token(token=regular_token)

        assert result is None

    # ========================================================================
    # Audit Log Tests
    # ========================================================================

    def test_impersonation_audit_log_created(
        self,
        impersonation_service: ImpersonationService,
        admin_user_for_impersonation: User,
        target_user: User,
        db: Session,
    ):
        """Test that ActivityLog entry is created when impersonation starts."""
        # Start impersonation
        impersonation_service.start_impersonation(
            admin_user=admin_user_for_impersonation,
            target_user_id=target_user.id,
            ip_address="192.168.1.100",
            user_agent="Test Browser/1.0",
        )

        # Query for the activity log
        log_entry = (
            db.query(ActivityLog)
            .filter(
                ActivityLog.action_type == ActivityActionType.IMPERSONATION_STARTED.value
            )
            .filter(ActivityLog.user_id == admin_user_for_impersonation.id)
            .order_by(ActivityLog.created_at.desc())
            .first()
        )

        assert log_entry is not None
        assert log_entry.target_entity == "User"
        assert log_entry.target_id == str(target_user.id)
        assert log_entry.ip_address == "192.168.1.100"
        assert log_entry.user_agent == "Test Browser/1.0"
        assert "admin_username" in log_entry.details
        assert "target_username" in log_entry.details
        assert "expires_at" in log_entry.details
        assert "jti" in log_entry.details

    def test_end_impersonation_audit_log_created(
        self,
        impersonation_service: ImpersonationService,
        admin_user_for_impersonation: User,
        target_user: User,
        db: Session,
    ):
        """Test that ActivityLog entry is created when impersonation ends."""
        # Start impersonation
        start_result = impersonation_service.start_impersonation(
            admin_user=admin_user_for_impersonation,
            target_user_id=target_user.id,
        )

        # End impersonation
        impersonation_service.end_impersonation(
            token=start_result.impersonation_token,
            ip_address="192.168.1.100",
            user_agent="Test Browser/1.0",
        )

        # Query for the activity log
        log_entry = (
            db.query(ActivityLog)
            .filter(
                ActivityLog.action_type == ActivityActionType.IMPERSONATION_ENDED.value
            )
            .filter(ActivityLog.user_id == admin_user_for_impersonation.id)
            .order_by(ActivityLog.created_at.desc())
            .first()
        )

        assert log_entry is not None
        assert log_entry.target_entity == "User"
        assert log_entry.target_id == str(target_user.id)
        assert log_entry.ip_address == "192.168.1.100"
        assert log_entry.user_agent == "Test Browser/1.0"
        assert "jti" in log_entry.details
        assert "ended_at" in log_entry.details

    # ========================================================================
    # Token TTL Tests
    # ========================================================================

    def test_impersonation_token_has_correct_ttl(
        self,
        impersonation_service: ImpersonationService,
        admin_user_for_impersonation: User,
        target_user: User,
    ):
        """Test that impersonation token has correct TTL (30 minutes)."""
        # Start impersonation
        result = impersonation_service.start_impersonation(
            admin_user=admin_user_for_impersonation,
            target_user_id=target_user.id,
        )

        # Decode token to check expiration
        payload = jwt.decode(
            result.impersonation_token,
            settings.SECRET_KEY,
            algorithms=[ALGORITHM],
        )

        exp_timestamp = payload.get("exp")
        iat_timestamp = payload.get("iat")

        assert exp_timestamp is not None
        assert iat_timestamp is not None

        # Calculate TTL
        exp_datetime = datetime.utcfromtimestamp(exp_timestamp)
        iat_datetime = datetime.utcfromtimestamp(iat_timestamp)
        ttl_minutes = (exp_datetime - iat_datetime).total_seconds() / 60

        # Allow some tolerance for timing differences
        assert abs(ttl_minutes - IMPERSONATION_TOKEN_TTL_MINUTES) < 1

    def test_impersonation_token_has_required_claims(
        self,
        impersonation_service: ImpersonationService,
        admin_user_for_impersonation: User,
        target_user: User,
    ):
        """Test that impersonation token contains all required claims."""
        # Start impersonation
        result = impersonation_service.start_impersonation(
            admin_user=admin_user_for_impersonation,
            target_user_id=target_user.id,
        )

        # Decode token
        payload = jwt.decode(
            result.impersonation_token,
            settings.SECRET_KEY,
            algorithms=[ALGORITHM],
        )

        # Verify required claims
        assert payload.get("sub") == str(target_user.id)
        assert payload.get("username") == target_user.username
        assert payload.get("type") == "impersonation"
        assert payload.get("original_admin_id") == str(admin_user_for_impersonation.id)
        assert payload.get("target_user_id") == str(target_user.id)
        assert payload.get("jti") is not None
        assert payload.get("exp") is not None
        assert payload.get("iat") is not None

    # ========================================================================
    # Edge Case Tests
    # ========================================================================

    def test_verify_token_with_missing_admin(
        self,
        impersonation_service: ImpersonationService,
        db: Session,
        admin_user_for_impersonation: User,
        target_user: User,
    ):
        """Test verification when original admin no longer exists."""
        # Start impersonation
        start_result = impersonation_service.start_impersonation(
            admin_user=admin_user_for_impersonation,
            target_user_id=target_user.id,
        )

        # Delete the admin user
        db.delete(admin_user_for_impersonation)
        db.commit()

        # Verify token - should return None because admin doesn't exist
        result = impersonation_service.verify_impersonation_token(
            token=start_result.impersonation_token
        )

        assert result is None

    def test_verify_token_with_inactive_target(
        self,
        impersonation_service: ImpersonationService,
        db: Session,
        admin_user_for_impersonation: User,
        target_user: User,
    ):
        """Test verification when target user becomes inactive."""
        # Start impersonation
        start_result = impersonation_service.start_impersonation(
            admin_user=admin_user_for_impersonation,
            target_user_id=target_user.id,
        )

        # Make target user inactive
        target_user.is_active = False
        db.commit()

        # Verify token - should return None because target is inactive
        result = impersonation_service.verify_impersonation_token(
            token=start_result.impersonation_token
        )

        assert result is None

    def test_verify_token_when_admin_loses_admin_role(
        self,
        impersonation_service: ImpersonationService,
        db: Session,
        admin_user_for_impersonation: User,
        target_user: User,
    ):
        """Test verification when original admin loses admin privileges."""
        # Start impersonation
        start_result = impersonation_service.start_impersonation(
            admin_user=admin_user_for_impersonation,
            target_user_id=target_user.id,
        )

        # Demote admin to regular user
        admin_user_for_impersonation.role = "coordinator"
        db.commit()

        # Verify token - should return None because admin is no longer admin
        result = impersonation_service.verify_impersonation_token(
            token=start_result.impersonation_token
        )

        assert result is None
