"""Enhanced auto-matching service for FMIT swap requests."""

from datetime import date, datetime, timedelta
from uuid import UUID, uuid4

from sqlalchemy import and_, or_
from sqlalchemy.orm import Session

from app.models.assignment import Assignment
from app.models.block import Block
from app.models.person import Person
from app.models.swap import SwapRecord, SwapStatus, SwapType
from app.schemas.swap_matching import (
    AutoMatchResult,
    BatchAutoMatchResult,
    MatchingCriteria,
    MatchingSuggestion,
    MatchPriority,
    MatchType,
    RankedMatch,
    ScoringBreakdown,
    SwapMatch,
)
from app.services.faculty_preference_service import FacultyPreferenceService
from app.services.swap_validation import SwapValidationService


class SwapAutoMatcher:
    """
    Enhanced auto-matching service for swap requests.

    Provides intelligent matching between swap requests using multiple
    scoring factors including date proximity, preference alignment,
    workload balance, past swap history, and faculty availability.
    """

    def __init__(self, db: Session, criteria: MatchingCriteria | None = None) -> None:
        """
        Initialize the auto-matcher.

        Args:
            db: Database session
            criteria: Optional custom matching criteria (uses defaults if not provided)
        """
        self.db = db
        self.criteria = criteria or MatchingCriteria()
        self.preference_service = FacultyPreferenceService(db)
        self.validation_service = SwapValidationService(db)

    def find_compatible_swaps(self, request_id: UUID) -> list[SwapMatch]:
        """
        Find all compatible swap matches for a given request.

        Args:
            request_id: The swap request ID to find matches for

        Returns:
            List of compatible SwapMatch objects

        Raises:
            ValueError: If request not found
        """
        # Get the source request
        request = self.db.query(SwapRecord).filter(SwapRecord.id == request_id).first()

        if not request:
            raise ValueError(f"Swap request {request_id} not found")

        if request.status != SwapStatus.PENDING:
            return []  # Only match pending requests

        # Find all other pending requests
        candidates = (
            self.db.query(SwapRecord)
            .filter(
                SwapRecord.id != request_id,
                SwapRecord.status == SwapStatus.PENDING,
            )
            .all()
        )

        matches = []

        for candidate in candidates:
            # Check if this is a compatible match
            if self._is_compatible(request, candidate):
                swap_match = self._create_swap_match(request, candidate)
                matches.append(swap_match)

        return matches

    def score_swap_compatibility(
        self, request: SwapRecord, candidate: SwapRecord
    ) -> float:
        """
        Calculate compatibility score between two swap requests.

        Incorporates multiple factors:
        - Date proximity (closer dates = higher score)
        - Preference alignment (both parties get preferred dates)
        - Workload balance (maintains fairness)
        - Past swap history (avoid repeated pairings)
        - Faculty availability verification

        Args:
            request: First swap request
            candidate: Second swap request (potential match)

        Returns:
            Compatibility score between 0.0 and 1.0
        """
        # Calculate individual factor scores
        date_score = self._score_date_proximity(request, candidate)
        preference_score = self._score_preference_alignment(request, candidate)
        workload_score = self._score_workload_balance(request, candidate)
        history_score = self._score_swap_history(request, candidate)
        availability_score = self._score_availability(request, candidate)

        # Apply blocking penalty
        blocking_penalty = self._check_blocking_constraints(request, candidate)

        # Calculate weighted total
        total_score = (
            (date_score * self.criteria.date_proximity_weight)
            + (preference_score * self.criteria.preference_alignment_weight)
            + (workload_score * self.criteria.workload_balance_weight)
            + (history_score * self.criteria.history_weight)
            + (availability_score * self.criteria.availability_weight)
        ) * blocking_penalty

        # Normalize by total weight
        if self.criteria.total_weight > 0:
            total_score = total_score / self.criteria.total_weight

        return min(max(total_score, 0.0), 1.0)

    def suggest_optimal_matches(
        self, request_id: UUID, top_k: int = 5
    ) -> list[RankedMatch]:
        """
        Suggest optimal matches for a swap request, ranked by compatibility.

        Args:
            request_id: The swap request ID
            top_k: Number of top matches to return (default: 5)

        Returns:
            List of RankedMatch objects, sorted by compatibility score (highest first)

        Raises:
            ValueError: If request not found
        """
        # Get the source request
        request = self.db.query(SwapRecord).filter(SwapRecord.id == request_id).first()

        if not request:
            raise ValueError(f"Swap request {request_id} not found")

        # Find all compatible matches
        compatible_matches = self.find_compatible_swaps(request_id)

        # Score and rank each match
        ranked_matches = []

        for match in compatible_matches:
            # Get the candidate request
            candidate = (
                self.db.query(SwapRecord)
                .filter(SwapRecord.id == match.request_b_id)
                .first()
            )

            if not candidate:
                continue

            # Calculate detailed scoring
            date_score = self._score_date_proximity(request, candidate)
            preference_score = self._score_preference_alignment(request, candidate)
            workload_score = self._score_workload_balance(request, candidate)
            history_score = self._score_swap_history(request, candidate)
            availability_score = self._score_availability(request, candidate)
            blocking_penalty = self._check_blocking_constraints(request, candidate)

            # Calculate total score
            total_score = self.score_swap_compatibility(request, candidate)

            # Only include matches above threshold
            if total_score < self.criteria.minimum_score_threshold:
                continue

            # Create scoring breakdown
            scoring_breakdown = ScoringBreakdown(
                date_proximity_score=date_score,
                preference_alignment_score=preference_score,
                workload_balance_score=workload_score,
                history_score=history_score,
                availability_score=availability_score,
                blocking_penalty=blocking_penalty,
                total_score=total_score,
            )

            # Determine priority
            priority = self._determine_priority(total_score, request, candidate)

            # Generate explanation
            explanation = self._generate_match_explanation(
                request, candidate, scoring_breakdown, match.is_mutual
            )

            # Estimate acceptance probability
            acceptance_prob = self._estimate_acceptance_probability(
                request, candidate, total_score
            )

            # Determine recommended action
            recommended_action = self._determine_recommended_action(
                priority, acceptance_prob
            )

            # Check for warnings
            warnings = self._check_match_warnings(request, candidate)

            ranked_match = RankedMatch(
                match=match,
                compatibility_score=total_score,
                priority=priority,
                scoring_breakdown=scoring_breakdown,
                explanation=explanation,
                estimated_acceptance_probability=acceptance_prob,
                recommended_action=recommended_action,
                warnings=warnings,
            )

            ranked_matches.append(ranked_match)

        # Sort by compatibility score (highest first)
        ranked_matches.sort(key=lambda x: x.compatibility_score, reverse=True)

        # Return top K matches
        limit = min(top_k, self.criteria.max_matches_per_request)
        return ranked_matches[:limit]

    def auto_match_pending_requests(self) -> BatchAutoMatchResult:
        """
        Automatically match all pending swap requests.

        Processes all pending requests and finds the best matches for each.
        Returns a comprehensive result with all matches found.

        Returns:
            BatchAutoMatchResult with matching statistics and results
        """
        start_time = datetime.utcnow()

        # Get all pending requests
        pending_requests = (
            self.db.query(SwapRecord)
            .filter(SwapRecord.status == SwapStatus.PENDING)
            .all()
        )

        total_requests = len(pending_requests)
        successful_matches = []
        no_matches = []
        high_priority_matches = []
        total_matches_found = 0

        for request in pending_requests:
            try:
                # Find matches for this request
                matches = self.suggest_optimal_matches(
                    request.id, top_k=self.criteria.max_matches_per_request
                )

                best_match = matches[0] if matches else None
                matches_found = len(matches)

                result = AutoMatchResult(
                    request_id=request.id,
                    faculty_id=request.source_faculty_id,
                    source_week=request.source_week,
                    target_week=request.target_week,
                    matches_found=matches_found,
                    best_match=best_match,
                    all_matches=matches,
                    success=matches_found > 0,
                    message=(
                        f"Found {matches_found} compatible matches"
                        if matches_found > 0
                        else "No compatible matches found"
                    ),
                )

                if matches_found > 0:
                    successful_matches.append(result)
                    total_matches_found += matches_found

                    # Check if any are high priority
                    if best_match and best_match.priority in [
                        MatchPriority.CRITICAL,
                        MatchPriority.HIGH,
                    ]:
                        high_priority_matches.append(result)
                else:
                    no_matches.append(request.id)

            except Exception:
                # Log error but continue processing
                no_matches.append(request.id)
                continue

        end_time = datetime.utcnow()
        execution_time = (end_time - start_time).total_seconds()

        return BatchAutoMatchResult(
            total_requests_processed=total_requests,
            total_matches_found=total_matches_found,
            successful_matches=successful_matches,
            no_matches=no_matches,
            high_priority_matches=high_priority_matches,
            execution_time_seconds=execution_time,
        )

    def suggest_proactive_swaps(
        self, faculty_id: UUID, limit: int = 5
    ) -> list[MatchingSuggestion]:
        """
        Proactively suggest beneficial swaps for a faculty member.

        Analyzes faculty preferences and current assignments to identify
        opportunities for beneficial swaps, even if no request exists.

        Args:
            faculty_id: Faculty member ID
            limit: Maximum number of suggestions to return

        Returns:
            List of MatchingSuggestion objects
        """
        # Get faculty's preferences
        preferences = self.preference_service.get_or_create_preferences(faculty_id)

        # Get faculty's current future assignments
        current_assignments = (
            self.db.query(Assignment, Block)
            .join(Block, Assignment.block_id == Block.id)
            .filter(
                Assignment.person_id == faculty_id,
                Block.start_date >= datetime.utcnow().date(),
            )
            .all()
        )

        suggestions = []

        for assignment, block in current_assignments:
            current_week = block.start_date

            # Check if this week is blocked by the faculty
            is_blocked = self.preference_service.is_week_blocked(
                faculty_id, current_week
            )

            if is_blocked:
                # Find faculty who prefer this week
                interested_faculty = (
                    self.preference_service.get_faculty_with_preference_for_week(
                        current_week, exclude_faculty_ids=[faculty_id]
                    )
                )

                for partner_id in interested_faculty:
                    partner = self._get_faculty(partner_id)
                    if not partner:
                        continue

                    # Find their assignments on weeks this faculty prefers
                    partner_assignments = (
                        self.db.query(Assignment, Block)
                        .join(Block, Assignment.block_id == Block.id)
                        .filter(
                            Assignment.person_id == partner_id,
                            Block.start_date >= datetime.utcnow().date(),
                        )
                        .all()
                    )

                    for partner_assignment, partner_block in partner_assignments:
                        partner_week = partner_block.start_date

                        # Check if we prefer their week
                        we_prefer = self.preference_service.is_week_preferred(
                            faculty_id, partner_week
                        )
                        they_dont_block = not self.preference_service.is_week_blocked(
                            partner_id, partner_week
                        )

                        if we_prefer and they_dont_block:
                            benefit_score = self._calculate_suggestion_benefit(
                                faculty_id,
                                current_week,
                                partner_week,
                                is_blocked=True,
                                is_preferred=True,
                            )

                            faculty = self._get_faculty(faculty_id)
                            faculty_name = faculty.name if faculty else "Unknown"

                            suggestion = MatchingSuggestion(
                                faculty_id=faculty_id,
                                faculty_name=faculty_name,
                                current_week=current_week,
                                suggested_partner_id=partner_id,
                                suggested_partner_name=partner.name,
                                partner_week=partner_week,
                                benefit_score=benefit_score,
                                reason=(
                                    f"You have {current_week.isoformat()} blocked, "
                                    f"but {partner.name} prefers it. "
                                    f"You prefer {partner_week.isoformat()}, "
                                    f"which they don't have blocked."
                                ),
                                action_text=f"Request swap with {partner.name}",
                            )

                            suggestions.append(suggestion)

        # Sort by benefit score
        suggestions.sort(key=lambda x: x.benefit_score, reverse=True)

        return suggestions[:limit]

    # ===== PRIVATE HELPER METHODS =====

    def _is_compatible(self, request_a: SwapRecord, request_b: SwapRecord) -> bool:
        """
        Check if two swap requests are compatible.

        Args:
            request_a: First request
            request_b: Second request

        Returns:
            True if requests are compatible
        """
        # Don't match with self
        if request_a.source_faculty_id == request_b.source_faculty_id:
            return False

        # Check date separation constraint
        if self.criteria.max_date_separation_days:
            days_apart = abs((request_a.source_week - request_b.source_week).days)
            if days_apart > self.criteria.max_date_separation_days:
                return False

        # Check if weeks are blocked
        if self.criteria.exclude_blocked_weeks:
            a_blocks_b = self.preference_service.is_week_blocked(
                request_a.source_faculty_id, request_b.source_week
            )
            b_blocks_a = self.preference_service.is_week_blocked(
                request_b.source_faculty_id, request_a.source_week
            )

            if a_blocks_b or b_blocks_a:
                return False

        # Check mutual availability if required
        if self.criteria.require_mutual_availability:
            # Validate both directions
            valid_ab = self.validation_service.validate_swap(
                source_faculty_id=request_a.source_faculty_id,
                source_week=request_a.source_week,
                target_faculty_id=request_b.source_faculty_id,
                target_week=request_b.source_week,
            )

            if not valid_ab.valid:
                return False

        return True

    def _create_swap_match(
        self, request_a: SwapRecord, request_b: SwapRecord
    ) -> SwapMatch:
        """Create a SwapMatch object from two requests."""
        faculty_a = self._get_faculty(request_a.source_faculty_id)
        faculty_b = self._get_faculty(request_b.source_faculty_id)

        # Check if it's a mutual match
        is_mutual = (
            (
                request_a.target_week == request_b.source_week
                and request_b.target_week == request_a.source_week
            )
            if request_a.target_week and request_b.target_week
            else False
        )

        # Determine match type
        if is_mutual:
            match_type = MatchType.MUTUAL
        elif (
            request_a.swap_type == SwapType.ABSORB
            or request_b.swap_type == SwapType.ABSORB
        ):
            match_type = MatchType.ABSORB
        else:
            match_type = MatchType.ONE_WAY

        return SwapMatch(
            match_id=uuid4(),
            request_a_id=request_a.id,
            request_b_id=request_b.id,
            faculty_a_id=request_a.source_faculty_id,
            faculty_a_name=faculty_a.name if faculty_a else "Unknown",
            faculty_b_id=request_b.source_faculty_id,
            faculty_b_name=faculty_b.name if faculty_b else "Unknown",
            week_a=request_a.source_week,
            week_b=request_b.source_week,
            match_type=match_type,
            is_mutual=is_mutual,
        )

    def _score_date_proximity(
        self, request_a: SwapRecord, request_b: SwapRecord
    ) -> float:
        """
        Score based on date proximity (closer dates = higher score).

        Returns:
            Score between 0.0 and 1.0
        """
        days_apart = abs((request_a.source_week - request_b.source_week).days)

        # If dates are very close (within 2 weeks), score high
        if days_apart <= 14:
            return 1.0
        # If dates are within max separation, score decreases linearly
        elif days_apart <= self.criteria.max_date_separation_days:
            ratio = days_apart / self.criteria.max_date_separation_days
            return 1.0 - (ratio * 0.5)  # Score from 1.0 to 0.5
        else:
            return 0.0

    def _score_preference_alignment(
        self, request_a: SwapRecord, request_b: SwapRecord
    ) -> float:
        """
        Score based on preference alignment.

        Returns:
            Score between 0.0 and 1.0
        """
        # Use the existing preference service logic
        return self.preference_service._score_preference_alignment(request_a, request_b)

    def _score_workload_balance(
        self, request_a: SwapRecord, request_b: SwapRecord
    ) -> float:
        """
        Score based on workload balance considerations.

        Returns:
            Score between 0.0 and 1.0
        """
        # Use the existing preference service logic
        return self.preference_service._score_workload_balance(request_a, request_b)

    def _score_swap_history(
        self, request_a: SwapRecord, request_b: SwapRecord
    ) -> float:
        """
        Score based on past swap history.

        Considers:
        - Have these faculty swapped successfully before?
        - Have they rejected each other before?
        - Overall acceptance rates

        Returns:
            Score between 0.0 and 1.0
        """
        if self.criteria.consider_past_rejections:
            # Check for past rejections between these two faculty
            past_rejections = (
                self.db.query(SwapRecord)
                .filter(
                    or_(
                        and_(
                            SwapRecord.source_faculty_id == request_a.source_faculty_id,
                            SwapRecord.target_faculty_id == request_b.source_faculty_id,
                            SwapRecord.status == SwapStatus.REJECTED,
                        ),
                        and_(
                            SwapRecord.source_faculty_id == request_b.source_faculty_id,
                            SwapRecord.target_faculty_id == request_a.source_faculty_id,
                            SwapRecord.status == SwapStatus.REJECTED,
                        ),
                    ),
                    SwapRecord.requested_at
                    >= datetime.utcnow()
                    - timedelta(days=self.criteria.history_lookback_days),
                )
                .count()
            )

            if past_rejections > 0:
                # Penalize repeated rejections
                penalty = min(past_rejections * 0.2, 0.6)
                base_score = 1.0 - penalty
            else:
                base_score = 1.0

            # Check for successful past swaps (bonus)
            past_successes = (
                self.db.query(SwapRecord)
                .filter(
                    or_(
                        and_(
                            SwapRecord.source_faculty_id == request_a.source_faculty_id,
                            SwapRecord.target_faculty_id == request_b.source_faculty_id,
                            SwapRecord.status == SwapStatus.EXECUTED,
                        ),
                        and_(
                            SwapRecord.source_faculty_id == request_b.source_faculty_id,
                            SwapRecord.target_faculty_id == request_a.source_faculty_id,
                            SwapRecord.status == SwapStatus.EXECUTED,
                        ),
                    ),
                    SwapRecord.requested_at
                    >= datetime.utcnow()
                    - timedelta(days=self.criteria.history_lookback_days),
                )
                .count()
            )

            if past_successes > 0:
                bonus = min(past_successes * 0.1, 0.3)
                base_score = min(base_score + bonus, 1.0)

            return base_score
        else:
            # Use overall acceptance rates
            return self.preference_service._score_historical_acceptance(
                request_a, request_b
            )

    def _score_availability(
        self, request_a: SwapRecord, request_b: SwapRecord
    ) -> float:
        """
        Score based on faculty availability verification.

        Returns:
            Score between 0.0 and 1.0
        """
        score = 0.0

        # Check if faculty A is available for faculty B's week
        a_available_for_b = not self.preference_service.is_week_blocked(
            request_a.source_faculty_id, request_b.source_week
        )

        # Check if faculty B is available for faculty A's week
        b_available_for_a = not self.preference_service.is_week_blocked(
            request_b.source_faculty_id, request_a.source_week
        )

        if a_available_for_b and b_available_for_a:
            score = 1.0
        elif a_available_for_b or b_available_for_a:
            score = 0.5
        else:
            score = 0.0

        # Bonus if weeks are preferred
        a_prefers_b = self.preference_service.is_week_preferred(
            request_a.source_faculty_id, request_b.source_week
        )
        b_prefers_a = self.preference_service.is_week_preferred(
            request_b.source_faculty_id, request_a.source_week
        )

        if a_prefers_b and b_prefers_a:
            score = min(score + 0.3, 1.0)
        elif a_prefers_b or b_prefers_a:
            score = min(score + 0.15, 1.0)

        return score

    def _check_blocking_constraints(
        self, request_a: SwapRecord, request_b: SwapRecord
    ) -> float:
        """
        Check for blocking constraints and return a penalty multiplier.

        Returns:
            Multiplier between 0.0 and 1.0 (1.0 = no penalty)
        """
        # Check if either party has blocked the week they would receive
        a_blocks_b = self.preference_service.is_week_blocked(
            request_a.source_faculty_id, request_b.source_week
        )
        b_blocks_a = self.preference_service.is_week_blocked(
            request_b.source_faculty_id, request_a.source_week
        )

        if a_blocks_b or b_blocks_a:
            return 0.0  # Complete penalty
        else:
            return 1.0  # No penalty

    def _determine_priority(
        self, score: float, request_a: SwapRecord, request_b: SwapRecord
    ) -> MatchPriority:
        """Determine priority level for a match."""
        # Check for urgent situations (blocked weeks)
        a_blocked = self.preference_service.is_week_blocked(
            request_a.source_faculty_id, request_a.source_week
        )
        b_blocked = self.preference_service.is_week_blocked(
            request_b.source_faculty_id, request_b.source_week
        )

        if (a_blocked or b_blocked) and score >= 0.7:
            return MatchPriority.CRITICAL

        if score >= self.criteria.high_priority_threshold:
            return MatchPriority.HIGH
        elif score >= 0.6:
            return MatchPriority.MEDIUM
        else:
            return MatchPriority.LOW

    def _generate_match_explanation(
        self,
        request_a: SwapRecord,
        request_b: SwapRecord,
        scoring: ScoringBreakdown,
        is_mutual: bool,
    ) -> str:
        """Generate human-readable explanation for the match."""
        reasons = []

        if is_mutual:
            reasons.append(
                "Perfect mutual match - both parties want each other's weeks"
            )

        if scoring.preference_alignment_score >= 0.8:
            reasons.append("Strong preference alignment")
        elif scoring.preference_alignment_score >= 0.6:
            reasons.append("Good preference match")

        if scoring.date_proximity_score >= 0.9:
            reasons.append("Very close dates")

        if scoring.history_score >= 0.8:
            reasons.append("Favorable past swap history")

        if scoring.workload_balance_score >= 0.8:
            reasons.append("Helps maintain workload balance")

        if not reasons:
            reasons.append("Compatible based on availability")

        return "; ".join(reasons)

    def _estimate_acceptance_probability(
        self, request_a: SwapRecord, request_b: SwapRecord, compatibility_score: float
    ) -> float:
        """
        Estimate probability both parties will accept the swap.

        Returns:
            Probability between 0.0 and 1.0
        """
        # Start with compatibility score as base
        base_prob = compatibility_score

        # Adjust based on historical acceptance rates
        a_history = self.preference_service.learn_from_swap_history(
            request_a.source_faculty_id
        )
        b_history = self.preference_service.learn_from_swap_history(
            request_b.source_faculty_id
        )

        a_rate = a_history.get("acceptance_rate", 0.5)
        b_rate = b_history.get("acceptance_rate", 0.5)

        # Combined probability (both must accept)
        historical_factor = (a_rate + b_rate) / 2.0

        # Weight base score more heavily, but consider history
        estimated_prob = (base_prob * 0.7) + (historical_factor * 0.3)

        return min(max(estimated_prob, 0.0), 1.0)

    def _determine_recommended_action(
        self, priority: MatchPriority, acceptance_prob: float
    ) -> str:
        """Determine the recommended action for a match."""
        if priority == MatchPriority.CRITICAL:
            return "Notify both parties immediately - urgent match"
        elif priority == MatchPriority.HIGH and acceptance_prob >= 0.7:
            return "Strongly recommend this swap to both parties"
        elif priority == MatchPriority.HIGH:
            return "Recommend this swap with explanation"
        elif acceptance_prob >= 0.7:
            return "Suggest this swap as a good option"
        else:
            return "Present as one of several options"

    def _check_match_warnings(
        self, request_a: SwapRecord, request_b: SwapRecord
    ) -> list[str]:
        """Check for any warnings about the match."""
        warnings = []

        # Check date separation
        days_apart = abs((request_a.source_week - request_b.source_week).days)
        if days_apart > 60:
            warnings.append(f"Dates are {days_apart} days apart - may not be ideal")

        # Check if weeks are very soon
        days_until_a = (request_a.source_week - datetime.utcnow().date()).days
        days_until_b = (request_b.source_week - datetime.utcnow().date()).days

        if days_until_a < 14 or days_until_b < 14:
            warnings.append("One or both weeks are coming up soon - act quickly")

        # Check workload
        a_count = (
            self.db.query(Assignment)
            .filter(Assignment.person_id == request_a.source_faculty_id)
            .count()
        )
        b_count = (
            self.db.query(Assignment)
            .filter(Assignment.person_id == request_b.source_faculty_id)
            .count()
        )

        if abs(a_count - b_count) > 3:
            warnings.append("Significant workload imbalance between parties")

        return warnings

    def _calculate_suggestion_benefit(
        self,
        faculty_id: UUID,
        current_week: date,
        proposed_week: date,
        is_blocked: bool = False,
        is_preferred: bool = False,
    ) -> float:
        """Calculate benefit score for a proactive suggestion."""
        score = 0.0

        if is_blocked:
            score += 0.4

        if is_preferred:
            score += 0.4

        # Check date proximity (prefer closer dates)
        days_apart = abs((current_week - proposed_week).days)
        if days_apart <= 14:
            score += 0.2
        elif days_apart <= 30:
            score += 0.1

        return min(score, 1.0)

    def _get_faculty(self, faculty_id: UUID) -> Person | None:
        """Get a faculty member by ID."""
        return (
            self.db.query(Person)
            .filter(Person.id == faculty_id, Person.type == "faculty")
            .first()
        )
