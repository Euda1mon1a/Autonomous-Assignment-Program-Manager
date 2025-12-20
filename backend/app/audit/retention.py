"""
Audit Log Retention Policy Management.

This module defines retention policies for audit logs, ensuring compliance
with regulatory requirements while managing storage costs.

Retention Levels:
---------------
- STANDARD: 90 days (default for most audit logs)
- COMPLIANCE: 1 year (for ACGME-related logs)
- LEGAL_HOLD: 7 years (for legal/regulatory requirements)
- PERMANENT: Never archived (critical system logs)

Policy Implementation:
--------------------
Policies determine:
- How long logs are kept in active database
- When logs are archived to compressed storage
- When archived logs can be purged
- Whether logs require special handling

Compliance Notes:
---------------
ACGME compliance logs (assignments, schedule runs) are automatically
assigned COMPLIANCE level retention (1 year active + 6 years archived).
"""

import logging
from datetime import datetime, timedelta
from enum import Enum
from typing import Any

from pydantic import BaseModel, Field

logger = logging.getLogger(__name__)


class RetentionLevel(str, Enum):
    """Retention level classifications."""

    STANDARD = "standard"  # 90 days active, 7 years archived
    COMPLIANCE = "compliance"  # 1 year active, 6 years archived
    LEGAL_HOLD = "legal_hold"  # 7 years active, permanent archived
    PERMANENT = "permanent"  # Never archived or purged


class RetentionPolicy(BaseModel):
    """
    Retention policy configuration.

    Defines how long audit logs are retained in active storage vs. archive.
    """

    level: RetentionLevel = Field(
        default=RetentionLevel.STANDARD,
        description="Retention classification level",
    )
    active_retention_days: int = Field(
        default=90,
        description="Days to keep logs in active database",
        ge=1,
    )
    archive_retention_years: int = Field(
        default=7,
        description="Years to keep logs in archive storage",
        ge=1,
    )
    entity_types: list[str] | None = Field(
        default=None,
        description="Entity types this policy applies to (None = all)",
    )
    require_approval: bool = Field(
        default=False,
        description="Require approval before archiving/purging",
    )
    compress_archives: bool = Field(
        default=True,
        description="Compress archives with gzip",
    )
    metadata: dict[str, Any] = Field(
        default_factory=dict,
        description="Additional policy metadata",
    )

    class Config:
        use_enum_values = True

    def should_archive(self, log_date: datetime) -> bool:
        """
        Check if logs from given date should be archived.

        Args:
            log_date: Date of the audit log

        Returns:
            bool: True if log should be archived
        """
        if self.level == RetentionLevel.PERMANENT:
            return False

        age_days = (datetime.utcnow() - log_date).days
        return age_days > self.active_retention_days

    def should_purge(self, archive_date: datetime) -> bool:
        """
        Check if archive from given date should be purged.

        Args:
            archive_date: Date when archive was created

        Returns:
            bool: True if archive should be purged
        """
        if self.level in (RetentionLevel.PERMANENT, RetentionLevel.LEGAL_HOLD):
            return False

        age_days = (datetime.utcnow() - archive_date).days
        return age_days > (self.archive_retention_years * 365)

    def get_archive_cutoff_date(self) -> datetime:
        """
        Get the cutoff date for archival.

        Returns:
            datetime: Logs older than this date should be archived
        """
        return datetime.utcnow() - timedelta(days=self.active_retention_days)

    def get_purge_cutoff_date(self) -> datetime:
        """
        Get the cutoff date for archive purging.

        Returns:
            datetime: Archives older than this date can be purged
        """
        return datetime.utcnow() - timedelta(days=self.archive_retention_years * 365)


# Predefined retention policies for common use cases

STANDARD_POLICY = RetentionPolicy(
    level=RetentionLevel.STANDARD,
    active_retention_days=90,
    archive_retention_years=7,
    compress_archives=True,
    metadata={
        "description": "Standard retention for general audit logs",
        "cost_tier": "low",
    },
)

COMPLIANCE_POLICY = RetentionPolicy(
    level=RetentionLevel.COMPLIANCE,
    active_retention_days=365,  # 1 year
    archive_retention_years=6,  # Total 7 years
    entity_types=["assignment", "schedule_run", "absence"],
    require_approval=False,
    compress_archives=True,
    metadata={
        "description": "ACGME compliance retention (7 years total)",
        "regulatory_basis": "ACGME requirements",
        "cost_tier": "medium",
    },
)

LEGAL_HOLD_POLICY = RetentionPolicy(
    level=RetentionLevel.LEGAL_HOLD,
    active_retention_days=2555,  # 7 years
    archive_retention_years=100,  # Effectively permanent
    require_approval=True,
    compress_archives=True,
    metadata={
        "description": "Legal hold - extended retention",
        "cost_tier": "high",
    },
)

PERMANENT_POLICY = RetentionPolicy(
    level=RetentionLevel.PERMANENT,
    active_retention_days=365000,  # Never archive
    archive_retention_years=100,
    require_approval=True,
    compress_archives=False,
    metadata={
        "description": "Permanent retention - never archived",
        "cost_tier": "critical",
    },
)


class RetentionPolicyManager:
    """
    Manages retention policies for different entity types.

    Provides policy selection, validation, and enforcement.
    """

    def __init__(self):
        """Initialize retention policy manager with default policies."""
        self.policies: dict[str, RetentionPolicy] = {
            "standard": STANDARD_POLICY,
            "compliance": COMPLIANCE_POLICY,
            "legal_hold": LEGAL_HOLD_POLICY,
            "permanent": PERMANENT_POLICY,
        }

        # Entity-specific policy mappings
        self.entity_policies: dict[str, str] = {
            "assignment": "compliance",
            "schedule_run": "compliance",
            "absence": "compliance",
            "swap_record": "standard",
            "user": "legal_hold",
        }

    def get_policy(self, entity_type: str | None = None) -> RetentionPolicy:
        """
        Get retention policy for entity type.

        Args:
            entity_type: Type of entity (assignment, absence, etc.)

        Returns:
            RetentionPolicy: Applicable retention policy
        """
        if entity_type and entity_type in self.entity_policies:
            policy_name = self.entity_policies[entity_type]
            return self.policies[policy_name]

        return self.policies["standard"]

    def register_policy(self, name: str, policy: RetentionPolicy) -> None:
        """
        Register a custom retention policy.

        Args:
            name: Policy name
            policy: RetentionPolicy instance
        """
        self.policies[name] = policy
        logger.info(f"Registered retention policy: {name}")

    def assign_entity_policy(self, entity_type: str, policy_name: str) -> None:
        """
        Assign a policy to an entity type.

        Args:
            entity_type: Type of entity
            policy_name: Name of policy to assign

        Raises:
            ValueError: If policy name is not registered
        """
        if policy_name not in self.policies:
            raise ValueError(f"Unknown policy: {policy_name}")

        self.entity_policies[entity_type] = policy_name
        logger.info(f"Assigned policy '{policy_name}' to entity type '{entity_type}'")

    def get_all_policies(self) -> dict[str, RetentionPolicy]:
        """
        Get all registered policies.

        Returns:
            dict: Mapping of policy names to RetentionPolicy instances
        """
        return self.policies.copy()

    def get_entity_mappings(self) -> dict[str, str]:
        """
        Get all entity-to-policy mappings.

        Returns:
            dict: Mapping of entity types to policy names
        """
        return self.entity_policies.copy()

    def calculate_archive_stats(self) -> dict[str, Any]:
        """
        Calculate statistics about retention policies.

        Returns:
            dict: Statistics including total policies, entity coverage, etc.
        """
        total_policies = len(self.policies)
        entities_with_policy = len(self.entity_policies)

        policy_usage = {}
        for entity_type, policy_name in self.entity_policies.items():
            policy_usage[policy_name] = policy_usage.get(policy_name, 0) + 1

        return {
            "total_policies": total_policies,
            "entities_with_policy": entities_with_policy,
            "policy_usage": policy_usage,
            "default_policy": "standard",
        }


# Global policy manager instance
_policy_manager: RetentionPolicyManager | None = None


def get_policy_manager() -> RetentionPolicyManager:
    """
    Get global retention policy manager instance.

    Returns:
        RetentionPolicyManager: Global policy manager
    """
    global _policy_manager
    if _policy_manager is None:
        _policy_manager = RetentionPolicyManager()
    return _policy_manager
