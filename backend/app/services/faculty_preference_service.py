"""Service for managing faculty FMIT scheduling preferences."""
from datetime import date, datetime
from typing import List, Optional
from uuid import UUID, uuid4

from sqlalchemy.orm import Session

from app.models.faculty_preference import FacultyPreference
from app.models.person import Person


class FacultyPreferenceService:
    """
    Service for managing faculty FMIT scheduling preferences.

    Handles CRUD operations and preference validation for faculty
    self-service portal.
    """

    def __init__(self, db: Session):
        self.db = db

    def get_or_create_preferences(self, faculty_id: UUID) -> FacultyPreference:
        """
        Get existing preferences or create default ones.

        Args:
            faculty_id: The faculty member's ID

        Returns:
            FacultyPreference record (existing or newly created)
        """
        preferences = self.db.query(FacultyPreference).filter(
            FacultyPreference.faculty_id == faculty_id
        ).first()

        if not preferences:
            # Verify faculty exists
            faculty = self.db.query(Person).filter(
                Person.id == faculty_id,
                Person.type == "faculty"
            ).first()

            if not faculty:
                raise ValueError(f"Faculty {faculty_id} not found")

            preferences = FacultyPreference(
                id=uuid4(),
                faculty_id=faculty_id,
                preferred_weeks=[],
                blocked_weeks=[],
                max_weeks_per_month=2,
                max_consecutive_weeks=1,
                min_gap_between_weeks=2,
                target_weeks_per_year=6,
                notify_swap_requests=True,
                notify_schedule_changes=True,
                notify_conflict_alerts=True,
                notify_reminder_days=7,
            )
            self.db.add(preferences)
            self.db.commit()
            self.db.refresh(preferences)

        return preferences

    def update_preferences(
        self,
        faculty_id: UUID,
        preferred_weeks: Optional[List[str]] = None,
        blocked_weeks: Optional[List[str]] = None,
        max_weeks_per_month: Optional[int] = None,
        max_consecutive_weeks: Optional[int] = None,
        min_gap_between_weeks: Optional[int] = None,
        notify_swap_requests: Optional[bool] = None,
        notify_schedule_changes: Optional[bool] = None,
        notify_conflict_alerts: Optional[bool] = None,
        notify_reminder_days: Optional[int] = None,
        notes: Optional[str] = None,
    ) -> FacultyPreference:
        """
        Update faculty preferences.

        Only updates fields that are provided (not None).
        """
        preferences = self.get_or_create_preferences(faculty_id)

        if preferred_weeks is not None:
            preferences.preferred_weeks = preferred_weeks
        if blocked_weeks is not None:
            preferences.blocked_weeks = blocked_weeks
        if max_weeks_per_month is not None:
            preferences.max_weeks_per_month = max_weeks_per_month
        if max_consecutive_weeks is not None:
            preferences.max_consecutive_weeks = max_consecutive_weeks
        if min_gap_between_weeks is not None:
            preferences.min_gap_between_weeks = min_gap_between_weeks
        if notify_swap_requests is not None:
            preferences.notify_swap_requests = notify_swap_requests
        if notify_schedule_changes is not None:
            preferences.notify_schedule_changes = notify_schedule_changes
        if notify_conflict_alerts is not None:
            preferences.notify_conflict_alerts = notify_conflict_alerts
        if notify_reminder_days is not None:
            preferences.notify_reminder_days = notify_reminder_days
        if notes is not None:
            preferences.notes = notes

        preferences.updated_at = datetime.utcnow()
        self.db.commit()
        self.db.refresh(preferences)

        return preferences

    def add_preferred_week(self, faculty_id: UUID, week_date: date) -> FacultyPreference:
        """Add a week to the preferred list."""
        preferences = self.get_or_create_preferences(faculty_id)
        week_str = week_date.isoformat()

        if preferences.preferred_weeks is None:
            preferences.preferred_weeks = []

        if week_str not in preferences.preferred_weeks:
            # Remove from blocked if present
            if preferences.blocked_weeks and week_str in preferences.blocked_weeks:
                preferences.blocked_weeks = [w for w in preferences.blocked_weeks if w != week_str]

            preferences.preferred_weeks = preferences.preferred_weeks + [week_str]
            preferences.updated_at = datetime.utcnow()
            self.db.commit()
            self.db.refresh(preferences)

        return preferences

    def add_blocked_week(self, faculty_id: UUID, week_date: date) -> FacultyPreference:
        """Add a week to the blocked list."""
        preferences = self.get_or_create_preferences(faculty_id)
        week_str = week_date.isoformat()

        if preferences.blocked_weeks is None:
            preferences.blocked_weeks = []

        if week_str not in preferences.blocked_weeks:
            # Remove from preferred if present
            if preferences.preferred_weeks and week_str in preferences.preferred_weeks:
                preferences.preferred_weeks = [w for w in preferences.preferred_weeks if w != week_str]

            preferences.blocked_weeks = preferences.blocked_weeks + [week_str]
            preferences.updated_at = datetime.utcnow()
            self.db.commit()
            self.db.refresh(preferences)

        return preferences

    def remove_preferred_week(self, faculty_id: UUID, week_date: date) -> FacultyPreference:
        """Remove a week from the preferred list."""
        preferences = self.get_or_create_preferences(faculty_id)
        week_str = week_date.isoformat()

        if preferences.preferred_weeks and week_str in preferences.preferred_weeks:
            preferences.preferred_weeks = [w for w in preferences.preferred_weeks if w != week_str]
            preferences.updated_at = datetime.utcnow()
            self.db.commit()
            self.db.refresh(preferences)

        return preferences

    def remove_blocked_week(self, faculty_id: UUID, week_date: date) -> FacultyPreference:
        """Remove a week from the blocked list."""
        preferences = self.get_or_create_preferences(faculty_id)
        week_str = week_date.isoformat()

        if preferences.blocked_weeks and week_str in preferences.blocked_weeks:
            preferences.blocked_weeks = [w for w in preferences.blocked_weeks if w != week_str]
            preferences.updated_at = datetime.utcnow()
            self.db.commit()
            self.db.refresh(preferences)

        return preferences

    def is_week_blocked(self, faculty_id: UUID, week_date: date) -> bool:
        """Check if a week is blocked for a faculty member."""
        preferences = self.db.query(FacultyPreference).filter(
            FacultyPreference.faculty_id == faculty_id
        ).first()

        if not preferences or not preferences.blocked_weeks:
            return False

        return week_date.isoformat() in preferences.blocked_weeks

    def is_week_preferred(self, faculty_id: UUID, week_date: date) -> bool:
        """Check if a week is preferred by a faculty member."""
        preferences = self.db.query(FacultyPreference).filter(
            FacultyPreference.faculty_id == faculty_id
        ).first()

        if not preferences or not preferences.preferred_weeks:
            return False

        return week_date.isoformat() in preferences.preferred_weeks

    def get_faculty_with_preference_for_week(
        self,
        week_date: date,
        exclude_faculty_ids: Optional[List[UUID]] = None,
    ) -> List[UUID]:
        """
        Find faculty who have marked a week as preferred.

        Useful for finding swap candidates.
        """
        query = self.db.query(FacultyPreference)

        if exclude_faculty_ids:
            query = query.filter(~FacultyPreference.faculty_id.in_(exclude_faculty_ids))

        week_str = week_date.isoformat()
        preferences = query.all()

        return [
            p.faculty_id for p in preferences
            if p.preferred_weeks and week_str in p.preferred_weeks
        ]

    def get_faculty_without_blocks_for_week(
        self,
        week_date: date,
        exclude_faculty_ids: Optional[List[UUID]] = None,
    ) -> List[UUID]:
        """
        Find faculty who haven't blocked a week.

        Useful for finding available swap candidates.
        """
        query = self.db.query(FacultyPreference)

        if exclude_faculty_ids:
            query = query.filter(~FacultyPreference.faculty_id.in_(exclude_faculty_ids))

        week_str = week_date.isoformat()
        preferences = query.all()

        return [
            p.faculty_id for p in preferences
            if not p.blocked_weeks or week_str not in p.blocked_weeks
        ]
