***REMOVED*** ADR-006: Swap System with Auto-Matching

**Date:** 2025-01 (Session 11)
**Status:** Adopted

***REMOVED******REMOVED*** Context

Medical residency schedules require flexibility for faculty and residents to exchange shifts due to:
- **Personal emergencies**: Family illness, childcare issues
- **Professional development**: Conference attendance, training opportunities
- **Work-life balance**: Preference-based shift exchanges

Manual swap coordination creates significant administrative burden:
- Coordinators manually search for compatible swap partners
- Time-consuming validation of ACGME compliance after swaps
- No audit trail for swap requests and approvals
- Risk of compliance violations if swaps are not validated

***REMOVED******REMOVED*** Decision

Build a **swap request system** with **automated matching**:
- Faculty/residents can request swaps via UI
- Auto-matcher finds compatible candidates based on:
  - Same rotation or compatible rotation types
  - Similar experience level (PGY-1, PGY-2, PGY-3)
  - ACGME compliance after swap
  - Availability and preferences
- All swaps validated for ACGME compliance before execution
- Full audit trail (request, approval, execution, rollback)
- 24-hour rollback window for reversing swaps

***REMOVED******REMOVED******REMOVED*** Swap Types

1. **One-to-One Swap**: Two people exchange shifts
2. **Absorb**: One person gives away shift (no reciprocation)
3. **Three-Way Swap**: A→B, B→C, C→A (future enhancement)

***REMOVED******REMOVED*** Consequences

***REMOVED******REMOVED******REMOVED*** Positive
- **Reduces coordinator burden**: Auto-matching eliminates manual search
- **Maintains ACGME compliance**: All swaps validated before execution
- **Audit trail**: Complete history for accreditation reviews
- **Faster turnaround**: Users get swap matches within seconds
- **Reduced errors**: Automated validation prevents compliance violations
- **User satisfaction**: Self-service swap requests improve autonomy

***REMOVED******REMOVED******REMOVED*** Negative
- **Matcher complexity**: Constraint satisfaction algorithm is non-trivial
- **Edge case handling**: Three-way swaps, absorbs, partial swaps require special logic
- **Performance concerns**: Matching algorithm may be slow for large rosters
- **False negatives**: Matcher may miss valid candidates due to conservative constraints
- **Rollback complexity**: Reverting swaps requires careful state management

***REMOVED******REMOVED*** Implementation

***REMOVED******REMOVED******REMOVED*** Swap Request Model
```python
class SwapRequest(Base):
    """Request to swap schedule assignments."""
    __tablename__ = "swap_requests"

    id: str
    requester_id: str
    requester_assignment_id: str
    swap_type: SwapType  ***REMOVED*** ONE_TO_ONE, ABSORB
    status: SwapStatus   ***REMOVED*** PENDING, APPROVED, EXECUTED, ROLLED_BACK
    created_at: datetime
    executed_at: datetime | None
    rollback_at: datetime | None
```

***REMOVED******REMOVED******REMOVED*** Auto-Matcher Algorithm
```python
class SwapMatcher:
    """Find compatible swap candidates."""

    async def find_matches(
        self,
        db: AsyncSession,
        request: SwapRequest
    ) -> list[SwapCandidate]:
        """
        Find compatible swap candidates.

        Matching criteria:
        1. Same or compatible rotation type
        2. Similar experience level
        3. ACGME compliance maintained after swap
        4. Candidate availability
        """
        ***REMOVED*** Get requester's assignment details
        requester_assignment = await self._get_assignment(db, request.requester_assignment_id)

        ***REMOVED*** Find all assignments on same date with compatible rotations
        candidates = await self._find_compatible_assignments(db, requester_assignment)

        ***REMOVED*** Filter by ACGME compliance
        valid_candidates = []
        for candidate in candidates:
            if await self._validate_swap_compliance(db, requester_assignment, candidate):
                valid_candidates.append(candidate)

        return valid_candidates
```

***REMOVED******REMOVED******REMOVED*** Swap Execution with Rollback
```python
class SwapExecutor:
    """Execute validated swaps with audit trail."""

    async def execute_swap(
        self,
        db: AsyncSession,
        swap_request: SwapRequest
    ) -> SwapResult:
        """
        Execute swap with atomic transaction.

        Steps:
        1. Validate ACGME compliance
        2. Create rollback snapshot
        3. Update assignments
        4. Mark swap as executed
        5. Send notifications
        """
        async with db.begin():
            ***REMOVED*** Validate compliance
            if not await self._validate_swap(db, swap_request):
                raise SwapValidationError("Swap violates ACGME rules")

            ***REMOVED*** Create rollback snapshot
            await self._create_rollback_snapshot(db, swap_request)

            ***REMOVED*** Execute swap
            await self._swap_assignments(db, swap_request)

            ***REMOVED*** Update swap status
            swap_request.status = SwapStatus.EXECUTED
            swap_request.executed_at = datetime.utcnow()

            await db.commit()

        ***REMOVED*** Send notifications
        await self._notify_swap_executed(swap_request)

        return SwapResult(success=True, swap_id=swap_request.id)
```

***REMOVED******REMOVED******REMOVED*** Rollback Mechanism
```python
async def rollback_swap(
    self,
    db: AsyncSession,
    swap_id: str
) -> RollbackResult:
    """
    Rollback swap within 24-hour window.

    Restores assignments to pre-swap state using snapshot.
    """
    swap = await self._get_swap(db, swap_id)

    ***REMOVED*** Check rollback window
    if datetime.utcnow() - swap.executed_at > timedelta(hours=24):
        raise RollbackWindowExpired("24-hour rollback window expired")

    ***REMOVED*** Restore from snapshot
    await self._restore_from_snapshot(db, swap)

    ***REMOVED*** Mark as rolled back
    swap.status = SwapStatus.ROLLED_BACK
    swap.rollback_at = datetime.utcnow()

    await db.commit()
```

***REMOVED******REMOVED*** References

- `backend/app/services/swap_matcher.py` - Auto-matching implementation
- `backend/app/services/swap_executor.py` - Swap execution with rollback
- `backend/app/models/swap.py` - Swap request model
- `backend/app/schemas/swap.py` - Pydantic schemas for swap API
- `backend/tests/services/test_swap_matcher.py` - Matcher test suite
- `docs/api/swap-system.md` - API documentation
