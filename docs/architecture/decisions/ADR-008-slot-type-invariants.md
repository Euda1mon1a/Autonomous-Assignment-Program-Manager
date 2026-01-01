# ADR-008: Slot-Type Invariants for Credentials

**Date:** 2025-12 (Session 29)
**Status:** Adopted

## Context

Medical residency programs face significant administrative burden tracking credentials:
- **Annual training requirements**: HIPAA, Cyber Awareness, AUP (Acceptable Use Policy)
- **Immunizations**: Flu vaccine, Tdap, Hepatitis B, TB testing
- **Safety certifications**: N95 fit testing, Bloodborne Pathogens, Chaperone training
- **Procedure credentials**: BLS, ACLS, PALS, NRP certifications

Current problems:
- **Reactive failures**: Assignments fail when credentials expire mid-rotation
- **Manual tracking**: Coordinators manually verify who has which certifications
- **No proactive reminders**: Coordinators discover expired credentials when assignments fail
- **Compliance risk**: Residents working without required credentials

Traditional approaches track credentials separately from scheduling, creating synchronization problems.

## Decision

Define **credential requirements as slot-type invariants**:
- Each slot type (inpatient call, clinic, procedures) specifies required credentials
- **Hard constraints**: Must have (HIPAA, Cyber, N95) - blocks assignment if missing
- **Soft constraints**: Penalty if expiring soon (14/30/60 day windows)
- Dashboard shows "next block failures" and "expiring in X days"
- Scheduler validates credentials during schedule generation

### Invariant Catalog Structure
```python
invariant_catalog = {
    "inpatient_call": {
        "hard": ["HIPAA", "Cyber_Training", "AUP", "Chaperone", "N95_Fit"],
        "soft": [{"name": "expiring_soon", "window_days": 14, "penalty": 3}]
    },
    "peds_clinic": {
        "hard": ["Flu_Vax", "Tdap", "HIPAA"],
        "soft": [{"name": "expiring_soon", "window_days": 30, "penalty": 2}]
    },
    "procedures_half_day": {
        "hard": ["BBP_Module", "Sharps_Safety", "BLS"],
        "soft": []
    },
    "ed_rotation": {
        "hard": ["ACLS", "PALS", "HIPAA", "N95_Fit"],
        "soft": [{"name": "expiring_soon", "window_days": 14, "penalty": 5}]
    }
}
```

## Consequences

### Positive
- **Prevents invalid assignments**: Schedule generation rejects assignments with missing credentials
- **Proactive renewal reminders**: Dashboard shows credentials expiring in 30/60/90 days
- **Reduced admin burden**: Automated checks replace manual verification
- **Compliance enforcement**: Cannot assign residents to slots without required credentials
- **Transparency**: Clear visibility into credential status across entire program
- **Early warning**: Soft constraints flag expiring credentials before they become blockers

### Negative
- **Initial setup burden**: Must define invariants for each slot type
- **Credential tracking infrastructure**: Requires database schema and UI for credential management
- **Maintenance overhead**: Invariant catalog must be updated when requirements change
- **False positives**: Conservative constraints may prevent valid assignments
- **Grace period complexity**: Handling temporary exceptions (new residents, recent renewals)

## Implementation

### Credential Model
```python
class Credential(Base):
    """Track faculty/resident credentials and certifications."""
    __tablename__ = "credentials"

    id: str
    person_id: str
    credential_type: str  # "HIPAA", "BLS", "N95_Fit"
    issued_at: date
    expires_at: date
    is_valid: bool
    verification_status: str  # "verified", "pending", "expired"
    document_url: str | None  # S3 link to certificate
```

### Eligibility Check
```python
class SlotTypeValidator:
    """Validate credential requirements for slot types."""

    def is_eligible(
        self,
        person_id: str,
        slot_type: str,
        assignment_date: date
    ) -> tuple[bool, int]:
        """
        Check if person meets slot requirements.

        Returns:
            (eligible: bool, penalty: int)
            - eligible=False if hard constraint fails
            - penalty>0 if soft constraint triggered
        """
        reqs = invariant_catalog.get(slot_type, {})

        # Check hard constraints (must pass all)
        for req in reqs.get("hard", []):
            cred = self._get_credential(person_id, req)
            if not cred or not cred.is_valid or cred.expires_at < assignment_date:
                return False, 0  # Hard failure

        # Check soft constraints (accumulate penalties)
        penalty = 0
        for soft in reqs.get("soft", []):
            if soft["name"] == "expiring_soon":
                if self._any_credential_expiring(
                    person_id,
                    soft["window_days"],
                    assignment_date
                ):
                    penalty += soft["penalty"]

        return True, penalty
```

### Dashboard Integration
```python
class CredentialDashboard:
    """Dashboard for credential monitoring."""

    async def get_next_block_failures(
        self,
        db: AsyncSession
    ) -> list[CredentialFailure]:
        """
        Find residents who cannot work their next scheduled block
        due to missing or expired credentials.
        """
        next_week = date.today() + timedelta(days=7)

        failures = []
        assignments = await self._get_upcoming_assignments(db, next_week)

        for assignment in assignments:
            slot_type = assignment.rotation.slot_type
            eligible, _ = self.validator.is_eligible(
                assignment.person_id,
                slot_type,
                assignment.date
            )

            if not eligible:
                failures.append(CredentialFailure(
                    person=assignment.person,
                    assignment=assignment,
                    missing_credentials=self._find_missing_credentials(
                        assignment.person_id,
                        slot_type,
                        assignment.date
                    )
                ))

        return failures

    async def get_expiring_credentials(
        self,
        db: AsyncSession,
        window_days: int
    ) -> list[ExpiringCredential]:
        """
        Find credentials expiring within X days.

        Args:
            window_days: 30, 60, or 90 day window
        """
        cutoff_date = date.today() + timedelta(days=window_days)

        result = await db.execute(
            select(Credential)
            .where(Credential.expires_at <= cutoff_date)
            .where(Credential.expires_at >= date.today())
            .where(Credential.is_valid == True)
        )

        return result.scalars().all()
```

### Schedule Generation Integration
```python
class ScheduleGenerator:
    """Generate schedules with credential validation."""

    async def generate_schedule(
        self,
        db: AsyncSession,
        params: ScheduleParams
    ) -> Schedule:
        """Generate schedule respecting credential invariants."""

        # Build constraint model
        model = cp_model.CpModel()

        # For each assignment variable
        for person_id, slot_type, date in assignments:
            eligible, penalty = self.validator.is_eligible(
                person_id,
                slot_type,
                date
            )

            # Hard constraint: cannot assign if ineligible
            if not eligible:
                model.Add(assignment_var == 0)

            # Soft constraint: penalize if credentials expiring soon
            if penalty > 0:
                objective_terms.append(-penalty * assignment_var)

        # Solve with constraints
        solver = cp_model.CpSolver()
        status = solver.Solve(model)

        return self._extract_schedule(solver, model)
```

### Common Credential Categories

| Category | Examples | Typical Validity |
|----------|----------|------------------|
| Annual Training | JKO Cyber Awareness, HIPAA, AUP | 12 months |
| Immunizations | Flu, Tdap, Hep B, TB test | Varies (6-24 months) |
| Safety | N95 Fit, Bloodborne Pathogens, Chaperone | 12-24 months |
| Procedures | BLS, ACLS, PALS, NRP | 24 months |
| Specialty | DEA license, Board certification | Varies |

## References

- `docs/constraints/SLOT_TYPE_INVARIANTS.md` - Detailed invariant documentation
- `backend/app/models/credential.py` - Credential model
- `backend/app/services/credential_validator.py` - Validation service
- `backend/app/scheduling/constraints/credentials.py` - Scheduler integration
- `backend/tests/services/test_credential_validator.py` - Test suite
- `frontend/app/credentials/dashboard/page.tsx` - Dashboard UI
