"""Service for managing faculty FMIT scheduling preferences."""
from datetime import date, datetime, timedelta
from typing import Optional
from uuid import UUID, uuid4

from sqlalchemy import and_, func, or_
from sqlalchemy.orm import Session

from app.models.assignment import Assignment
from app.models.block import Block
from app.models.faculty_preference import FacultyPreference
from app.models.person import Person
from app.models.swap import SwapApproval, SwapRecord, SwapStatus


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
        preferred_weeks: list[str] | None = None,
        blocked_weeks: list[str] | None = None,
        max_weeks_per_month: int | None = None,
        max_consecutive_weeks: int | None = None,
        min_gap_between_weeks: int | None = None,
        notify_swap_requests: bool | None = None,
        notify_schedule_changes: bool | None = None,
        notify_conflict_alerts: bool | None = None,
        notify_reminder_days: int | None = None,
        notes: str | None = None,
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
        exclude_faculty_ids: list[UUID] | None = None,
    ) -> list[UUID]:
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
        exclude_faculty_ids: list[UUID] | None = None,
    ) -> list[UUID]:
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

    # ===== SWAP AUTO-MATCHING LOGIC =====

    def find_best_matches(
        self,
        swap_request_id: UUID,
        limit: int = 10,
    ) -> list[dict]:
        """
        Find the best potential matches for a swap request.

        Args:
            swap_request_id: The ID of the swap request to match
            limit: Maximum number of matches to return

        Returns:
            List of match dictionaries with compatibility scores, sorted by score.
            Each dict contains:
            - swap_id: UUID of potential matching swap
            - compatibility_score: float between 0-1
            - source_faculty_id: UUID
            - target_faculty_id: UUID
            - source_week: date
            - target_week: date
            - reason: str explaining the match
        """
        # Get the original swap request
        swap_request = self.db.query(SwapRecord).filter(
            SwapRecord.id == swap_request_id
        ).first()

        if not swap_request:
            raise ValueError(f"Swap request {swap_request_id} not found")

        # Find potential matching swaps (pending swaps where someone wants the source week)
        potential_matches = self.db.query(SwapRecord).filter(
            and_(
                SwapRecord.id != swap_request_id,
                SwapRecord.status == SwapStatus.PENDING,
                or_(
                    # They want our week as their target
                    SwapRecord.target_week == swap_request.source_week,
                    # Or we want their source week as our target
                    SwapRecord.source_week == swap_request.target_week,
                ),
            )
        ).all()

        matches = []
        for candidate in potential_matches:
            score = self.calculate_compatibility_score(swap_request, candidate)

            if score > 0:  # Only include viable matches
                reason = self._generate_match_reason(swap_request, candidate, score)

                matches.append({
                    "swap_id": candidate.id,
                    "compatibility_score": score,
                    "source_faculty_id": candidate.source_faculty_id,
                    "target_faculty_id": candidate.target_faculty_id,
                    "source_week": candidate.source_week,
                    "target_week": candidate.target_week,
                    "reason": reason,
                })

        # Sort by compatibility score (highest first)
        matches.sort(key=lambda x: x["compatibility_score"], reverse=True)

        return matches[:limit]

    def calculate_compatibility_score(
        self,
        request_a: SwapRecord,
        request_b: SwapRecord,
    ) -> float:
        """
        Calculate compatibility score between two swap requests.

        The score is a float between 0 and 1, where:
        - 1.0 = Perfect match
        - 0.5-0.99 = Good match with some factors favoring it
        - 0.1-0.49 = Acceptable match but not ideal
        - 0.0 = Incompatible

        Scoring factors:
        - Mutual preference alignment (40 points)
        - No blocked weeks (30 points)
        - Historical acceptance rate (20 points)
        - Workload balance (10 points)

        Args:
            request_a: First swap request
            request_b: Second swap request

        Returns:
            Compatibility score between 0.0 and 1.0
        """
        score = 0.0
        max_score = 100.0

        # Factor 1: Mutual preference alignment (40 points)
        preference_score = self._score_preference_alignment(request_a, request_b)
        score += preference_score * 40

        # Factor 2: No blocked weeks (30 points)
        blocking_score = self._score_blocking_constraints(request_a, request_b)
        score += blocking_score * 30

        # Factor 3: Historical acceptance rate (20 points)
        history_score = self._score_historical_acceptance(request_a, request_b)
        score += history_score * 20

        # Factor 4: Workload balance (10 points)
        workload_score = self._score_workload_balance(request_a, request_b)
        score += workload_score * 10

        return score / max_score

    def auto_suggest_swaps(
        self,
        person_id: UUID,
        limit: int = 5,
    ) -> list[dict]:
        """
        Auto-suggest potential swaps for a person based on their preferences.

        This proactively looks for swap opportunities that would benefit
        the person based on their stated preferences.

        Args:
            person_id: The faculty member's ID
            limit: Maximum number of suggestions to return

        Returns:
            List of suggested swap opportunities with:
            - assignment_id: UUID of the assignment they could swap from
            - current_week: date of their current assignment
            - suggested_partner_id: UUID of potential swap partner
            - suggested_week: date they would get
            - benefit_score: float indicating how beneficial this swap would be
            - reason: str explaining the suggestion
        """
        # Get person's preferences
        preferences = self.get_or_create_preferences(person_id)

        # Get person's current assignments
        current_assignments = self.db.query(Assignment, Block).join(
            Block, Assignment.block_id == Block.id
        ).filter(
            and_(
                Assignment.person_id == person_id,
                Block.start_date >= datetime.utcnow().date(),  # Future assignments only
            )
        ).all()

        suggestions = []

        for assignment, block in current_assignments:
            current_week = block.start_date

            # Check if this week is blocked by the person
            if self.is_week_blocked(person_id, current_week):
                # Find someone who wants this week
                interested_faculty = self.get_faculty_with_preference_for_week(
                    current_week,
                    exclude_faculty_ids=[person_id]
                )

                for partner_id in interested_faculty:
                    # Find their assignments on preferred weeks
                    partner_assignments = self.db.query(Assignment, Block).join(
                        Block, Assignment.block_id == Block.id
                    ).filter(
                        and_(
                            Assignment.person_id == partner_id,
                            Block.start_date >= datetime.utcnow().date(),
                        )
                    ).all()

                    for partner_assignment, partner_block in partner_assignments:
                        partner_week = partner_block.start_date

                        # Check if we prefer their week and they don't block it
                        if (self.is_week_preferred(person_id, partner_week) and
                            not self.is_week_blocked(partner_id, partner_week)):

                            benefit_score = self._calculate_swap_benefit(
                                person_id, current_week, partner_week
                            )

                            suggestions.append({
                                "assignment_id": assignment.id,
                                "current_week": current_week,
                                "suggested_partner_id": partner_id,
                                "suggested_week": partner_week,
                                "benefit_score": benefit_score,
                                "reason": (
                                    f"You have this week blocked, they prefer it. "
                                    f"You prefer their week ({partner_week.isoformat()}), "
                                    f"and they don't have it blocked."
                                ),
                            })

        # Sort by benefit score
        suggestions.sort(key=lambda x: x["benefit_score"], reverse=True)

        return suggestions[:limit]

    def learn_from_swap_history(
        self,
        faculty_id: UUID,
        lookback_days: int = 365,
    ) -> dict:
        """
        Learn from a faculty member's swap history to understand patterns.

        Analyzes past swap behavior to identify:
        - Most commonly swapped-for weeks
        - Most commonly swapped-away weeks
        - Acceptance/rejection patterns
        - Preferred swap partners

        Args:
            faculty_id: The faculty member's ID
            lookback_days: How many days back to analyze

        Returns:
            Dictionary with learning insights:
            - acceptance_rate: float (0-1)
            - commonly_desired_weeks: list of week dates they usually want
            - commonly_avoided_weeks: list of week dates they usually avoid
            - preferred_partners: list of faculty IDs they often swap with
            - rejection_rate: float (0-1)
        """
        cutoff_date = datetime.utcnow() - timedelta(days=lookback_days)

        # Get swap history where this person was involved
        swaps = self.db.query(SwapRecord).filter(
            or_(
                SwapRecord.source_faculty_id == faculty_id,
                SwapRecord.target_faculty_id == faculty_id,
            ),
            SwapRecord.requested_at >= cutoff_date,
        ).all()

        if not swaps:
            return {
                "acceptance_rate": 0.5,  # Neutral default
                "commonly_desired_weeks": [],
                "commonly_avoided_weeks": [],
                "preferred_partners": [],
                "rejection_rate": 0.5,
                "total_swaps": 0,
            }

        # Analyze acceptances
        approvals = self.db.query(SwapApproval).filter(
            SwapApproval.faculty_id == faculty_id,
            SwapApproval.swap_id.in_([s.id for s in swaps]),
        ).all()

        accepted = sum(1 for a in approvals if a.approved is True)
        rejected = sum(1 for a in approvals if a.approved is False)
        total_responses = accepted + rejected

        acceptance_rate = accepted / total_responses if total_responses > 0 else 0.5
        rejection_rate = rejected / total_responses if total_responses > 0 else 0.5

        # Analyze week patterns
        desired_weeks = {}
        avoided_weeks = {}
        partners = {}

        for swap in swaps:
            if swap.source_faculty_id == faculty_id:
                # They initiated - they want target_week, avoid source_week
                if swap.target_week:
                    desired_weeks[swap.target_week] = desired_weeks.get(swap.target_week, 0) + 1
                avoided_weeks[swap.source_week] = avoided_weeks.get(swap.source_week, 0) + 1

                if swap.status in [SwapStatus.APPROVED, SwapStatus.EXECUTED]:
                    partners[swap.target_faculty_id] = partners.get(swap.target_faculty_id, 0) + 1

            elif swap.target_faculty_id == faculty_id:
                # They were target - they want source_week, would give up target_week
                desired_weeks[swap.source_week] = desired_weeks.get(swap.source_week, 0) + 1
                if swap.target_week:
                    avoided_weeks[swap.target_week] = avoided_weeks.get(swap.target_week, 0) + 1

                if swap.status in [SwapStatus.APPROVED, SwapStatus.EXECUTED]:
                    partners[swap.source_faculty_id] = partners.get(swap.source_faculty_id, 0) + 1

        # Sort and get top items
        commonly_desired = sorted(desired_weeks.items(), key=lambda x: x[1], reverse=True)
        commonly_avoided = sorted(avoided_weeks.items(), key=lambda x: x[1], reverse=True)
        preferred_partners_list = sorted(partners.items(), key=lambda x: x[1], reverse=True)

        return {
            "acceptance_rate": acceptance_rate,
            "commonly_desired_weeks": [w for w, _ in commonly_desired[:5]],
            "commonly_avoided_weeks": [w for w, _ in commonly_avoided[:5]],
            "preferred_partners": [p for p, _ in preferred_partners_list[:5]],
            "rejection_rate": rejection_rate,
            "total_swaps": len(swaps),
        }

    # ===== PRIVATE HELPER METHODS =====

    def _score_preference_alignment(
        self,
        request_a: SwapRecord,
        request_b: SwapRecord,
    ) -> float:
        """
        Score how well the two requests align with each other's preferences.

        Returns a score between 0 and 1.
        """
        score = 0.0

        # Check if A wants what B has, and B wants what A has
        a_wants_b_source = (
            request_a.target_week == request_b.source_week if request_a.target_week else False
        )
        b_wants_a_source = (
            request_b.target_week == request_a.source_week if request_b.target_week else False
        )

        # Perfect mutual alignment
        if a_wants_b_source and b_wants_a_source:
            score = 1.0
        # One-way alignment
        elif a_wants_b_source or b_wants_a_source:
            score = 0.6
        else:
            # Check preference lists
            a_prefs = self.get_or_create_preferences(request_a.source_faculty_id)
            b_prefs = self.get_or_create_preferences(request_b.source_faculty_id)

            a_prefers_b_week = (
                b_prefs.preferred_weeks and
                request_b.source_week.isoformat() in a_prefs.preferred_weeks
            ) if a_prefs.preferred_weeks else False

            b_prefers_a_week = (
                a_prefs.preferred_weeks and
                request_a.source_week.isoformat() in b_prefs.preferred_weeks
            ) if b_prefs.preferred_weeks else False

            if a_prefers_b_week and b_prefers_a_week:
                score = 0.8
            elif a_prefers_b_week or b_prefers_a_week:
                score = 0.4
            else:
                score = 0.2

        return score

    def _score_blocking_constraints(
        self,
        request_a: SwapRecord,
        request_b: SwapRecord,
    ) -> float:
        """
        Score based on blocking constraints. Returns 1.0 if no blocks, lower if blocked.
        """
        # Check if either party has blocked the week they would receive
        a_blocks_b_week = self.is_week_blocked(
            request_a.source_faculty_id,
            request_b.source_week
        )
        b_blocks_a_week = self.is_week_blocked(
            request_b.source_faculty_id,
            request_a.source_week
        )

        if a_blocks_b_week or b_blocks_a_week:
            return 0.0  # Incompatible

        return 1.0  # No blocking issues

    def _score_historical_acceptance(
        self,
        request_a: SwapRecord,
        request_b: SwapRecord,
    ) -> float:
        """
        Score based on historical acceptance rates of both parties.
        """
        a_history = self.learn_from_swap_history(request_a.source_faculty_id)
        b_history = self.learn_from_swap_history(request_b.source_faculty_id)

        a_rate = a_history.get("acceptance_rate", 0.5)
        b_rate = b_history.get("acceptance_rate", 0.5)

        # Average of both acceptance rates
        return (a_rate + b_rate) / 2.0

    def _score_workload_balance(
        self,
        request_a: SwapRecord,
        request_b: SwapRecord,
    ) -> float:
        """
        Score based on workload balance considerations.

        Considers if the swap would help balance workload distribution.
        """
        # Get preferences for both parties
        a_prefs = self.get_or_create_preferences(request_a.source_faculty_id)
        b_prefs = self.get_or_create_preferences(request_b.source_faculty_id)

        # Count current assignments for each person
        a_count = self.db.query(Assignment).filter(
            Assignment.person_id == request_a.source_faculty_id
        ).count()

        b_count = self.db.query(Assignment).filter(
            Assignment.person_id == request_b.source_faculty_id
        ).count()

        # Get target weeks per year
        a_target = a_prefs.target_weeks_per_year or 6
        b_target = b_prefs.target_weeks_per_year or 6

        # Calculate how far each is from their target
        a_delta = abs(a_count - a_target)
        b_delta = abs(b_count - b_target)

        # Swap is better if it helps both get closer to their targets
        # For simplicity, if both are close to their targets, score higher
        max_delta = max(a_delta, b_delta, 1)  # Avoid division by zero

        return 1.0 - (max_delta / 52.0)  # Normalize assuming max 52 weeks

    def _generate_match_reason(
        self,
        request_a: SwapRecord,
        request_b: SwapRecord,
        score: float,
    ) -> str:
        """Generate a human-readable reason for the match."""
        reasons = []

        # Check mutual preference
        a_wants_b = request_a.target_week == request_b.source_week if request_a.target_week else False
        b_wants_a = request_b.target_week == request_a.source_week if request_b.target_week else False

        if a_wants_b and b_wants_a:
            reasons.append("Perfect mutual preference match")
        elif a_wants_b:
            reasons.append("You want their week")
        elif b_wants_a:
            reasons.append("They want your week")

        # Check historical compatibility
        a_history = self.learn_from_swap_history(request_a.source_faculty_id)
        if request_b.source_faculty_id in a_history.get("preferred_partners", []):
            reasons.append("Previous successful swap partner")

        # Check preference lists
        a_prefs = self.get_or_create_preferences(request_a.source_faculty_id)
        b_prefs = self.get_or_create_preferences(request_b.source_faculty_id)

        if (a_prefs.preferred_weeks and
            request_b.source_week.isoformat() in a_prefs.preferred_weeks):
            reasons.append("Their week is on your preferred list")

        if score >= 0.8:
            reasons.insert(0, "Highly compatible")
        elif score >= 0.6:
            reasons.insert(0, "Good match")

        return "; ".join(reasons) if reasons else "Potential match based on availability"

    def _calculate_swap_benefit(
        self,
        person_id: UUID,
        current_week: date,
        proposed_week: date,
    ) -> float:
        """
        Calculate the benefit score for a potential swap.

        Returns a score between 0 and 1 indicating how beneficial
        the swap would be for the person.
        """
        score = 0.0

        # Check if current week is blocked
        if self.is_week_blocked(person_id, current_week):
            score += 0.4

        # Check if proposed week is preferred
        if self.is_week_preferred(person_id, proposed_week):
            score += 0.4

        # Check historical patterns
        history = self.learn_from_swap_history(person_id)

        if proposed_week in history.get("commonly_desired_weeks", []):
            score += 0.1

        if current_week in history.get("commonly_avoided_weeks", []):
            score += 0.1

        return min(score, 1.0)
