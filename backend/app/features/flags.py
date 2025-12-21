"""Feature flag service for managing and evaluating feature flags.

This service provides the main interface for:
- Creating, updating, and deleting feature flags
- Evaluating flags for users
- Tracking evaluation history
- Audit logging for compliance
"""
import uuid
from datetime import datetime
from typing import Any

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import get_settings
from app.features.evaluator import FeatureFlagEvaluator
from app.features.storage import (
    DatabaseStorageBackend,
    FeatureFlagStorageBackend,
    InMemoryStorageBackend,
)
from app.models.feature_flag import (
    FeatureFlag,
    FeatureFlagAudit,
    FeatureFlagEvaluation,
)

settings = get_settings()


class FeatureFlagService:
    """
    Service for managing and evaluating feature flags.

    Handles all business logic for feature flags including:
    - CRUD operations
    - Flag evaluation with targeting
    - Audit logging
    - Evaluation tracking
    """

    def __init__(
        self,
        db: AsyncSession,
        storage_backend: FeatureFlagStorageBackend | None = None,
        environment: str | None = None
    ):
        """
        Initialize feature flag service.

        Args:
            db: Database session
            storage_backend: Storage backend (defaults to database)
            environment: Current environment (development, staging, production)
        """
        self.db = db
        self.storage = storage_backend or DatabaseStorageBackend(db)
        self.environment = environment or "production"
        self.evaluator = FeatureFlagEvaluator(environment=self.environment)

    async def create_flag(
        self,
        key: str,
        name: str,
        description: str | None = None,
        flag_type: str = 'boolean',
        enabled: bool = False,
        rollout_percentage: float | None = None,
        environments: list[str] | None = None,
        target_user_ids: list[str] | None = None,
        target_roles: list[str] | None = None,
        variants: dict[str, float] | None = None,
        dependencies: list[str] | None = None,
        custom_attributes: dict[str, Any] | None = None,
        created_by: str | None = None,
    ) -> FeatureFlag:
        """
        Create a new feature flag.

        Args:
            key: Unique flag key
            name: Human-readable name
            description: Detailed description
            flag_type: Type of flag (boolean, percentage, variant)
            enabled: Whether flag is enabled
            rollout_percentage: Percentage rollout (0.0-1.0)
            environments: Target environments
            target_user_ids: Target user IDs
            target_roles: Target roles
            variants: A/B test variants
            dependencies: Prerequisite flag keys
            custom_attributes: Custom targeting attributes
            created_by: User ID who created the flag

        Returns:
            Created FeatureFlag instance

        Raises:
            ValueError: If flag key already exists
        """
        # Check if flag already exists
        existing = await self.db.execute(
            select(FeatureFlag).where(FeatureFlag.key == key)
        )
        if existing.scalar_one_or_none():
            raise ValueError(f"Feature flag with key '{key}' already exists")

        # Create flag
        flag = FeatureFlag(
            id=uuid.uuid4(),
            key=key,
            name=name,
            description=description,
            flag_type=flag_type,
            enabled=enabled,
            rollout_percentage=rollout_percentage,
            environments=environments,
            target_user_ids=target_user_ids,
            target_roles=target_roles,
            variants=variants,
            dependencies=dependencies,
            custom_attributes=custom_attributes,
            created_by=uuid.UUID(created_by) if created_by else None,
        )

        self.db.add(flag)
        await self.db.commit()
        await self.db.refresh(flag)

        # Log creation
        await self._log_audit(
            flag_id=flag.id,
            user_id=created_by,
            action='created',
            changes={'key': key, 'name': name, 'enabled': enabled},
            reason='Flag created'
        )

        return flag

    async def update_flag(
        self,
        key: str,
        updates: dict[str, Any],
        updated_by: str | None = None,
        reason: str | None = None
    ) -> FeatureFlag:
        """
        Update an existing feature flag.

        Args:
            key: Flag key to update
            updates: Dict of fields to update
            updated_by: User ID who updated the flag
            reason: Reason for update

        Returns:
            Updated FeatureFlag instance

        Raises:
            ValueError: If flag not found
        """
        result = await self.db.execute(
            select(FeatureFlag).where(FeatureFlag.key == key)
        )
        flag = result.scalar_one_or_none()

        if flag is None:
            raise ValueError(f"Feature flag with key '{key}' not found")

        # Track changes for audit
        changes = {}
        for field, new_value in updates.items():
            if hasattr(flag, field):
                old_value = getattr(flag, field)
                if old_value != new_value:
                    changes[field] = {'old': old_value, 'new': new_value}
                    setattr(flag, field, new_value)

        if changes:
            await self.db.commit()
            await self.db.refresh(flag)

            # Log update
            await self._log_audit(
                flag_id=flag.id,
                user_id=updated_by,
                action='updated',
                changes=changes,
                reason=reason
            )

        return flag

    async def delete_flag(
        self,
        key: str,
        deleted_by: str | None = None,
        reason: str | None = None
    ) -> bool:
        """
        Delete a feature flag.

        Args:
            key: Flag key to delete
            deleted_by: User ID who deleted the flag
            reason: Reason for deletion

        Returns:
            True if deleted, False if not found
        """
        result = await self.db.execute(
            select(FeatureFlag).where(FeatureFlag.key == key)
        )
        flag = result.scalar_one_or_none()

        if flag is None:
            return False

        # Log deletion before actually deleting
        await self._log_audit(
            flag_id=flag.id,
            user_id=deleted_by,
            action='deleted',
            changes={'key': key},
            reason=reason
        )

        await self.db.delete(flag)
        await self.db.commit()

        return True

    async def get_flag(self, key: str) -> FeatureFlag | None:
        """
        Get a feature flag by key.

        Args:
            key: Flag key

        Returns:
            FeatureFlag instance or None if not found
        """
        result = await self.db.execute(
            select(FeatureFlag).where(FeatureFlag.key == key)
        )
        return result.scalar_one_or_none()

    async def list_flags(
        self,
        enabled_only: bool = False,
        environment: str | None = None
    ) -> list[FeatureFlag]:
        """
        List all feature flags.

        Args:
            enabled_only: Only return enabled flags
            environment: Filter by environment

        Returns:
            List of FeatureFlag instances
        """
        query = select(FeatureFlag)

        if enabled_only:
            query = query.where(FeatureFlag.enabled == True)

        if environment:
            # Filter flags that target this environment or all environments (null)
            query = query.where(
                (FeatureFlag.environments.is_(None)) |
                (FeatureFlag.environments.contains([environment]))
            )

        result = await self.db.execute(query)
        return list(result.scalars().all())

    async def evaluate_flag(
        self,
        key: str,
        user_id: str | None = None,
        user_role: str | None = None,
        context: dict[str, Any] | None = None,
        track_evaluation: bool = True
    ) -> tuple[bool, str | None, str]:
        """
        Evaluate a feature flag for a given context.

        Args:
            key: Flag key to evaluate
            user_id: User ID for targeting
            user_role: User role for targeting
            context: Additional context
            track_evaluation: Whether to record evaluation in database

        Returns:
            Tuple of (enabled: bool, variant: str | None, reason: str)
        """
        # Get flag from storage
        flag = await self.get_flag(key)

        if flag is None:
            return False, None, f"Flag '{key}' not found"

        # Convert to dict for evaluator
        flag_data = {
            'key': flag.key,
            'enabled': flag.enabled,
            'flag_type': flag.flag_type,
            'rollout_percentage': flag.rollout_percentage,
            'environments': flag.environments,
            'target_user_ids': flag.target_user_ids,
            'target_roles': flag.target_roles,
            'variants': flag.variants,
            'dependencies': flag.dependencies,
            'custom_attributes': flag.custom_attributes,
        }

        # Evaluate flag
        enabled, variant, reason = self.evaluator.evaluate(
            flag_data=flag_data,
            user_id=user_id,
            user_role=user_role,
            context=context
        )

        # Track evaluation if requested
        if track_evaluation:
            await self._track_evaluation(
                flag_id=flag.id,
                user_id=user_id,
                user_role=user_role,
                enabled=enabled,
                variant=variant,
                context=context
            )

        return enabled, variant, reason

    async def evaluate_flags_bulk(
        self,
        flag_keys: list[str],
        user_id: str | None = None,
        user_role: str | None = None,
        context: dict[str, Any] | None = None,
        track_evaluation: bool = False
    ) -> dict[str, tuple[bool, str | None, str]]:
        """
        Evaluate multiple feature flags at once.

        Args:
            flag_keys: List of flag keys to evaluate
            user_id: User ID for targeting
            user_role: User role for targeting
            context: Additional context
            track_evaluation: Whether to record evaluations

        Returns:
            Dict mapping flag key to (enabled, variant, reason)
        """
        results = {}

        for key in flag_keys:
            results[key] = await self.evaluate_flag(
                key=key,
                user_id=user_id,
                user_role=user_role,
                context=context,
                track_evaluation=track_evaluation
            )

        return results

    async def get_stats(self) -> dict[str, Any]:
        """
        Get feature flag statistics.

        Returns:
            Dict with statistics about flags
        """
        # Count total flags
        total_result = await self.db.execute(select(func.count(FeatureFlag.id)))
        total_flags = total_result.scalar()

        # Count enabled flags
        enabled_result = await self.db.execute(
            select(func.count(FeatureFlag.id)).where(FeatureFlag.enabled == True)
        )
        enabled_flags = enabled_result.scalar()

        # Count by type
        percentage_result = await self.db.execute(
            select(func.count(FeatureFlag.id)).where(FeatureFlag.flag_type == 'percentage')
        )
        percentage_flags = percentage_result.scalar()

        variant_result = await self.db.execute(
            select(func.count(FeatureFlag.id)).where(FeatureFlag.flag_type == 'variant')
        )
        variant_flags = variant_result.scalar()

        # Count recent evaluations (last 24 hours)
        from datetime import timedelta
        yesterday = datetime.utcnow() - timedelta(days=1)
        recent_eval_result = await self.db.execute(
            select(func.count(FeatureFlagEvaluation.id)).where(
                FeatureFlagEvaluation.evaluated_at >= yesterday
            )
        )
        recent_evaluations = recent_eval_result.scalar()

        # Count unique users in evaluations (last 24 hours)
        unique_users_result = await self.db.execute(
            select(func.count(func.distinct(FeatureFlagEvaluation.user_id))).where(
                FeatureFlagEvaluation.evaluated_at >= yesterday,
                FeatureFlagEvaluation.user_id.isnot(None)
            )
        )
        unique_users = unique_users_result.scalar()

        return {
            'total_flags': total_flags,
            'enabled_flags': enabled_flags,
            'disabled_flags': total_flags - enabled_flags,
            'percentage_rollout_flags': percentage_flags,
            'variant_flags': variant_flags,
            'recent_evaluations': recent_evaluations,
            'unique_users': unique_users,
        }

    async def _log_audit(
        self,
        flag_id: uuid.UUID,
        user_id: str | None,
        action: str,
        changes: dict[str, Any] | None = None,
        reason: str | None = None
    ) -> None:
        """
        Log an audit entry for a flag change.

        Args:
            flag_id: Flag ID
            user_id: User ID who made the change
            action: Action type (created, updated, deleted, enabled, disabled)
            changes: Changes made
            reason: Reason for change
        """
        audit = FeatureFlagAudit(
            id=uuid.uuid4(),
            flag_id=flag_id,
            user_id=uuid.UUID(user_id) if user_id else None,
            action=action,
            changes=changes,
            reason=reason,
        )

        self.db.add(audit)
        await self.db.commit()

    async def _track_evaluation(
        self,
        flag_id: uuid.UUID,
        user_id: str | None,
        user_role: str | None,
        enabled: bool,
        variant: str | None,
        context: dict[str, Any] | None
    ) -> None:
        """
        Track a feature flag evaluation.

        Args:
            flag_id: Flag ID
            user_id: User ID
            user_role: User role
            enabled: Whether flag was enabled
            variant: Variant assigned (if any)
            context: Evaluation context
        """
        evaluation = FeatureFlagEvaluation(
            id=uuid.uuid4(),
            flag_id=flag_id,
            user_id=uuid.UUID(user_id) if user_id else None,
            user_role=user_role,
            enabled=enabled,
            variant=variant,
            environment=self.environment,
            context=context,
        )

        self.db.add(evaluation)
        await self.db.commit()
