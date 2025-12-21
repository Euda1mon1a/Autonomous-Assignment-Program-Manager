"""Feature flags package for gradual rollouts and A/B testing.

This package provides a complete feature flag system with:
- Boolean and percentage rollouts
- User and role targeting
- Environment-based flags
- A/B testing support
- Flag dependencies
- Audit logging
- Multiple storage backends (Database, Redis, In-Memory)

Example usage:

    # Create a feature flag
    from app.features import FeatureFlagService
    from app.db.session import get_db

    async def create_flag():
        db = await get_db()
        service = FeatureFlagService(db)

        flag = await service.create_flag(
            key="new_dashboard",
            name="New Dashboard Design",
            description="Redesigned dashboard with improved UX",
            enabled=True,
            rollout_percentage=0.1,  # 10% rollout
            created_by=current_user.id
        )

    # Evaluate a flag
    async def check_flag():
        db = await get_db()
        service = FeatureFlagService(db)

        enabled, variant, reason = await service.evaluate_flag(
            key="new_dashboard",
            user_id=current_user.id,
            user_role=current_user.role
        )

        if enabled:
            # Show new dashboard
            pass

    # Use decorators
    from app.features import require_feature_flag

    @router.get("/beta-feature")
    @require_feature_flag("beta_feature")
    async def beta_endpoint(
        current_user: User = Depends(get_current_active_user),
        db = Depends(get_db)
    ):
        return {"message": "Beta feature!"}
"""

from app.features.decorators import (
    FeatureFlagContext,
    ab_test_variant,
    feature_enabled,
    feature_flag_gate,
    require_feature_flag,
)
from app.features.evaluator import FeatureFlagEvaluator
from app.features.flags import FeatureFlagService
from app.features.storage import (
    CachedDatabaseStorageBackend,
    DatabaseStorageBackend,
    FeatureFlagStorageBackend,
    InMemoryStorageBackend,
    RedisStorageBackend,
)

__all__ = [
    # Service
    "FeatureFlagService",
    # Evaluator
    "FeatureFlagEvaluator",
    # Storage backends
    "FeatureFlagStorageBackend",
    "DatabaseStorageBackend",
    "RedisStorageBackend",
    "InMemoryStorageBackend",
    "CachedDatabaseStorageBackend",
    # Decorators
    "require_feature_flag",
    "feature_flag_gate",
    "ab_test_variant",
    "FeatureFlagContext",
    "feature_enabled",
]
