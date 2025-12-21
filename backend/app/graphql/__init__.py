"""GraphQL API layer for Residency Scheduler.

This package provides a GraphQL API alongside the existing REST API,
offering:
- Flexible querying with field selection
- Real-time subscriptions for schedule updates
- Type-safe API with automatic schema generation
- Pagination support for large datasets
- Authentication integration with JWT

Usage:
    The GraphQL endpoint is available at /graphql
    GraphQL Playground (dev only) at /graphql (interactive)

Subscriptions:
    Real-time subscriptions are available via WebSocket using GraphQL subscriptions protocol.
    Supported subscriptions:
    - schedule_updates: Schedule changes
    - assignment_updates: Assignment changes
    - swap_requests: Swap request notifications
    - swap_approvals: Swap approval notifications
    - conflict_alerts: Conflict detection alerts
    - resilience_alerts: Resilience system alerts
    - user_presence: User online/offline status
    - heartbeat: Connection keep-alive
"""

from app.graphql.schema import get_context, graphql_router, schema
from app.graphql.subscriptions import (
    Subscription,
    broadcast_assignment_update,
    broadcast_conflict_alert,
    broadcast_resilience_alert,
    broadcast_schedule_update,
    broadcast_swap_approval,
    broadcast_swap_request,
    get_subscription_manager,
)

__all__ = [
    "schema",
    "get_context",
    "graphql_router",
    "Subscription",
    "get_subscription_manager",
    "broadcast_schedule_update",
    "broadcast_assignment_update",
    "broadcast_swap_request",
    "broadcast_swap_approval",
    "broadcast_conflict_alert",
    "broadcast_resilience_alert",
]
