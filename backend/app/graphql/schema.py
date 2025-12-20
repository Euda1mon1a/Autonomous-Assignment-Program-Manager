"""Main GraphQL schema definition."""
from typing import Any, AsyncGenerator, Optional

import strawberry
from fastapi import Depends, Request
from sqlalchemy.orm import Session
from strawberry.fastapi import GraphQLRouter
from strawberry.types import Info

from app.core.security import oauth2_scheme, verify_token
from app.db.session import get_db
from app.graphql.resolvers import Mutation, Query
from app.graphql.subscriptions import Subscription


# Build the schema
schema = strawberry.Schema(
    query=Query,
    mutation=Mutation,
    subscription=Subscription,
)


async def get_context(
    request: Request,
    db: Session = Depends(get_db),
) -> dict[str, Any]:
    """
    Build GraphQL context with database session and authenticated user.

    The context is available in all resolvers via info.context.

    Args:
        request: FastAPI request object
        db: Database session from dependency injection

    Returns:
        Context dictionary with db session and user info
    """
    context = {
        "db": db,
        "request": request,
        "user": None,
    }

    # Extract and verify JWT token if present
    # Check Authorization header
    auth_header = request.headers.get("Authorization")
    token = None

    if auth_header and auth_header.startswith("Bearer "):
        token = auth_header.replace("Bearer ", "")
    else:
        # Try to get from query params (for subscriptions)
        token = request.query_params.get("token")

    # Verify token and add user to context
    if token:
        token_data = verify_token(token, db)
        if token_data:
            context["user"] = {
                "user_id": token_data.user_id,
                "username": token_data.username,
            }

    return context


# Create GraphQL router for FastAPI integration
graphql_router = GraphQLRouter(
    schema,
    context_getter=get_context,
    graphiql=True,  # Enable GraphQL Playground in development
)


__all__ = ["schema", "get_context", "graphql_router"]
