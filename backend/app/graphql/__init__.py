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
"""

from app.graphql.schema import get_context, graphql_router, schema

__all__ = ["schema", "get_context", "graphql_router"]
