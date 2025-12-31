"""
Rotation Requirements Compliance Validator.

Implements ACGME rotation validation:
- Minimum rotation length enforcement
- Continuity clinic frequency validation
- Procedure volume tracking
- Educational milestone validation
- Rotation sequence compliance
- PGY-level specific requirements

This validator ensures residents complete required rotations
with adequate duration and sequencing for educational goals.
"""

import logging
from dataclasses import dataclass
from datetime import date
from typing import Optional
from uuid import UUID

logger = logging.getLogger(__name__)


# Rotation Constants
MIN_ROTATION_DAYS = 7  # Minimum ~1 week

# PGY-Level Requirements (annual targets)
PGY1_MIN_CLINIC_BLOCKS = 8
PGY2_MIN_CLINIC_BLOCKS = 8
PGY3_MIN_CLINIC_BLOCKS = 6
MIN_SPECIALTY_BLOCKS = 6
MIN_PROCEDURE_BLOCKS = 2

# Continuity clinic (weekly ongoing patient relationships)
MIN_CONTINUITY_CLINIC_FREQUENCY = 2  # Blocks per month

# Procedure volume targets per year
MIN_PROCEDURES_PER_YEAR = 50
MIN_PROCEDURES_PGY1 = 20
MIN_PROCEDURES_PGY2 = 30

# Conference attendance
MIN_CONFERENCE_ATTENDANCE = 0.95  # 95%


@dataclass
class RotationViolation:
    """Represents a rotation compliance violation."""

    person_id: UUID
    violation_type: str  # "minimum_length", "missing_required", "volume_shortfall"
    severity: str  # "CRITICAL", "HIGH", "MEDIUM"
    message: str
    rotation_name: str
    actual_value: int | float
    required_value: int | float


@dataclass
class RotationWarning:
    """Represents a rotation compliance warning."""

    person_id: UUID
    warning_type: str  # "approaching_end", "low_volume"
    message: str
    rotation_name: str
    current_value: int | float
    target_value: int | float


class RotationValidator:
    """
    Validates ACGME rotation requirements for residents.

    Rules:
    1. Minimum rotation length: ≥7 days per rotation
    2. Minimum clinic frequency: Each PGY level has minimum blocks
    3. Procedure volume: Adequate hands-on experience tracking
    4. Educational sequence: Required order and spacing
    5. Milestones: Competency assessment per rotation type
    """

    def __init__(self):
        """Initialize rotation validator."""
        self.min_rotation_days = MIN_ROTATION_DAYS
        self.pgy1_min_clinic = PGY1_MIN_CLINIC_BLOCKS
        self.pgy2_min_clinic = PGY2_MIN_CLINIC_BLOCKS
        self.pgy3_min_clinic = PGY3_MIN_CLINIC_BLOCKS
        self.min_specialty = MIN_SPECIALTY_BLOCKS
        self.min_procedures = MIN_PROCEDURE_BLOCKS

    def validate_minimum_rotation_length(
        self,
        person_id: UUID,
        rotation_name: str,
        start_date: date,
        end_date: date,
    ) -> RotationViolation | None:
        """
        Validate rotation meets minimum duration.

        Args:
            person_id: Resident ID
            rotation_name: Name of rotation
            start_date: Rotation start date
            end_date: Rotation end date

        Returns:
            RotationViolation if too short, None if adequate
        """
        duration = (end_date - start_date).days + 1

        if duration < self.min_rotation_days:
            return RotationViolation(
                person_id=person_id,
                violation_type="minimum_length",
                severity="MEDIUM",
                message=(
                    f"Rotation '{rotation_name}' is {duration} days "
                    f"(minimum {self.min_rotation_days} days required)"
                ),
                rotation_name=rotation_name,
                actual_value=duration,
                required_value=self.min_rotation_days,
            )

        return None

    def validate_pgy_level_clinic_requirements(
        self,
        person_id: UUID,
        pgy_level: int,
        clinic_blocks_completed: int,
        year_to_date: bool = False,
    ) -> RotationViolation | None:
        """
        Validate PGY-level minimum clinic block requirements.

        Args:
            person_id: Resident ID
            pgy_level: PGY level (1, 2, or 3)
            clinic_blocks_completed: Number of clinic blocks completed
            year_to_date: Whether measuring year-to-date (vs annual)

        Returns:
            RotationViolation if insufficient, None if adequate
        """
        if pgy_level == 1:
            minimum = self.pgy1_min_clinic
        elif pgy_level == 2:
            minimum = self.pgy2_min_clinic
        elif pgy_level == 3:
            minimum = self.pgy3_min_clinic
        else:
            return None  # Unknown PGY level

        if clinic_blocks_completed < minimum:
            deficit = minimum - clinic_blocks_completed
            period = "year-to-date" if year_to_date else "annual"
            return RotationViolation(
                person_id=person_id,
                violation_type="missing_required",
                severity="HIGH",
                message=(
                    f"PGY-{pgy_level} clinic requirement not met ({period}): "
                    f"{clinic_blocks_completed} blocks completed "
                    f"(minimum {minimum}, deficit {deficit})"
                ),
                rotation_name=f"PGY-{pgy_level} Clinic",
                actual_value=clinic_blocks_completed,
                required_value=minimum,
            )

        return None

    def validate_specialty_rotation_completion(
        self,
        person_id: UUID,
        pgy_level: int,
        specialty_blocks_completed: int,
    ) -> RotationViolation | None:
        """
        Validate specialty/elective rotation requirements (PGY-2/3).

        Args:
            person_id: Resident ID
            pgy_level: PGY level
            specialty_blocks_completed: Number of specialty blocks

        Returns:
            RotationViolation if insufficient, None if adequate
        """
        # PGY-1 not typically required specialty blocks
        if pgy_level < 2:
            return None

        if specialty_blocks_completed < self.min_specialty:
            deficit = self.min_specialty - specialty_blocks_completed
            return RotationViolation(
                person_id=person_id,
                violation_type="missing_required",
                severity="HIGH",
                message=(
                    f"Specialty rotation requirement not met: "
                    f"{specialty_blocks_completed} blocks completed "
                    f"(minimum {self.min_specialty}, deficit {deficit})"
                ),
                rotation_name="Specialty/Elective Rotations",
                actual_value=specialty_blocks_completed,
                required_value=self.min_specialty,
            )

        return None

    def validate_procedure_volume(
        self,
        person_id: UUID,
        pgy_level: int,
        procedures_completed: int,
        target_volume: int | None = None,
    ) -> tuple[RotationViolation | None, RotationWarning | None]:
        """
        Validate procedure volume requirements.

        Args:
            person_id: Resident ID
            pgy_level: PGY level
            procedures_completed: Number of procedures performed
            target_volume: Optional custom target (if not PGY-specific)

        Returns:
            (violation, warning) tuple
        """
        # Determine target based on PGY level
        if target_volume is None:
            if pgy_level == 1:
                target_volume = MIN_PROCEDURES_PGY1
            elif pgy_level == 2:
                target_volume = MIN_PROCEDURES_PGY2
            else:
                target_volume = MIN_PROCEDURES_PER_YEAR

        violation = None
        warning = None

        # Critical threshold: less than 60% of target
        if procedures_completed < target_volume * 0.6:
            violation = RotationViolation(
                person_id=person_id,
                violation_type="volume_shortfall",
                severity="HIGH",
                message=(
                    f"Low procedure volume: {procedures_completed} procedures "
                    f"(target {target_volume}, only "
                    f"{procedures_completed / target_volume * 100:.0f}% complete)"
                ),
                rotation_name="Procedures",
                actual_value=procedures_completed,
                required_value=target_volume,
            )
        # Warning threshold: less than 85% of target
        elif procedures_completed < target_volume * 0.85:
            warning = RotationWarning(
                person_id=person_id,
                warning_type="low_volume",
                message=(
                    f"Procedure volume below target: {procedures_completed}/"
                    f"{target_volume} ({procedures_completed / target_volume * 100:.0f}%)"
                ),
                rotation_name="Procedures",
                current_value=procedures_completed,
                target_value=target_volume,
            )

        return violation, warning

    def validate_rotation_sequence(
        self,
        person_id: UUID,
        pgy_level: int,
        completed_rotations: list[dict],
    ) -> list[RotationViolation]:
        """
        Validate rotation sequencing (order of rotations).

        Args:
            person_id: Resident ID
            pgy_level: PGY level
            completed_rotations: List of dicts with 'rotation_name', 'start_date',
                               'end_date'

        Returns:
            List of sequence violations
        """
        violations = []

        # PGY-1 specific rules
        if pgy_level == 1:
            # FMIT should be early (first 6 months ideally)
            rotation_names = [
                r.get("rotation_name", "").upper() for r in completed_rotations
            ]

            # Check if FMIT appears late
            if "FMIT" in rotation_names:
                fmit_index = rotation_names.index("FMIT")
                if fmit_index > 5:  # After 5 other rotations
                    violations.append(
                        RotationViolation(
                            person_id=person_id,
                            violation_type="missing_required",
                            severity="MEDIUM",
                            message=(
                                f"FMIT scheduled late for PGY-1 "
                                f"(position {fmit_index + 1}, recommended early)"
                            ),
                            rotation_name="FMIT",
                            actual_value=fmit_index + 1,
                            required_value=3,
                        )
                    )

        # PGY-2/3 rules
        if pgy_level >= 2:
            # Specialty rotations should be distributed (not clustered)
            rotation_names = [
                r.get("rotation_name", "").upper() for r in completed_rotations
            ]
            specialty_indices = [
                i
                for i, r in enumerate(rotation_names)
                if "SPECIALTY" in r or "ELECTIVE" in r or "DERM" in r or "NEURO" in r
            ]

            # Check for clustering (more than 2 consecutive specialty rotations)
            if len(specialty_indices) >= 3:
                consecutive_count = 1
                for i in range(1, len(specialty_indices)):
                    if specialty_indices[i] == specialty_indices[i - 1] + 1:
                        consecutive_count += 1
                        if consecutive_count > 2:
                            violations.append(
                                RotationViolation(
                                    person_id=person_id,
                                    violation_type="missing_required",
                                    severity="MEDIUM",
                                    message=(
                                        f"{consecutive_count} consecutive specialty "
                                        f"rotations found (recommend distribution)"
                                    ),
                                    rotation_name="Specialty Rotations",
                                    actual_value=consecutive_count,
                                    required_value=2,
                                )
                            )
                    else:
                        consecutive_count = 1

        return violations

    def validate_continuity_clinic_frequency(
        self,
        person_id: UUID,
        pgy_level: int,
        continuity_blocks_per_month: float,
    ) -> RotationWarning | None:
        """
        Validate longitudinal continuity clinic frequency.

        Args:
            person_id: Resident ID
            pgy_level: PGY level
            continuity_blocks_per_month: Average frequency per month

        Returns:
            RotationWarning if frequency too low, None otherwise
        """
        if continuity_blocks_per_month < MIN_CONTINUITY_CLINIC_FREQUENCY:
            return RotationWarning(
                person_id=person_id,
                warning_type="low_volume",
                message=(
                    f"Low continuity clinic frequency: "
                    f"{continuity_blocks_per_month:.1f} blocks/month "
                    f"(target {MIN_CONTINUITY_CLINIC_FREQUENCY}/month)"
                ),
                rotation_name="Continuity Clinic",
                current_value=continuity_blocks_per_month,
                target_value=MIN_CONTINUITY_CLINIC_FREQUENCY,
            )

        return None

    def validate_educational_milestone_completion(
        self,
        person_id: UUID,
        rotation_name: str,
        milestones_completed: dict[str, bool],
    ) -> list[RotationViolation]:
        """
        Validate educational milestones for rotation.

        Args:
            person_id: Resident ID
            rotation_name: Rotation name
            milestones_completed: Dict mapping milestone_name to completed (bool)

        Returns:
            List of violations for incomplete milestones
        """
        violations = []

        for milestone, completed in milestones_completed.items():
            if not completed:
                violations.append(
                    RotationViolation(
                        person_id=person_id,
                        violation_type="missing_required",
                        severity="MEDIUM",
                        message=(
                            f"Educational milestone incomplete: {milestone} "
                            f"for {rotation_name}"
                        ),
                        rotation_name=rotation_name,
                        actual_value=0,
                        required_value=1,
                    )
                )

        return violations

    def get_annual_rotation_summary(
        self,
        person_id: UUID,
        pgy_level: int,
        completed_rotations: list[dict],
        total_blocks_available: int = 26,
    ) -> dict:
        """
        Generate annual rotation summary for resident.

        Args:
            person_id: Resident ID
            pgy_level: PGY level
            completed_rotations: List of completed rotation dicts
            total_blocks_available: Total blocks in academic year

        Returns:
            Summary dict with rotation metrics
        """
        rotation_by_type = {}
        total_blocks = 0

        for rotation in completed_rotations:
            rot_type = rotation.get("rotation_type", "Other")
            blocks = rotation.get("blocks", 1)
            total_blocks += blocks

            if rot_type not in rotation_by_type:
                rotation_by_type[rot_type] = 0
            rotation_by_type[rot_type] += blocks

        clinic_blocks = rotation_by_type.get("Clinic", 0) + rotation_by_type.get(
            "Continuity Clinic", 0
        )
        specialty_blocks = rotation_by_type.get("Specialty", 0)
        inpatient_blocks = rotation_by_type.get("Inpatient", 0)

        return {
            "person_id": str(person_id),
            "pgy_level": pgy_level,
            "total_blocks_completed": total_blocks,
            "blocks_available": total_blocks_available,
            "utilization_rate": total_blocks / total_blocks_available
            if total_blocks_available > 0
            else 0,
            "rotation_breakdown": rotation_by_type,
            "clinic_blocks": clinic_blocks,
            "specialty_blocks": specialty_blocks,
            "inpatient_blocks": inpatient_blocks,
            "diversity_score": len(
                rotation_by_type
            ),  # Number of distinct rotation types
        }
