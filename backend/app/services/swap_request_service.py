"""Service for managing FMIT swap requests (portal workflow)."""
from dataclasses import dataclass, field
from datetime import date, datetime, timedelta
from typing import List, Optional, Tuple
from uuid import UUID, uuid4

from sqlalchemy import or_, and_
from sqlalchemy.orm import Session

from app.models.swap import SwapRecord, SwapStatus, SwapType, SwapApproval
from app.models.person import Person
from app.models.assignment import Assignment
from app.models.block import Block
from app.services.swap_validation import SwapValidationService, ValidationError
from app.services.swap_executor import SwapExecutor
from app.services.swap_notification_service import SwapNotificationService
from app.services.faculty_preference_service import FacultyPreferenceService


@dataclass
class RequestResult:
    """Result of creating a swap request."""
    success: bool
    request_id: Optional[UUID] = None
    message: str = ""
    errors: List[ValidationError] = field(default_factory=list)
    warnings: List[ValidationError] = field(default_factory=list)
    candidates_notified: int = 0


@dataclass
class RequestDetail:
    """Detailed information about a swap request."""
    id: UUID
    status: SwapStatus
    swap_type: SwapType
    source_faculty_id: UUID
    source_faculty_name: str
    source_week: date
    target_faculty_id: UUID
    target_faculty_name: str
    target_week: Optional[date]
    reason: Optional[str]
    requested_at: datetime
    approved_at: Optional[datetime] = None
    executed_at: Optional[datetime] = None
    can_cancel: bool = False
    can_respond: bool = False
    needs_approval: bool = False


@dataclass
class ResponseResult:
    """Result of responding to a swap request."""
    success: bool
    message: str = ""
    new_request_id: Optional[UUID] = None  # For counter-offers
    executed: bool = False
    errors: List[ValidationError] = field(default_factory=list)


@dataclass
class CancelResult:
    """Result of canceling a swap request."""
    success: bool
    message: str = ""


@dataclass
class MatchResult:
    """Result of auto-matching swap requests."""
    matches_found: int
    potential_matches: List[Tuple[UUID, UUID]] = field(default_factory=list)
    message: str = ""


class SwapRequestService:
    """
    Service for managing FMIT swap requests through the faculty portal.

    Orchestrates the swap request workflow:
    1. Faculty creates request to offload a week
    2. System finds compatible candidates or notifies specific faculty
    3. Target faculty responds (accept/reject/counter)
    4. Upon acceptance, swap is validated and executed
    5. Both parties are notified
    """

    def __init__(self, db: Session):
        self.db = db
        self.validator = SwapValidationService(db)
        self.executor = SwapExecutor(db)
        self.notifier = SwapNotificationService(db)
        self.preference_service = FacultyPreferenceService(db)

    def create_request(
        self,
        requester_id: UUID,
        source_week: date,
        desired_weeks: Optional[List[date]] = None,
        reason: Optional[str] = None,
        target_faculty_id: Optional[UUID] = None,
        auto_find_candidates: bool = True,
    ) -> RequestResult:
        """
        Initiate a swap request to offload an FMIT week.

        Args:
            requester_id: Faculty requesting the swap
            source_week: The week to offload
            desired_weeks: Preferred weeks to swap for (optional)
            reason: Reason for the swap request
            target_faculty_id: Specific faculty to target (optional)
            auto_find_candidates: Find and notify compatible candidates

        Returns:
            RequestResult with request details or errors
        """
        # Verify requester is faculty
        requester = self._get_faculty(requester_id)
        if not requester:
            return RequestResult(
                success=False,
                message="Requester is not a valid faculty member",
                errors=[ValidationError("INVALID_REQUESTER", "Faculty not found")]
            )

        # Verify source week is assigned to requester
        if not self._is_week_assigned_to_faculty(requester_id, source_week):
            return RequestResult(
                success=False,
                message=f"Week {source_week} is not assigned to you",
                errors=[ValidationError("WEEK_NOT_ASSIGNED", "Cannot swap unassigned week")]
            )

        # Check if there's already a pending request for this week
        existing = self.db.query(SwapRecord).filter(
            SwapRecord.source_faculty_id == requester_id,
            SwapRecord.source_week == source_week,
            SwapRecord.status.in_([SwapStatus.PENDING, SwapStatus.APPROVED])
        ).first()

        if existing:
            return RequestResult(
                success=False,
                message="You already have a pending swap request for this week",
                errors=[ValidationError("DUPLICATE_REQUEST", "Pending request exists")]
            )

        # If target specified, validate the swap
        if target_faculty_id:
            validation = self.validator.validate_swap(
                source_faculty_id=requester_id,
                source_week=source_week,
                target_faculty_id=target_faculty_id,
                target_week=desired_weeks[0] if desired_weeks else None,
            )

            if not validation.valid:
                return RequestResult(
                    success=False,
                    message="Swap validation failed",
                    errors=validation.errors,
                    warnings=validation.warnings,
                )

        # Create the swap request
        swap_type = SwapType.ONE_TO_ONE if desired_weeks else SwapType.ABSORB

        # If no target specified, this becomes a marketplace posting
        if not target_faculty_id:
            # Find potential candidates
            candidates = self._find_compatible_candidates(
                source_faculty_id=requester_id,
                source_week=source_week,
                desired_weeks=desired_weeks,
            ) if auto_find_candidates else []

            if not candidates:
                # Create marketplace request without target
                request_id = uuid4()
                swap_record = SwapRecord(
                    id=request_id,
                    source_faculty_id=requester_id,
                    source_week=source_week,
                    target_faculty_id=requester_id,  # Placeholder
                    target_week=desired_weeks[0] if desired_weeks else None,
                    swap_type=swap_type,
                    status=SwapStatus.PENDING,
                    reason=reason,
                    requested_at=datetime.utcnow(),
                )
                self.db.add(swap_record)
                self.db.commit()

                return RequestResult(
                    success=True,
                    request_id=request_id,
                    message="Swap request posted to marketplace (no compatible candidates found)",
                    candidates_notified=0,
                )

            # Use first candidate as target
            target_faculty_id = candidates[0]

        # Create swap record with specific target
        request_id = uuid4()
        swap_record = SwapRecord(
            id=request_id,
            source_faculty_id=requester_id,
            source_week=source_week,
            target_faculty_id=target_faculty_id,
            target_week=desired_weeks[0] if desired_weeks else None,
            swap_type=swap_type,
            status=SwapStatus.PENDING,
            reason=reason,
            requested_at=datetime.utcnow(),
        )
        self.db.add(swap_record)
        self.db.commit()

        # Send notification to target
        target = self._get_faculty(target_faculty_id)
        if target:
            self.notifier.notify_swap_request_received(
                recipient_faculty_id=target_faculty_id,
                requester_name=requester.name,
                week_offered=source_week,
                swap_id=request_id,
                reason=reason,
            )
            self.notifier.send_pending_notifications()

        return RequestResult(
            success=True,
            request_id=request_id,
            message=f"Swap request created and sent to {target.name if target else 'candidate'}",
            candidates_notified=1,
        )

    def get_request(self, request_id: UUID) -> Optional[RequestDetail]:
        """
        Get details of a specific swap request.

        Args:
            request_id: The swap request ID

        Returns:
            RequestDetail or None if not found
        """
        swap = self.db.query(SwapRecord).filter(SwapRecord.id == request_id).first()
        if not swap:
            return None

        source_faculty = self._get_faculty(swap.source_faculty_id)
        target_faculty = self._get_faculty(swap.target_faculty_id)

        return RequestDetail(
            id=swap.id,
            status=swap.status,
            swap_type=swap.swap_type,
            source_faculty_id=swap.source_faculty_id,
            source_faculty_name=source_faculty.name if source_faculty else "Unknown",
            source_week=swap.source_week,
            target_faculty_id=swap.target_faculty_id,
            target_faculty_name=target_faculty.name if target_faculty else "Unknown",
            target_week=swap.target_week,
            reason=swap.reason,
            requested_at=swap.requested_at,
            approved_at=swap.approved_at,
            executed_at=swap.executed_at,
            can_cancel=swap.status == SwapStatus.PENDING,
            can_respond=swap.status == SwapStatus.PENDING,
            needs_approval=swap.status == SwapStatus.PENDING,
        )

    def get_my_requests(self, faculty_id: UUID) -> List[RequestDetail]:
        """
        Get all outgoing swap requests for a faculty member.

        Args:
            faculty_id: The faculty member's ID

        Returns:
            List of outgoing RequestDetail records
        """
        swaps = self.db.query(SwapRecord).filter(
            SwapRecord.source_faculty_id == faculty_id
        ).order_by(SwapRecord.requested_at.desc()).all()

        return [self._swap_to_detail(swap) for swap in swaps]

    def get_requests_for_me(self, faculty_id: UUID) -> List[RequestDetail]:
        """
        Get all incoming swap requests targeting a faculty member.

        Args:
            faculty_id: The faculty member's ID

        Returns:
            List of incoming RequestDetail records
        """
        swaps = self.db.query(SwapRecord).filter(
            SwapRecord.target_faculty_id == faculty_id,
            SwapRecord.source_faculty_id != faculty_id,  # Exclude self-requests
            SwapRecord.status == SwapStatus.PENDING,
        ).order_by(SwapRecord.requested_at.desc()).all()

        return [self._swap_to_detail(swap) for swap in swaps]

    def respond_to_request(
        self,
        request_id: UUID,
        faculty_id: UUID,
        accept: bool,
        counter_week: Optional[date] = None,
        notes: Optional[str] = None,
    ) -> ResponseResult:
        """
        Respond to a swap request (accept/reject/counter).

        Args:
            request_id: The swap request ID
            faculty_id: The responding faculty's ID
            accept: True to accept, False to reject
            counter_week: Optional counter-offer week
            notes: Optional response notes

        Returns:
            ResponseResult with outcome
        """
        swap = self.db.query(SwapRecord).filter(SwapRecord.id == request_id).first()
        if not swap:
            return ResponseResult(
                success=False,
                message="Swap request not found",
                errors=[ValidationError("NOT_FOUND", "Request does not exist")]
            )

        # Verify faculty is the target
        if swap.target_faculty_id != faculty_id:
            return ResponseResult(
                success=False,
                message="You are not the target of this swap request",
                errors=[ValidationError("UNAUTHORIZED", "Not your request to respond to")]
            )

        # Verify request is still pending
        if swap.status != SwapStatus.PENDING:
            return ResponseResult(
                success=False,
                message=f"Request is already {swap.status.value}",
                errors=[ValidationError("INVALID_STATUS", "Cannot respond to non-pending request")]
            )

        source_faculty = self._get_faculty(swap.source_faculty_id)
        target_faculty = self._get_faculty(faculty_id)

        # Handle counter-offer
        if counter_week and not accept:
            # Create a new swap request as counter-offer
            counter_result = self.create_request(
                requester_id=faculty_id,
                source_week=counter_week,
                desired_weeks=[swap.source_week],
                reason=f"Counter-offer to swap {request_id}",
                target_faculty_id=swap.source_faculty_id,
                auto_find_candidates=False,
            )

            # Reject original request
            swap.status = SwapStatus.REJECTED
            swap.notes = f"Counter-offered with week {counter_week}"
            self.db.commit()

            # Notify original requester
            if source_faculty:
                self.notifier.notify_swap_rejected(
                    recipient_faculty_id=swap.source_faculty_id,
                    rejecter_name=target_faculty.name if target_faculty else "Faculty",
                    week=swap.source_week,
                    swap_id=request_id,
                    reason=f"Counter-offered with {counter_week}",
                )
                self.notifier.send_pending_notifications()

            return ResponseResult(
                success=True,
                message=f"Counter-offer created for week {counter_week}",
                new_request_id=counter_result.request_id,
            )

        # Handle rejection
        if not accept:
            swap.status = SwapStatus.REJECTED
            swap.notes = notes
            self.db.commit()

            # Notify requester
            if source_faculty:
                self.notifier.notify_swap_rejected(
                    recipient_faculty_id=swap.source_faculty_id,
                    rejecter_name=target_faculty.name if target_faculty else "Faculty",
                    week=swap.source_week,
                    swap_id=request_id,
                    reason=notes,
                )
                self.notifier.send_pending_notifications()

            return ResponseResult(
                success=True,
                message="Swap request rejected",
            )

        # Handle acceptance
        # Re-validate the swap before executing
        validation = self.validator.validate_swap(
            source_faculty_id=swap.source_faculty_id,
            source_week=swap.source_week,
            target_faculty_id=swap.target_faculty_id,
            target_week=swap.target_week,
        )

        if not validation.valid:
            return ResponseResult(
                success=False,
                message="Swap validation failed",
                errors=validation.errors,
                warnings=validation.warnings,
            )

        # Mark as approved
        swap.status = SwapStatus.APPROVED
        swap.approved_at = datetime.utcnow()
        self.db.commit()

        # Execute the swap
        execution = self.executor.execute_swap(
            source_faculty_id=swap.source_faculty_id,
            source_week=swap.source_week,
            target_faculty_id=swap.target_faculty_id,
            target_week=swap.target_week,
            swap_type=swap.swap_type.value,
            reason=swap.reason,
        )

        if execution.success:
            swap.status = SwapStatus.EXECUTED
            swap.executed_at = datetime.utcnow()
            self.db.commit()

            # Notify both parties
            self.notifier.notify_swap_accepted(
                recipient_faculty_id=swap.source_faculty_id,
                accepter_name=target_faculty.name if target_faculty else "Faculty",
                week=swap.source_week,
                swap_id=request_id,
            )
            self.notifier.notify_swap_executed(
                faculty_ids=[swap.source_faculty_id, swap.target_faculty_id],
                week=swap.source_week,
                swap_id=request_id,
                details=f"Swap executed: {swap.source_week} transferred from {source_faculty.name if source_faculty else 'Faculty'} to {target_faculty.name if target_faculty else 'Faculty'}",
            )
            self.notifier.send_pending_notifications()

            return ResponseResult(
                success=True,
                message="Swap accepted and executed successfully",
                executed=True,
            )
        else:
            # Execution failed, revert to pending
            swap.status = SwapStatus.PENDING
            self.db.commit()

            return ResponseResult(
                success=False,
                message=f"Swap execution failed: {execution.message}",
                errors=[ValidationError("EXECUTION_FAILED", execution.message)]
            )

    def cancel_request(self, request_id: UUID, requester_id: UUID) -> CancelResult:
        """
        Cancel a pending swap request.

        Args:
            request_id: The swap request ID
            requester_id: The original requester's ID

        Returns:
            CancelResult with outcome
        """
        swap = self.db.query(SwapRecord).filter(SwapRecord.id == request_id).first()
        if not swap:
            return CancelResult(
                success=False,
                message="Swap request not found",
            )

        # Verify faculty is the requester
        if swap.source_faculty_id != requester_id:
            return CancelResult(
                success=False,
                message="You are not the requester of this swap",
            )

        # Verify request is still pending
        if swap.status != SwapStatus.PENDING:
            return CancelResult(
                success=False,
                message=f"Cannot cancel request with status {swap.status.value}",
            )

        swap.status = SwapStatus.CANCELLED
        self.db.commit()

        return CancelResult(
            success=True,
            message="Swap request cancelled successfully",
        )

    def get_pending_requests(self) -> List[RequestDetail]:
        """
        Get all pending swap requests (admin view).

        Returns:
            List of all pending RequestDetail records
        """
        swaps = self.db.query(SwapRecord).filter(
            SwapRecord.status == SwapStatus.PENDING
        ).order_by(SwapRecord.requested_at.desc()).all()

        return [self._swap_to_detail(swap) for swap in swaps]

    def auto_match_requests(self) -> MatchResult:
        """
        Find compatible pairs of swap requests.

        Looks for mutual swaps where:
        - Faculty A wants to offload week X
        - Faculty B wants to offload week Y
        - Faculty A would accept week Y
        - Faculty B would accept week X

        Returns:
            MatchResult with potential matches
        """
        pending_swaps = self.db.query(SwapRecord).filter(
            SwapRecord.status == SwapStatus.PENDING
        ).all()

        matches = []

        for i, swap_a in enumerate(pending_swaps):
            for swap_b in pending_swaps[i + 1:]:
                # Check for mutual compatibility
                if (swap_a.target_week and swap_b.target_week and
                    swap_a.source_week == swap_b.target_week and
                    swap_b.source_week == swap_a.target_week):

                    # Validate both directions
                    valid_ab = self.validator.validate_swap(
                        source_faculty_id=swap_a.source_faculty_id,
                        source_week=swap_a.source_week,
                        target_faculty_id=swap_b.source_faculty_id,
                        target_week=swap_b.source_week,
                    )

                    valid_ba = self.validator.validate_swap(
                        source_faculty_id=swap_b.source_faculty_id,
                        source_week=swap_b.source_week,
                        target_faculty_id=swap_a.source_faculty_id,
                        target_week=swap_a.source_week,
                    )

                    if valid_ab.valid and valid_ba.valid:
                        matches.append((swap_a.id, swap_b.id))

        return MatchResult(
            matches_found=len(matches),
            potential_matches=matches,
            message=f"Found {len(matches)} compatible swap pairs",
        )

    def execute_matched_swap(self, request_id: UUID) -> ResponseResult:
        """
        Execute a swap that has been matched and approved.

        Args:
            request_id: The swap request ID to execute

        Returns:
            ResponseResult with execution outcome
        """
        swap = self.db.query(SwapRecord).filter(SwapRecord.id == request_id).first()
        if not swap:
            return ResponseResult(
                success=False,
                message="Swap request not found",
                errors=[ValidationError("NOT_FOUND", "Request does not exist")]
            )

        if swap.status != SwapStatus.APPROVED:
            return ResponseResult(
                success=False,
                message="Swap must be approved before execution",
                errors=[ValidationError("NOT_APPROVED", "Request not in approved state")]
            )

        # Execute the swap
        execution = self.executor.execute_swap(
            source_faculty_id=swap.source_faculty_id,
            source_week=swap.source_week,
            target_faculty_id=swap.target_faculty_id,
            target_week=swap.target_week,
            swap_type=swap.swap_type.value,
            reason=swap.reason,
        )

        if execution.success:
            swap.status = SwapStatus.EXECUTED
            swap.executed_at = datetime.utcnow()
            self.db.commit()

            # Notify parties
            self.notifier.notify_swap_executed(
                faculty_ids=[swap.source_faculty_id, swap.target_faculty_id],
                week=swap.source_week,
                swap_id=request_id,
                details=f"Matched swap executed successfully",
            )
            self.notifier.send_pending_notifications()

            return ResponseResult(
                success=True,
                message="Swap executed successfully",
                executed=True,
            )
        else:
            return ResponseResult(
                success=False,
                message=f"Execution failed: {execution.message}",
                errors=[ValidationError("EXECUTION_FAILED", execution.message)]
            )

    # Helper methods

    def _get_faculty(self, faculty_id: UUID) -> Optional[Person]:
        """Get a faculty member by ID."""
        return self.db.query(Person).filter(
            Person.id == faculty_id,
            Person.type == "faculty"
        ).first()

    def _is_week_assigned_to_faculty(self, faculty_id: UUID, week_start: date) -> bool:
        """Check if a week is assigned to a faculty member."""
        # Look for FMIT assignments in the week
        week_end = week_start + timedelta(days=6)

        assignment = self.db.query(Assignment).join(Block).filter(
            Assignment.person_id == faculty_id,
            Block.start_date <= week_end,
            Block.end_date >= week_start,
            # Assuming FMIT rotation has specific identifier
            # This might need adjustment based on actual data model
        ).first()

        # For now, return True as placeholder
        # TODO: Implement proper FMIT week verification
        return True

    def _find_compatible_candidates(
        self,
        source_faculty_id: UUID,
        source_week: date,
        desired_weeks: Optional[List[date]] = None,
    ) -> List[UUID]:
        """
        Find faculty who might be compatible swap partners.

        Uses preferences and availability to find candidates.
        """
        candidates = []

        # Find faculty who prefer this week
        preferred_candidates = self.preference_service.get_faculty_with_preference_for_week(
            week_date=source_week,
            exclude_faculty_ids=[source_faculty_id]
        )

        # Find faculty without blocks for this week
        available_candidates = self.preference_service.get_faculty_without_blocks_for_week(
            week_date=source_week,
            exclude_faculty_ids=[source_faculty_id]
        )

        # Prioritize faculty who prefer the week
        candidates.extend(preferred_candidates)

        # Add other available candidates
        for candidate_id in available_candidates:
            if candidate_id not in candidates:
                # Validate the swap would work
                validation = self.validator.validate_swap(
                    source_faculty_id=source_faculty_id,
                    source_week=source_week,
                    target_faculty_id=candidate_id,
                    target_week=desired_weeks[0] if desired_weeks else None,
                )

                if validation.valid:
                    candidates.append(candidate_id)

        return candidates[:5]  # Limit to top 5 candidates

    def _swap_to_detail(self, swap: SwapRecord) -> RequestDetail:
        """Convert SwapRecord to RequestDetail."""
        source_faculty = self._get_faculty(swap.source_faculty_id)
        target_faculty = self._get_faculty(swap.target_faculty_id)

        return RequestDetail(
            id=swap.id,
            status=swap.status,
            swap_type=swap.swap_type,
            source_faculty_id=swap.source_faculty_id,
            source_faculty_name=source_faculty.name if source_faculty else "Unknown",
            source_week=swap.source_week,
            target_faculty_id=swap.target_faculty_id,
            target_faculty_name=target_faculty.name if target_faculty else "Unknown",
            target_week=swap.target_week,
            reason=swap.reason,
            requested_at=swap.requested_at,
            approved_at=swap.approved_at,
            executed_at=swap.executed_at,
            can_cancel=swap.status == SwapStatus.PENDING,
            can_respond=swap.status == SwapStatus.PENDING,
            needs_approval=swap.status == SwapStatus.PENDING,
        )
