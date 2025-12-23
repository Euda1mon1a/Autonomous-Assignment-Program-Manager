"""
Blue-Green Deployment and Canary Release Support.

This module provides utilities for zero-downtime deployments of the
Residency Scheduler backend using blue-green deployment patterns and
canary releases.

Key features:
- Blue-green deployment slot management
- Canary releases with progressive rollouts
- Traffic switching utilities
- Health verification before switch
- Rollback triggers
- Database migration coordination
- Session draining support
- Deployment state tracking
- Deployment notifications

Usage - Blue-Green:
    from app.deployment import BlueGreenDeploymentManager, DeploymentSlot

    manager = BlueGreenDeploymentManager()

    # Prepare new deployment
    await manager.prepare_deployment(DeploymentSlot.GREEN)

    # Verify health
    health = await manager.verify_slot_health(DeploymentSlot.GREEN)

    # Switch traffic
    if health.is_healthy:
        await manager.switch_traffic(DeploymentSlot.GREEN)

Usage - Canary:
    from app.deployment import CanaryReleaseManager

    manager = CanaryReleaseManager()
    release = await manager.create_release(version="v1.2.3")
    await manager.start_ramp(release.id)
"""

from app.deployment.blue_green import (
    BlueGreenDeploymentManager,
    DeploymentConfig,
    DeploymentSlot,
    DeploymentState,
    DeploymentStatus,
    HealthCheck,
    HealthCheckResult,
    SessionDrainStatus,
    TrafficSplitStrategy,
)
from app.deployment.blue_green import (
    RollbackReason as BlueGreenRollbackReason,
)
from app.deployment.canary import (
    CanaryConfig,
    CanaryMetrics,
    CanaryOutcome,
    CanaryRelease,
    CanaryReleaseManager,
    CanaryState,
    MetricComparison,
    RollbackReason,
    TrafficSplit,
    UserSegment,
)

__all__ = [
    # Blue-Green Deployment
    "BlueGreenDeploymentManager",
    "DeploymentConfig",
    "DeploymentSlot",
    "DeploymentState",
    "DeploymentStatus",
    "HealthCheck",
    "HealthCheckResult",
    "BlueGreenRollbackReason",
    "SessionDrainStatus",
    "TrafficSplitStrategy",
    # Canary Release
    "CanaryConfig",
    "CanaryMetrics",
    "CanaryRelease",
    "CanaryReleaseManager",
    "CanaryState",
    "CanaryOutcome",
    "MetricComparison",
    "RollbackReason",
    "UserSegment",
    "TrafficSplit",
]
