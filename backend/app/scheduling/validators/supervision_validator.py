"""
Supervision Ratio Compliance Validator.

Implements ACGME supervision ratio requirements:
- PGY-1: 1 faculty per 2 residents (direct/immediate supervision)
- PGY-2/3: 1 faculty per 4 residents (available supervision)

This validator uses fractional load approach for mixed PGY scenarios,
ensuring accurate calculation of required faculty coverage.
"""

import functools
import logging
from dataclasses import dataclass
from datetime import date
from typing import Optional
from uuid import UUID

logger = logging.getLogger(__name__)


# ACGME Supervision Constants
PGY1_RATIO = 2  # 1 faculty per 2 PGY-1 residents
OTHER_RATIO = 4  # 1 faculty per 4 PGY-2/3 residents


@dataclass
class SupervisionViolation:
    """Represents a supervision ratio compliance violation."""

    block_id: UUID | None
    block_date: date
    residents: int
    pgy1_count: int
    pgy2_3_count: int
    required_faculty: int
    actual_faculty: int
    deficit: int
    severity: str  # "CRITICAL", "HIGH"
    message: str


class SupervisionValidator:
    """
    Validates ACGME supervision ratio compliance for resident assignments.

    Rules:
    1. PGY-1 Supervision: 1 faculty per 2 PGY-1 residents (direct)
    2. PGY-2/3 Supervision: 1 faculty per 4 PGY-2/3 residents (available)
    3. Fractional Load: Mixed scenarios use combined calculation

    Formula (Fractional Load Approach):
    - PGY-1 residents = 2 supervision units each
    - PGY-2/3 residents = 1 supervision unit each
    - Required faculty = ceil(total_units / 4)
    """

    def __init__(self) -> None:
        """Initialize supervision validator."""
        self.pgy1_ratio = PGY1_RATIO
        self.other_ratio = OTHER_RATIO

    def calculate_required_faculty(self, pgy1_count: int, other_count: int) -> int:
        """
        Calculate required faculty using fractional supervision units.

        Algorithm:
        1. PGY-1 residents = 2 supervision units each (1:2 ratio)
        2. PGY-2/3 residents = 1 supervision unit each (1:4 ratio)
        3. Sum all units
        4. Apply ceiling division by 4
        5. Return max(1, result) if any residents, else 0

        Args:
            pgy1_count: Number of PGY-1 residents
            other_count: Number of PGY-2/3 residents

        Returns:
            Required faculty count (ceiling)
        """
        # Calculate supervision units
        supervision_units = (pgy1_count * 2) + other_count

        if supervision_units == 0:
            return 0

        # Apply ceiling division: ceil(n/4) = (n+3)//4
        return (supervision_units + 3) // 4

    def validate_block_supervision(
        self,
        block_id: UUID | None,
        block_date: date,
        pgy1_residents: list[UUID],
        other_residents: list[UUID],
        faculty_assigned: list[UUID],
    ) -> SupervisionViolation | None:
        """
        Validate supervision for a single clinical block.

        Args:
            block_id: Block identifier
            block_date: Date of block
            pgy1_residents: List of PGY-1 resident IDs
            other_residents: List of PGY-2/3 resident IDs
            faculty_assigned: List of faculty member IDs

        Returns:
            SupervisionViolation if inadequate, None if compliant
        """
        pgy1_count = len(pgy1_residents) if pgy1_residents else 0
        other_count = len(other_residents) if other_residents else 0
        actual_faculty = len(faculty_assigned) if faculty_assigned else 0

        # Calculate requirement
        required = self.calculate_required_faculty(pgy1_count, other_count)

        # Check compliance
        if actual_faculty >= required:
            return None  # Compliant

        # Calculate deficit
        deficit = required - actual_faculty

        # Determine severity
        severity = "CRITICAL" if deficit >= 2 else "HIGH"

        # Create violation
        message = (
            f"Block {block_date} needs {required} faculty but has {actual_faculty} "
            f"(deficit: {deficit}) for {pgy1_count} PGY-1 + {other_count} PGY-2/3"
        )

        return SupervisionViolation(
            block_id=block_id,
            block_date=block_date,
            residents=pgy1_count + other_count,
            pgy1_count=pgy1_count,
            pgy2_3_count=other_count,
            required_faculty=required,
            actual_faculty=actual_faculty,
            deficit=deficit,
            severity=severity,
            message=message,
        )

    def validate_period_supervision(
        self,
        period_blocks: list[dict],
    ) -> tuple[list[SupervisionViolation], dict]:
        """
        Validate supervision across entire period.

        Args:
            period_blocks: List of dicts with keys:
                          'block_id', 'block_date', 'pgy1_residents',
                          'other_residents', 'faculty_assigned'

        Returns:
            (violations, metrics) tuple where metrics contains:
            - total_blocks: Total blocks analyzed
            - blocks_with_violations: Count of non-compliant blocks
            - compliance_rate: Percentage compliant
            - supervision_load_factors: Distribution of ratios
        """
        violations = []
        total_blocks = len(period_blocks)
        blocks_with_violations_count = 0

        # Track supervision load distribution
        load_distribution = {
            "all_compliant": 0,
            "single_deficit": 0,
            "multi_deficit": 0,
            "no_residents": 0,
        }

        for block_data in period_blocks:
            violation = self.validate_block_supervision(
                block_id=block_data.get("block_id"),
                block_date=block_data.get("block_date"),
                pgy1_residents=block_data.get("pgy1_residents", []),
                other_residents=block_data.get("other_residents", []),
                faculty_assigned=block_data.get("faculty_assigned", []),
            )

            if violation:
                violations.append(violation)
                blocks_with_violations_count += 1
                if violation.deficit >= 2:
                    load_distribution["multi_deficit"] += 1
                else:
                    load_distribution["single_deficit"] += 1
            elif (
                len(block_data.get("pgy1_residents", []))
                + len(block_data.get("other_residents", []))
            ) == 0:
                load_distribution["no_residents"] += 1
            else:
                load_distribution["all_compliant"] += 1

        # Calculate compliance rate
        compliance_rate = (
            ((total_blocks - blocks_with_violations_count) / total_blocks * 100)
            if total_blocks > 0
            else 100.0
        )

        metrics = {
            "total_blocks": total_blocks,
            "blocks_with_violations": blocks_with_violations_count,
            "compliance_rate": compliance_rate,
            "supervision_load_factors": load_distribution,
        }

        return violations, metrics

    def validate_attending_availability(
        self,
        faculty_id: UUID,
        faculty_availability: dict[date, bool],
        required_dates: list[date],
    ) -> str | None:
        """
        Validate that supervising faculty are available for required dates.

        Args:
            faculty_id: Faculty member ID
            faculty_availability: Dict mapping date to availability (True/False)
            required_dates: Dates when supervision is required

        Returns:
            Message if unavailable, None if all required dates covered
        """
        unavailable_dates = [
            d for d in required_dates if not faculty_availability.get(d, False)
        ]

        if unavailable_dates:
            return (
                f"Faculty {faculty_id} unavailable on "
                f"{len(unavailable_dates)} required supervision dates"
            )

        return None

    def validate_specialty_supervision(
        self,
        specialty_rotation: str,
        supervising_faculty: list[dict],
    ) -> tuple[bool, str | None]:
        """
        Validate that specialty rotation has appropriate supervising faculty.

        Args:
            specialty_rotation: Specialty type (e.g., 'Sports Medicine')
            supervising_faculty: List of faculty dicts with 'id' and 'specialties'

        Returns:
            (is_valid, error_message) tuple
        """
        # Check if any faculty has required specialty
        for faculty in supervising_faculty:
            specialties = faculty.get("specialties", [])
            if specialty_rotation in specialties:
                return True, None

        return False, (
            f"No supervising faculty with {specialty_rotation} specialty "
            f"available for supervision"
        )

    def validate_procedure_supervision(
        self,
        procedure_type: str,
        supervising_faculty: list[dict],
    ) -> tuple[bool, str | None]:
        """
        Validate that procedure rotation has qualified supervising faculty.

        Args:
            procedure_type: Procedure type (e.g., 'Minor Procedures')
            supervising_faculty: List of faculty dicts with procedure certifications

        Returns:
            (is_valid, error_message) tuple
        """
        # Check if any faculty certified for procedure
        for faculty in supervising_faculty:
            certifications = faculty.get("procedure_certifications", [])
            if procedure_type in certifications:
                return True, None

        return False, (
            f"No supervising faculty certified for {procedure_type} "
            f"available for supervision"
        )

    def get_supervision_deficit_report(
        self, violations: list[SupervisionViolation]
    ) -> dict:
        """
        Generate summary report of supervision deficits.

        Args:
            violations: List of supervision violations

        Returns:
            Report dict with:
            - total_violations: Count
            - critical_count: Violations with deficit >= 2
            - high_count: Violations with deficit == 1
            - total_deficit: Sum of all deficits
            - worst_case: Block with largest deficit
            - by_date: Violations grouped by date
        """
        if not violations:
            return {
                "total_violations": 0,
                "critical_count": 0,
                "high_count": 0,
                "total_deficit": 0,
                "worst_case": None,
                "by_date": {},
            }

        critical = [v for v in violations if v.deficit >= 2]
        high = [v for v in violations if v.deficit == 1]
        total_deficit = sum(v.deficit for v in violations)

        worst_case = max(violations, key=lambda v: v.deficit)

        by_date = {}
        for violation in violations:
            date_key = str(violation.block_date)
            if date_key not in by_date:
                by_date[date_key] = []
            by_date[date_key].append(violation.message)

        return {
            "total_violations": len(violations),
            "critical_count": len(critical),
            "high_count": len(high),
            "total_deficit": total_deficit,
            "worst_case": {
                "date": worst_case.block_date,
                "deficit": worst_case.deficit,
                "message": worst_case.message,
            },
            "by_date": by_date,
        }
