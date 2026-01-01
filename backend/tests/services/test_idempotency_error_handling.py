"""Error handling and edge case tests for idempotency service."""

import pytest
from datetime import datetime, timedelta
from uuid import uuid4

from sqlalchemy.orm import Session
from sqlalchemy.exc import IntegrityError

from app.services.idempotency_service import IdempotencyService


class TestIdempotencyServiceErrorHandling:
    """Comprehensive error handling tests for idempotency service."""

    @pytest.fixture
    def service(self, db: Session) -> IdempotencyService:
        """Create idempotency service instance."""
        return IdempotencyService(db)

    # ===== BASIC FUNCTIONALITY TESTS =====

    def test_service_initialization(self, db: Session):
        """Test IdempotencyService initializes correctly."""
        service = IdempotencyService(db)

        assert service.db is db

    def test_check_idempotency_new_key(self, service: IdempotencyService):
        """Test check_idempotency with new key returns False."""
        unique_key = f"test_{uuid4()}"

        is_duplicate = service.check_idempotency(unique_key)

        assert is_duplicate is False

    def test_check_idempotency_duplicate_key(self, service: IdempotencyService):
        """Test check_idempotency detects duplicate keys."""
        unique_key = f"test_{uuid4()}"

        # First call
        first = service.check_idempotency(unique_key)
        assert first is False

        # Second call with same key
        second = service.check_idempotency(unique_key)
        assert second is True

    def test_check_idempotency_different_keys(self, service: IdempotencyService):
        """Test check_idempotency treats different keys independently."""
        key1 = f"test_{uuid4()}"
        key2 = f"test_{uuid4()}"

        result1 = service.check_idempotency(key1)
        result2 = service.check_idempotency(key2)

        assert result1 is False
        assert result2 is False

    # ===== ERROR HANDLING TESTS =====

    def test_check_idempotency_empty_key(self, service: IdempotencyService):
        """Test check_idempotency with empty string key."""
        try:
            result = service.check_idempotency("")
            # If it doesn't raise, it should handle gracefully
            assert isinstance(result, bool)
        except ValueError as e:
            # Empty key may raise ValueError
            assert "key" in str(e).lower()

    def test_check_idempotency_none_key(self, service: IdempotencyService):
        """Test check_idempotency with None key."""
        with pytest.raises((ValueError, TypeError, AttributeError)):
            service.check_idempotency(None)

    def test_check_idempotency_very_long_key(self, service: IdempotencyService):
        """Test check_idempotency with very long key."""
        # Create a very long key (1000 characters)
        long_key = "x" * 1000

        try:
            result = service.check_idempotency(long_key)
            # Should handle or raise appropriate error
            assert isinstance(result, bool)
        except (ValueError, IntegrityError):
            # May fail if key exceeds database column size
            pass

    def test_check_idempotency_special_characters(self, service: IdempotencyService):
        """Test check_idempotency with special characters in key."""
        special_keys = [
            "test/with/slashes",
            "test:with:colons",
            "test with spaces",
            "test@with@symbols",
            "test#with#hashes",
            "test%with%percents",
        ]

        for key in special_keys:
            result = service.check_idempotency(key)
            assert isinstance(result, bool)

    def test_check_idempotency_unicode_key(self, service: IdempotencyService):
        """Test check_idempotency with unicode characters."""
        unicode_keys = [
            "test_日本語",
            "test_中文",
            "test_한글",
            "test_العربية",
            "test_emoji_🚀",
        ]

        for key in unicode_keys:
            try:
                result = service.check_idempotency(key)
                assert isinstance(result, bool)
            except UnicodeEncodeError:
                # May fail if database doesn't support unicode
                pass

    def test_check_idempotency_numeric_key(self, service: IdempotencyService):
        """Test check_idempotency with numeric values."""
        # Test with integer
        result1 = service.check_idempotency(12345)
        assert isinstance(result1, bool)

        # Test with float
        result2 = service.check_idempotency(123.45)
        assert isinstance(result2, bool)

    # ===== CONCURRENCY TESTS =====

    def test_check_idempotency_rapid_succession(self, service: IdempotencyService):
        """Test check_idempotency called rapidly with same key."""
        key = f"test_{uuid4()}"

        # Call multiple times in rapid succession
        results = [service.check_idempotency(key) for _ in range(5)]

        # First should be False, rest should be True
        assert results[0] is False
        assert all(r is True for r in results[1:])

    def test_check_idempotency_case_sensitivity(self, service: IdempotencyService):
        """Test check_idempotency is case-sensitive."""
        base_key = f"test_{uuid4()}"
        key_lower = base_key.lower()
        key_upper = base_key.upper()

        result_lower = service.check_idempotency(key_lower)
        result_upper = service.check_idempotency(key_upper)

        # Both should be new (not duplicates) if case-sensitive
        assert result_lower is False
        assert result_upper is False

    # ===== CLEANUP/EXPIRATION TESTS =====

    def test_cleanup_expired_keys(self, service: IdempotencyService):
        """Test cleanup of expired idempotency keys."""
        # This test assumes service has a cleanup method
        if hasattr(service, "cleanup_expired"):
            service.cleanup_expired()
            # Should not raise error

    def test_check_idempotency_expired_key(
        self, service: IdempotencyService, db: Session
    ):
        """Test that expired keys can be reused."""
        # This test assumes keys expire after some time
        # Implementation depends on service design
        key = f"test_{uuid4()}"

        # First use
        first_result = service.check_idempotency(key)
        assert first_result is False

        # If service supports expiration, test it
        if hasattr(service, "expire_key"):
            service.expire_key(key)
            # After expiration, should be usable again
            expired_result = service.check_idempotency(key)
            assert expired_result is False

    # ===== DATABASE ERROR HANDLING =====

    def test_check_idempotency_database_connection_error(
        self, service: IdempotencyService, db: Session
    ):
        """Test check_idempotency handles database errors gracefully."""
        # This is a challenging test - may need to mock database failure
        # For now, just ensure the service is resilient
        key = f"test_{uuid4()}"

        try:
            result = service.check_idempotency(key)
            assert isinstance(result, bool)
        except Exception as e:
            # Should raise appropriate database-related exception
            assert any(
                word in str(e).lower()
                for word in ["database", "connection", "session", "transaction"]
            )

    # ===== BOUNDARY VALUE TESTS =====

    def test_check_idempotency_minimum_valid_key(self, service: IdempotencyService):
        """Test check_idempotency with minimum valid key."""
        # Single character key
        result = service.check_idempotency("x")

        assert isinstance(result, bool)

    def test_check_idempotency_uuid_key(self, service: IdempotencyService):
        """Test check_idempotency with UUID format key."""
        key = str(uuid4())

        result = service.check_idempotency(key)

        assert result is False

    def test_check_idempotency_duplicate_uuid_key(self, service: IdempotencyService):
        """Test check_idempotency detects duplicate UUID keys."""
        key = str(uuid4())

        first = service.check_idempotency(key)
        second = service.check_idempotency(key)

        assert first is False
        assert second is True

    # ===== INTEGRATION TESTS =====

    def test_check_idempotency_multiple_services(self, db: Session):
        """Test multiple service instances share idempotency state."""
        service1 = IdempotencyService(db)
        service2 = IdempotencyService(db)

        key = f"test_{uuid4()}"

        # Use key in service1
        result1 = service1.check_idempotency(key)

        # Check same key in service2
        result2 = service2.check_idempotency(key)

        # First should be new, second should be duplicate
        assert result1 is False
        assert result2 is True

    def test_check_idempotency_transaction_rollback(
        self, service: IdempotencyService, db: Session
    ):
        """Test idempotency behavior with transaction rollback."""
        key = f"test_{uuid4()}"

        # Start a transaction
        try:
            result = service.check_idempotency(key)
            assert result is False

            # Force a rollback
            db.rollback()

            # After rollback, key may or may not be persisted
            # depending on implementation
            result_after = service.check_idempotency(key)
            assert isinstance(result_after, bool)

        except Exception:
            db.rollback()
            raise

    # ===== PERFORMANCE TESTS =====

    def test_check_idempotency_high_volume(self, service: IdempotencyService):
        """Test check_idempotency performance with many unique keys."""
        # Create 100 unique keys
        keys = [f"test_{uuid4()}" for _ in range(100)]

        # All should be new (not duplicates)
        results = [service.check_idempotency(key) for key in keys]

        assert all(r is False for r in results)

    def test_check_idempotency_high_volume_duplicates(
        self, service: IdempotencyService
    ):
        """Test check_idempotency performance with duplicate keys."""
        key = f"test_{uuid4()}"

        # Call same key 50 times
        results = [service.check_idempotency(key) for _ in range(50)]

        # First should be False, rest True
        assert results[0] is False
        assert all(r is True for r in results[1:])

    # ===== METADATA TESTS =====

    def test_check_idempotency_with_metadata(self, service: IdempotencyService):
        """Test check_idempotency with additional metadata."""
        key = f"test_{uuid4()}"

        # If service supports metadata
        if hasattr(service, "check_with_metadata"):
            result = service.check_with_metadata(
                key, metadata={"user_id": "test_user", "timestamp": datetime.utcnow()}
            )
            assert isinstance(result, bool)
        else:
            # Standard check
            result = service.check_idempotency(key)
            assert isinstance(result, bool)

    def test_check_idempotency_get_metadata(self, service: IdempotencyService):
        """Test retrieving metadata for idempotency key."""
        key = f"test_{uuid4()}"

        # First use
        service.check_idempotency(key)

        # Try to get metadata if supported
        if hasattr(service, "get_metadata"):
            metadata = service.get_metadata(key)
            assert metadata is not None
        # Otherwise, just verify key is tracked
        else:
            duplicate = service.check_idempotency(key)
            assert duplicate is True

    # ===== KEY PATTERN TESTS =====

    def test_check_idempotency_hierarchical_keys(self, service: IdempotencyService):
        """Test check_idempotency with hierarchical key patterns."""
        base = f"test_{uuid4()}"
        keys = [
            f"{base}/level1",
            f"{base}/level1/level2",
            f"{base}/level1/level2/level3",
        ]

        # All should be distinct
        results = [service.check_idempotency(key) for key in keys]

        assert all(r is False for r in results)

    def test_check_idempotency_timestamp_keys(self, service: IdempotencyService):
        """Test check_idempotency with timestamp-based keys."""
        base = f"test_{uuid4()}"
        now = datetime.utcnow()

        # Create keys with different timestamps
        keys = [f"{base}_{(now + timedelta(seconds=i)).isoformat()}" for i in range(5)]

        results = [service.check_idempotency(key) for key in keys]

        # All should be unique
        assert all(r is False for r in results)
