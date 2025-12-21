"""
Unit tests for FacultyConstraintService with caching.

Tests:
- FacultyPreferenceCache operations
- CachedFacultyPreferenceService caching behavior
- FacultyConstraintService authorization checks (IDOR prevention)
- Cache invalidation on preference updates
"""

import pytest
from datetime import date, timedelta
from unittest.mock import Mock, MagicMock, patch
from uuid import uuid4

from app.models.faculty_preference import FacultyPreference
from app.models.person import Person
from app.models.user import User
from app.services.constraints.faculty import (
    FacultyPreferenceCache,
    CachedFacultyPreferenceService,
    FacultyConstraintService,
    get_faculty_pref_cache,
)


class TestFacultyPreferenceCache:
    """Tests for the FacultyPreferenceCache class."""

    def test_cache_init_with_redis_unavailable(self):
        """Test cache falls back to local when Redis is unavailable."""
        with patch("app.services.constraints.faculty.redis") as mock_redis:
            mock_redis.from_url.side_effect = Exception("Connection failed")
            cache = FacultyPreferenceCache()
            assert cache._available is False

    def test_cache_set_and_get_preferences(self):
        """Test caching faculty preferences."""
        cache = FacultyPreferenceCache()

        faculty_id = uuid4()
        pref = FacultyPreference()
        pref.id = uuid4()
        pref.faculty_id = faculty_id
        pref.preferred_weeks = ["2025-01-06"]
        pref.blocked_weeks = ["2025-02-03"]
        pref.max_weeks_per_month = 2
        pref.max_consecutive_weeks = 1
        pref.min_gap_between_weeks = 2
        pref.target_weeks_per_year = 6
        pref.notify_swap_requests = True
        pref.notify_schedule_changes = True
        pref.notify_conflict_alerts = True
        pref.notify_reminder_days = 7
        pref.notes = "Test notes"

        cache.set_preferences(faculty_id, pref)
        cached = cache.get_preferences(faculty_id)

        assert cached is not None
        assert cached["faculty_id"] == str(faculty_id)
        assert cached["preferred_weeks"] == ["2025-01-06"]
        assert cached["blocked_weeks"] == ["2025-02-03"]

    def test_cache_week_blocked_status(self):
        """Test caching blocked week status."""
        cache = FacultyPreferenceCache()
        faculty_id = uuid4()
        week_date = date(2025, 1, 6)

        cache.set_week_blocked(faculty_id, week_date, True)
        result = cache.is_week_blocked(faculty_id, week_date)

        assert result is True

    def test_cache_week_preferred_status(self):
        """Test caching preferred week status."""
        cache = FacultyPreferenceCache()
        faculty_id = uuid4()
        week_date = date(2025, 1, 6)

        cache.set_week_preferred(faculty_id, week_date, True)
        result = cache.is_week_preferred(faculty_id, week_date)

        assert result is True

    def test_cache_invalidate_faculty(self):
        """Test invalidating cache for a specific faculty member."""
        cache = FacultyPreferenceCache()
        faculty_id = uuid4()
        week_date = date(2025, 1, 6)

        # Set some values
        cache.set_week_blocked(faculty_id, week_date, True)
        cache.set_week_preferred(faculty_id, week_date, False)

        # Invalidate
        deleted = cache.invalidate_faculty(faculty_id)

        # Verify cleared
        assert cache.is_week_blocked(faculty_id, week_date) is None
        assert cache.is_week_preferred(faculty_id, week_date) is None

    def test_cache_invalidate_all(self):
        """Test clearing all cache entries."""
        cache = FacultyPreferenceCache()
        faculty_id1 = uuid4()
        faculty_id2 = uuid4()
        week_date = date(2025, 1, 6)

        # Set values for multiple faculty
        cache.set_week_blocked(faculty_id1, week_date, True)
        cache.set_week_blocked(faculty_id2, week_date, False)

        # Clear all
        deleted = cache.invalidate_all()

        # Verify all cleared
        assert cache.is_week_blocked(faculty_id1, week_date) is None
        assert cache.is_week_blocked(faculty_id2, week_date) is None


class TestCachedFacultyPreferenceService:
    """Tests for CachedFacultyPreferenceService."""

    @pytest.fixture
    def mock_db(self):
        """Create a mock database session."""
        return MagicMock()

    @pytest.fixture
    def mock_cache(self):
        """Create a mock cache."""
        return MagicMock(spec=FacultyPreferenceCache)

    def test_get_preferences_from_cache(self, mock_db, mock_cache):
        """Test getting preferences from cache."""
        faculty_id = uuid4()
        cached_data = {
            "id": str(uuid4()),
            "faculty_id": str(faculty_id),
            "preferred_weeks": ["2025-01-06"],
            "blocked_weeks": [],
            "max_weeks_per_month": 2,
            "max_consecutive_weeks": 1,
            "min_gap_between_weeks": 2,
            "target_weeks_per_year": 6,
            "notify_swap_requests": True,
            "notify_schedule_changes": True,
            "notify_conflict_alerts": True,
            "notify_reminder_days": 7,
            "notes": None,
        }
        mock_cache.get_preferences.return_value = cached_data

        service = CachedFacultyPreferenceService(mock_db, mock_cache)
        result = service.get_preferences(faculty_id)

        assert result is not None
        assert result.preferred_weeks == ["2025-01-06"]
        mock_db.query.assert_not_called()  # Should not hit DB

    def test_get_preferences_cache_miss(self, mock_db, mock_cache):
        """Test getting preferences when not in cache."""
        faculty_id = uuid4()
        mock_cache.get_preferences.return_value = None

        # Mock database query
        mock_pref = FacultyPreference()
        mock_pref.id = uuid4()
        mock_pref.faculty_id = faculty_id
        mock_pref.preferred_weeks = ["2025-02-03"]
        mock_pref.blocked_weeks = []

        mock_query = MagicMock()
        mock_query.filter.return_value.first.return_value = mock_pref
        mock_db.query.return_value = mock_query

        service = CachedFacultyPreferenceService(mock_db, mock_cache)
        result = service.get_preferences(faculty_id)

        assert result is not None
        mock_cache.set_preferences.assert_called_once()

    def test_is_week_blocked_cached(self, mock_db, mock_cache):
        """Test is_week_blocked with cached value."""
        faculty_id = uuid4()
        week_date = date(2025, 1, 6)
        mock_cache.is_week_blocked.return_value = True

        service = CachedFacultyPreferenceService(mock_db, mock_cache)
        result = service.is_week_blocked(faculty_id, week_date)

        assert result is True
        mock_db.query.assert_not_called()


class TestFacultyConstraintService:
    """Tests for FacultyConstraintService authorization."""

    @pytest.fixture
    def mock_db(self):
        """Create a mock database session."""
        return MagicMock()

    @pytest.fixture
    def admin_user(self):
        """Create an admin user."""
        user = User()
        user.id = uuid4()
        user.email = "admin@test.org"
        user.role = "admin"
        return user

    @pytest.fixture
    def faculty_user(self):
        """Create a faculty user."""
        user = User()
        user.id = uuid4()
        user.email = "faculty@test.org"
        user.role = "faculty"
        return user

    def test_get_authorized_faculty_id(self, mock_db, faculty_user):
        """Test getting authorized faculty ID from user."""
        faculty_id = uuid4()

        # Mock finding the faculty
        mock_faculty = Person()
        mock_faculty.id = faculty_id
        mock_faculty.email = faculty_user.email
        mock_faculty.type = "faculty"

        mock_query = MagicMock()
        mock_query.filter.return_value.first.return_value = mock_faculty
        mock_db.query.return_value = mock_query

        service = FacultyConstraintService(mock_db)
        result = service.get_authorized_faculty_id(faculty_user)

        assert result == faculty_id

    def test_get_authorized_faculty_id_not_faculty(self, mock_db, faculty_user):
        """Test getting faculty ID when user is not a faculty member."""
        mock_query = MagicMock()
        mock_query.filter.return_value.first.return_value = None
        mock_db.query.return_value = mock_query

        service = FacultyConstraintService(mock_db)
        result = service.get_authorized_faculty_id(faculty_user)

        assert result is None

    def test_validate_faculty_access_admin(self, mock_db, admin_user):
        """Test admin can access any faculty data (IDOR check)."""
        faculty_id = uuid4()

        service = FacultyConstraintService(mock_db)
        result = service.validate_faculty_access(admin_user, faculty_id)

        assert result is True

    def test_validate_faculty_access_own_data(self, mock_db, faculty_user):
        """Test faculty can access their own data."""
        faculty_id = uuid4()

        # Mock getting authorized faculty ID
        mock_faculty = Person()
        mock_faculty.id = faculty_id
        mock_faculty.email = faculty_user.email
        mock_faculty.type = "faculty"

        mock_query = MagicMock()
        mock_query.filter.return_value.first.return_value = mock_faculty
        mock_db.query.return_value = mock_query

        service = FacultyConstraintService(mock_db)
        result = service.validate_faculty_access(faculty_user, faculty_id)

        assert result is True

    def test_validate_faculty_access_other_data_blocked(self, mock_db, faculty_user):
        """Test faculty cannot access other faculty's data (IDOR prevention)."""
        own_faculty_id = uuid4()
        other_faculty_id = uuid4()

        # Mock getting authorized faculty ID (returns own ID)
        mock_faculty = Person()
        mock_faculty.id = own_faculty_id
        mock_faculty.email = faculty_user.email
        mock_faculty.type = "faculty"

        mock_query = MagicMock()
        mock_query.filter.return_value.first.return_value = mock_faculty
        mock_db.query.return_value = mock_query

        service = FacultyConstraintService(mock_db)
        result = service.validate_faculty_access(faculty_user, other_faculty_id)

        assert result is False  # IDOR blocked

    def test_get_preferences_with_authorization(self, mock_db, faculty_user):
        """Test getting preferences with authorization check."""
        own_faculty_id = uuid4()
        other_faculty_id = uuid4()

        # Mock getting authorized faculty ID
        mock_faculty = Person()
        mock_faculty.id = own_faculty_id
        mock_faculty.email = faculty_user.email
        mock_faculty.type = "faculty"

        mock_query = MagicMock()
        mock_query.filter.return_value.first.return_value = mock_faculty
        mock_db.query.return_value = mock_query

        service = FacultyConstraintService(mock_db)

        # Should return None for unauthorized access
        result = service.get_preferences_for_constraint(other_faculty_id, faculty_user)
        assert result is None

    def test_check_week_availability(self, mock_db):
        """Test checking week availability."""
        faculty_id = uuid4()
        week_date = date(2025, 1, 6)

        # Mock preferences
        mock_pref = FacultyPreference()
        mock_pref.faculty_id = faculty_id
        mock_pref.blocked_weeks = ["2025-01-06"]
        mock_pref.preferred_weeks = []
        mock_pref.max_weeks_per_month = 2
        mock_pref.max_consecutive_weeks = 1
        mock_pref.min_gap_between_weeks = 2

        with patch.object(CachedFacultyPreferenceService, 'is_week_blocked', return_value=True):
            with patch.object(CachedFacultyPreferenceService, 'is_week_preferred', return_value=False):
                with patch.object(CachedFacultyPreferenceService, 'get_preferences', return_value=mock_pref):
                    service = FacultyConstraintService(mock_db)
                    result = service.check_week_availability(faculty_id, week_date)

        assert result["is_blocked"] is True
        assert result["is_preferred"] is False
        assert "max_weeks_per_month" in result["constraints"]
