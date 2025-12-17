"""
Emergency Coverage Service.

Handles last-minute changes to the schedule:
- Military deployments
- TDY assignments
- Medical emergencies
- Family emergencies

Finds replacement coverage and protects critical services.
"""
from datetime import date
from uuid import UUID

from sqlalchemy.orm import Session

from app.models.absence import Absence
from app.models.assignment import Assignment
from app.models.block import Block
from app.models.person import Person


class EmergencyCoverageService:
    """Handle emergency coverage scenarios."""

    # Critical services that must be covered
    CRITICAL_ACTIVITIES = ["inpatient", "call", "emergency", "procedure"]

    def __init__(self, db: Session):
        self.db = db

    async def handle_emergency_absence(
        self,
        person_id: UUID,
        start_date: date,
        end_date: date,
        reason: str,
        is_deployment: bool = False,
    ) -> dict:
        """
        Find replacement coverage for emergency absence.

        Priority:
        1. Critical services (inpatient, call) - must be covered
        2. Clinic - can be rescheduled if no coverage available
        3. Education - can be missed

        Returns summary of replacements and gaps.
        """
        # Record the absence
        absence = Absence(
            person_id=person_id,
            start_date=start_date,
            end_date=end_date,
            absence_type="deployment" if is_deployment else "family_emergency",
            deployment_orders=is_deployment,
            replacement_activity=reason,
        )
        self.db.add(absence)

        # Find affected assignments
        affected = self._find_affected_assignments(person_id, start_date, end_date)

        replacements = []
        gaps = []
        details = []

        for assignment in affected:
            is_critical = self._is_critical_service(assignment)

            # Find replacement
            replacement = await self._find_replacement(assignment)

            if replacement:
                # Update assignment with new person
                old_person = self.db.query(Person).filter(
                    Person.id == assignment.person_id
                ).first()

                assignment.person_id = replacement.id
                assignment.notes = f"Replaced {old_person.name if old_person else 'Unknown'} due to: {reason}"

                replacements.append(assignment)
                details.append({
                    "block_id": str(assignment.block_id),
                    "original_person": old_person.name if old_person else "Unknown",
                    "replacement": replacement.name,
                    "is_critical": is_critical,
                    "status": "covered",
                })
            else:
                if is_critical:
                    # Critical gap - needs manual attention
                    gaps.append(assignment)
                    details.append({
                        "block_id": str(assignment.block_id),
                        "is_critical": is_critical,
                        "status": "UNCOVERED - REQUIRES ATTENTION",
                        "recommended_action": "Manual assignment needed",
                    })
                else:
                    # Non-critical - can be cancelled
                    self.db.delete(assignment)
                    details.append({
                        "block_id": str(assignment.block_id),
                        "is_critical": is_critical,
                        "status": "cancelled",
                        "recommended_action": "Reschedule when possible",
                    })

        self.db.commit()

        return {
            "status": "success" if not gaps else "partial",
            "replacements_found": len(replacements),
            "coverage_gaps": len(gaps),
            "requires_manual_review": len(gaps) > 0,
            "details": details,
        }

    def _find_affected_assignments(
        self, person_id: UUID, start_date: date, end_date: date
    ) -> list[Assignment]:
        """Find all assignments affected by the absence."""
        return (
            self.db.query(Assignment)
            .join(Block)
            .filter(
                Assignment.person_id == person_id,
                Block.date >= start_date,
                Block.date <= end_date,
            )
            .all()
        )

    def _is_critical_service(self, assignment: Assignment) -> bool:
        """Check if assignment is a critical service (24/7 coverage required)."""
        if assignment.rotation_template:
            activity_type = assignment.rotation_template.activity_type.lower()
            return any(
                keyword in activity_type for keyword in self.CRITICAL_ACTIVITIES
            )
        return False

    async def _find_replacement(self, assignment: Assignment) -> Person | None:
        """
        Find a replacement for the assignment.

        Strategy:
        1. Find residents not already assigned to this block
        2. Check availability (no absences)
        3. Match PGY level if possible
        4. Return best match or None
        """
        block = self.db.query(Block).filter(Block.id == assignment.block_id).first()
        if not block:
            return None

        # Get current person's details
        current_person = (
            self.db.query(Person).filter(Person.id == assignment.person_id).first()
        )

        # Find candidates (same type as current person)
        candidates = (
            self.db.query(Person)
            .filter(
                Person.type == current_person.type if current_person else "resident",
                Person.id != assignment.person_id,
            )
            .all()
        )

        # Filter out those already assigned to this block
        assigned_to_block = (
            self.db.query(Assignment.person_id)
            .filter(Assignment.block_id == assignment.block_id)
            .all()
        )
        assigned_ids = {a[0] for a in assigned_to_block}

        candidates = [c for c in candidates if c.id not in assigned_ids]

        # Filter out those with absences on this date
        absences_on_date = (
            self.db.query(Absence.person_id)
            .filter(
                Absence.start_date <= block.date,
                Absence.end_date >= block.date,
            )
            .all()
        )
        absent_ids = {a[0] for a in absences_on_date}

        candidates = [c for c in candidates if c.id not in absent_ids]

        if not candidates:
            return None

        # Prefer same PGY level
        if current_person and current_person.pgy_level:
            same_level = [
                c for c in candidates if c.pgy_level == current_person.pgy_level
            ]
            if same_level:
                return same_level[0]

        # Return first available
        return candidates[0]
