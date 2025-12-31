"""
Skill and credential validation for swaps.

Ensures faculty members have required skills and credentials
for the duties they'll assume after a swap.
"""

import logging
from dataclasses import dataclass
from datetime import date, datetime
from typing import Any
from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_

from app.models.swap import SwapRecord
from app.models.person import Person
from app.models.assignment import Assignment


logger = logging.getLogger(__name__)


@dataclass
class SkillCheckResult:
    """Result of skill validation."""

    qualified: bool
    missing_credentials: list[dict[str, Any]]
    expiring_soon: list[dict[str, Any]]
    warnings: list[str]


class SkillValidator:
    """
    Validates skill and credential requirements for swaps.

    Checks:
    - BLS/ACLS certifications
    - Procedure credentials
    - Specialty qualifications
    - License validity
    """

    REQUIRED_CREDENTIALS = {
        "inpatient": ["BLS", "ACLS", "HIPAA"],
        "emergency": ["BLS", "ACLS", "ATLS", "HIPAA"],
        "procedures": ["BLS", "ACLS", "procedure_privileges", "HIPAA"],
        "clinic": ["BLS", "HIPAA"],
    }

    def __init__(self, db: AsyncSession):
        """
        Initialize skill validator.

        Args:
            db: Async database session
        """
        self.db = db

    async def validate_skills(
        self,
        swap: SwapRecord,
    ) -> SkillCheckResult:
        """
        Validate skills for a swap.

        Args:
            swap: Swap request to validate

        Returns:
            SkillCheckResult with validation details
        """
        missing_credentials = []
        expiring_soon = []
        warnings = []

        # Check source faculty can do target's duties
        source_check = await self._check_faculty_credentials(
            swap.target_faculty_id,  # Check target's current duties
            swap.source_faculty_id,  # Against source's credentials
            swap.target_week or swap.source_week,
        )

        if source_check["missing"]:
            missing_credentials.extend(
                [
                    {
                        "faculty_id": str(swap.source_faculty_id),
                        "faculty_role": "source",
                        **cred,
                    }
                    for cred in source_check["missing"]
                ]
            )

        if source_check["expiring"]:
            expiring_soon.extend(source_check["expiring"])

        # Check target faculty can do source's duties
        target_check = await self._check_faculty_credentials(
            swap.source_faculty_id,  # Check source's current duties
            swap.target_faculty_id,  # Against target's credentials
            swap.source_week,
        )

        if target_check["missing"]:
            missing_credentials.extend(
                [
                    {
                        "faculty_id": str(swap.target_faculty_id),
                        "faculty_role": "target",
                        **cred,
                    }
                    for cred in target_check["missing"]
                ]
            )

        if target_check["expiring"]:
            expiring_soon.extend(target_check["expiring"])

        # Generate warnings
        if expiring_soon:
            warnings.append(
                f"{len(expiring_soon)} credentials expiring within 30 days"
            )

        qualified = len(missing_credentials) == 0

        logger.info(
            f"Skill validation for swap {swap.id}: "
            f"{'QUALIFIED' if qualified else 'CREDENTIALS MISSING'}"
        )

        return SkillCheckResult(
            qualified=qualified,
            missing_credentials=missing_credentials,
            expiring_soon=expiring_soon,
            warnings=warnings,
        )

    async def _check_faculty_credentials(
        self,
        duties_faculty_id: UUID,  # Who currently does these duties
        checking_faculty_id: UUID,  # Who we're checking can do them
        week: date,
    ) -> dict[str, Any]:
        """Check if faculty has credentials for specific duties."""
        missing = []
        expiring = []

        # Get the rotation types for the duties
        rotation_types = await self._get_faculty_rotation_types(
            duties_faculty_id,
            week,
        )

        # Get required credentials
        required_creds = set()
        for rotation_type in rotation_types:
            creds = self.REQUIRED_CREDENTIALS.get(rotation_type, [])
            required_creds.update(creds)

        # Check if checking_faculty has these credentials
        faculty_creds = await self._get_faculty_credentials(checking_faculty_id)

        for cred_name in required_creds:
            if cred_name not in faculty_creds:
                missing.append({
                    "credential": cred_name,
                    "required_for": list(rotation_types),
                })
            else:
                # Check expiration
                cred_info = faculty_creds[cred_name]
                if cred_info.get("expires_at"):
                    days_until_expiry = (
                        cred_info["expires_at"] - datetime.utcnow().date()
                    ).days

                    if days_until_expiry < 30:
                        expiring.append({
                            "credential": cred_name,
                            "expires_at": cred_info["expires_at"].isoformat(),
                            "days_until_expiry": days_until_expiry,
                        })

        return {
            "missing": missing,
            "expiring": expiring,
        }

    async def _get_faculty_rotation_types(
        self,
        faculty_id: UUID,
        week: date,
    ) -> set[str]:
        """Get rotation types for a faculty member's duties."""
        from datetime import timedelta

        week_end = week + timedelta(days=6)

        result = await self.db.execute(
            select(Assignment.rotation_type)
            .where(Assignment.person_id == faculty_id)
            .distinct()
        )

        rotation_types = set(result.scalars().all())

        # Remove None values
        rotation_types.discard(None)

        return rotation_types

    async def _get_faculty_credentials(
        self,
        faculty_id: UUID,
    ) -> dict[str, Any]:
        """Get faculty member's credentials."""
        # This would query the credentials table
        # For now, return a placeholder

        # In real implementation:
        # - Query credential records
        # - Check expiration dates
        # - Return dict of credential_name -> {expires_at, status}

        return {
            "BLS": {
                "expires_at": date(2025, 12, 31),
                "status": "active",
            },
            "ACLS": {
                "expires_at": date(2025, 6, 30),
                "status": "active",
            },
            "HIPAA": {
                "expires_at": date(2025, 12, 31),
                "status": "active",
            },
        }
