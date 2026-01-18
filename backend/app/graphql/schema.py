"""Main GraphQL schema definition."""

from typing import Any

import strawberry
from fastapi import Depends, HTTPException, Request, status
from sqlalchemy.orm import Session
from strawberry.fastapi import GraphQLRouter

from app.core.security import verify_token
from app.db.session import get_db
from app.graphql.resolvers import Mutation, Query
from app.graphql.subscriptions import Subscription
from app.models.user import User

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

    SECURITY: All GraphQL requests require authentication. Anonymous access
    is not permitted.

    The context is available in all resolvers via info.context.

    Args:
        request: FastAPI request object
        db: Database session from dependency injection

    Returns:
        Context dictionary with db session and user info

    Raises:
        HTTPException: If authentication fails
    """
    context = {
        "db": db,
        "request": request,
        "user": None,
        "user_role": None,
    }

    # Extract JWT token from Authorization header or query params
    auth_header = request.headers.get("Authorization")
    token = None

    if auth_header and auth_header.startswith("Bearer "):
        token = auth_header.replace("Bearer ", "")
    else:
        # Try to get from query params (for subscriptions)
        token = request.query_params.get("token")

    # SECURITY: Require authentication for all GraphQL requests
    if not token:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authentication required for GraphQL API",
            headers={"WWW-Authenticate": "Bearer"},
        )

    # Verify token and extract user
    token_data = verify_token(token, db)
    if not token_data:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired token",
            headers={"WWW-Authenticate": "Bearer"},
        )

    # Verify user is active
    user = db.query(User).filter(User.id == token_data.user_id).first()
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User not found",
            headers={"WWW-Authenticate": "Bearer"},
        )

    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User account is deactivated",
            headers={"WWW-Authenticate": "Bearer"},
        )

    context["user"] = {
        "user_id": token_data.user_id,
        "username": token_data.username,
    }
    context["user_role"] = user.role

    return context


# Create GraphQL router for FastAPI integration
graphql_router = GraphQLRouter(
    schema,
    context_getter=get_context,
    graphiql=True,  # Enable GraphQL Playground in development
)


__all__ = ["schema", "get_context", "graphql_router"]
