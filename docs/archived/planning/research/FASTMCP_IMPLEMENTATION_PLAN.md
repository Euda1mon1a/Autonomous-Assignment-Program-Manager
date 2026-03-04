# FastMCP 2.0 Implementation Plan for Residency Scheduler

> **Date:** 2025-12-19
> **Purpose:** Research and implementation plan for exposing the Residency Scheduler through Model Context Protocol (MCP) using FastMCP 2.0
> **Status:** Research Complete - Ready for Implementation Planning

---

## Table of Contents

1. [FastMCP Overview](#1-fastmcp-overview)
2. [Authentication Integration](#2-authentication-integration)
3. [FastAPI Integration](#3-fastapi-integration)
4. [Resource & Tool Patterns](#4-resource--tool-patterns)
5. [Implementation Architecture](#5-implementation-architecture)
6. [Testing Strategy](#6-testing-strategy)
7. [Implementation Roadmap](#7-implementation-roadmap)
8. [References](#8-references)

---

## 1. FastMCP Overview

### What is FastMCP 2.0?

**FastMCP 2.0** is an open-source Python framework that simplifies building Model Context Protocol (MCP) servers and clients. It's often described as **"the USB-C port for AI"** - providing a uniform, standardized way to connect Large Language Models (LLMs) to external data sources and functionality.

**Key Characteristics:**
- **Successor to FastMCP 1.0**: The original FastMCP 1.0 pioneered Python MCP development and was incorporated into the official MCP SDK in 2024
- **Production-Ready**: Designed for enterprise use with authentication, deployment tools, and testing utilities
- **Async-First**: Built on modern Python async patterns for high performance
- **Developer-Friendly**: Decorator-based API similar to FastAPI

### Key Features and Capabilities

#### Core MCP Primitives

FastMCP exposes three fundamental building blocks:

1. **Resources** - Read-only data sources (like GET endpoints)
   - Expose documents, database records, configuration
   - URI-addressable with templating support
   - Ideal for providing context to LLMs

2. **Tools** - Executable functions (like POST/PUT endpoints)
   - Perform actions, computations, or side effects
   - Can be synchronous or asynchronous
   - Support complex parameter schemas via Pydantic

3. **Prompts** - Reusable templates for LLM interactions
   - Standardized interaction patterns
   - Parameterized prompt templates
   - Guide LLM behavior and workflows

#### Advanced Features (FastMCP 2.0 Exclusive)

- **Enterprise Authentication**: Full OIDC support with providers for Google, GitHub, WorkOS, Azure, Auth0
- **OAuth Proxy Pattern**: Unique architecture for secure token management
- **Server Composition**: Combine multiple MCP servers
- **OpenAPI/FastAPI Generation**: Auto-generate MCP servers from existing APIs
- **Background Tasks**: Protocol-native long-running operations with progress reporting (MCP 2025-11-25 spec)
- **Tool Transformation**: Modify and enhance tools dynamically
- **Deployment Tools**: Production-ready server management

#### Latest Features (v2.14+)

**Background Tasks (SEP-1686):**
```python
@mcp.tool(task=True)  # Enable background task support
async def long_running_operation(ctx: Context, data: str) -> str:
    """Long operation that reports progress."""
    await ctx.report_progress(progress=0.0, total=100.0)
    # ... do work ...
    await ctx.report_progress(progress=50.0, total=100.0)
    # ... finish work ...
    return "Complete"
```

### Comparison with Raw MCP Protocol

| Feature | Raw MCP SDK | FastMCP 2.0 |
|---------|-------------|-------------|
| **Setup Complexity** | Manual protocol implementation | Decorator-based, minimal boilerplate |
| **Type Safety** | Manual schema definition | Automatic from Python type hints + Pydantic |
| **Authentication** | Implement yourself | Built-in OIDC, OAuth, JWT |
| **Testing** | Manual transport setup | In-memory client for unit tests |
| **Async Support** | Manual async handling | Native async-first, supports both sync/async |
| **FastAPI Integration** | Not available | Automatic conversion via `from_fastapi()` |
| **Middleware** | Custom implementation | Standard ASGI middleware support |
| **Deployment** | DIY | Built-in SSE, HTTP transports |
| **Background Tasks** | Manual implementation | Protocol-native with `task=True` |

**Verdict:** FastMCP 2.0 provides a significantly better developer experience with production-grade features out of the box.

---

## 2. Authentication Integration

### How FastMCP Handles Auth

FastMCP 2.0 implements a **modular authentication system** built around the `AuthProvider` hierarchy. The architecture supports multiple patterns:

1. **Token Verification** - Validate JWT or API keys
2. **OAuth Flows** - Full OAuth 2.0/OIDC support
3. **Custom Validators** - Implement any auth scheme

### Authentication Architecture

```python
from fastmcp.auth import AuthProvider, AuthConfig
from fastmcp.auth.oauth import OAuthProvider

# Built-in providers
providers = {
    "google": GoogleOAuthProvider,
    "github": GitHubOAuthProvider,
    "auth0": Auth0OAuthProvider,
    "azure": AzureADOAuthProvider,
    "workos": WorkOSOAuthProvider,
}
```

### Integration with Existing JWT Tokens

FastMCP can validate JWT tokens issued by external systems (like our existing FastAPI auth):

#### Option 1: Custom JWT Validator (Recommended)

```python
from fastmcp.auth import AuthProvider, AuthResult
from jose import jwt, JWTError
from datetime import datetime
import os

class ResidencySchedulerJWTAuth(AuthProvider):
    """Validates JWTs issued by the Residency Scheduler FastAPI backend."""

    def __init__(self):
        self.secret_key = os.getenv("SECRET_KEY")
        self.algorithm = "HS256"

    async def validate(self, credentials: str) -> AuthResult:
        """
        Validate JWT token from Authorization header.

        Args:
            credentials: Bearer token from Authorization header

        Returns:
            AuthResult with user claims if valid
        """
        if not credentials.startswith("Bearer "):
            return AuthResult(
                success=False,
                error="Invalid authorization header format"
            )

        token = credentials.removeprefix("Bearer ")

        try:
            # Decode and verify JWT (same logic as FastAPI)
            payload = jwt.decode(
                token,
                self.secret_key,
                algorithms=[self.algorithm]
            )

            # Extract user info
            user_id = payload.get("sub")
            email = payload.get("email")
            role = payload.get("role")

            if not user_id:
                return AuthResult(success=False, error="Missing user ID")

            # Return successful auth with user context
            return AuthResult(
                success=True,
                user_id=user_id,
                metadata={
                    "email": email,
                    "role": role,
                    "scopes": payload.get("scopes", [])
                }
            )

        except JWTError as e:
            return AuthResult(success=False, error=f"Invalid token: {str(e)}")
```

#### Option 2: OAuth Proxy Pattern

FastMCP's **OAuth Proxy** implements a token factory pattern where it issues its own JWT tokens instead of forwarding upstream provider tokens. This is useful for maintaining OAuth 2.0 token audience boundaries.

```python
from fastmcp import FastMCP
from fastmcp.auth.oauth import Auth0OAuthProvider

# Create FastMCP server with OAuth
mcp = FastMCP(
    "Residency Scheduler MCP",
    auth=Auth0OAuthProvider(
        domain=os.getenv("AUTH0_DOMAIN"),
        client_id=os.getenv("AUTH0_CLIENT_ID"),
        client_secret=os.getenv("AUTH0_CLIENT_SECRET"),
        scopes=["openid", "profile", "email"]
    )
)
```

**Benefits:**
- Proper token audience boundaries
- Tokens are specific to MCP server
- Can add MCP-specific claims
- Maintains OAuth compliance

### Role-Based Access Patterns

#### Accessing User Context in Tools

```python
from fastmcp import FastMCP, Context
from fastapi import HTTPException

mcp = FastMCP("Scheduler MCP", auth=ResidencySchedulerJWTAuth())

@mcp.tool()
async def create_swap_request(
    ctx: Context,
    from_block_id: str,
    to_block_id: str,
    reason: str
) -> dict:
    """
    Create a schedule swap request (requires FACULTY role).

    Args:
        ctx: FastMCP context with user info
        from_block_id: Block to swap from
        to_block_id: Block to swap to
        reason: Justification for swap
    """
    # Extract user from authenticated context
    user_id = ctx.request_context.auth_result.user_id
    user_role = ctx.request_context.auth_result.metadata.get("role")

    # Enforce role-based access
    if user_role not in ["FACULTY", "ADMIN"]:
        raise HTTPException(
            status_code=403,
            detail="Only faculty and admins can create swap requests"
        )

    # Call existing service layer (reuse business logic)
    from app.services.swap_service import SwapService

    service = SwapService()
    result = await service.create_swap_request(
        user_id=user_id,
        from_block_id=from_block_id,
        to_block_id=to_block_id,
        reason=reason
    )

    return {
        "swap_id": result.id,
        "status": result.status,
        "created_at": result.created_at.isoformat()
    }
```

#### Granular Permission Checks

```python
from enum import Enum

class Permission(str, Enum):
    """Permissions for MCP operations."""
    READ_SCHEDULES = "schedules:read"
    WRITE_SCHEDULES = "schedules:write"
    MANAGE_SWAPS = "swaps:manage"
    ACGME_OVERRIDE = "acgme:override"
    ADMIN = "admin:*"

# Role -> Permission mapping
ROLE_PERMISSIONS = {
    "ADMIN": [Permission.ADMIN],
    "COORDINATOR": [
        Permission.READ_SCHEDULES,
        Permission.WRITE_SCHEDULES,
        Permission.MANAGE_SWAPS
    ],
    "FACULTY": [
        Permission.READ_SCHEDULES,
        Permission.MANAGE_SWAPS
    ],
    "RESIDENT": [
        Permission.READ_SCHEDULES
    ]
}

def require_permission(permission: Permission):
    """Decorator to enforce permissions on MCP tools."""
    def decorator(func):
        async def wrapper(ctx: Context, *args, **kwargs):
            user_role = ctx.request_context.auth_result.metadata.get("role")
            user_permissions = ROLE_PERMISSIONS.get(user_role, [])

            if Permission.ADMIN in user_permissions:
                # Admins have all permissions
                return await func(ctx, *args, **kwargs)

            if permission not in user_permissions:
                raise PermissionError(
                    f"User lacks required permission: {permission}"
                )

            return await func(ctx, *args, **kwargs)
        return wrapper
    return decorator

# Usage
@mcp.tool()
@require_permission(Permission.ACGME_OVERRIDE)
async def override_acgme_violation(
    ctx: Context,
    assignment_id: str,
    justification: str
) -> dict:
    """Override ACGME compliance violation (ADMIN only)."""
    # Implementation
    pass
```

---

## 3. FastAPI Integration

### Can FastMCP Integrate with Existing FastAPI Routes?

**Yes!** FastMCP provides multiple integration patterns:

1. **Auto-conversion**: `FastMCP.from_fastapi(app)` - Automatically convert FastAPI endpoints to MCP tools
2. **Manual mounting**: Mount MCP server as ASGI app alongside FastAPI
3. **Shared lifespan**: Coordinate database connections and startup tasks
4. **Middleware sharing**: Reuse FastAPI middleware in MCP server

### Integration Pattern 1: Auto-Conversion (Fastest)

```python
from fastapi import FastAPI
from fastmcp import FastMCP

# Existing FastAPI app
app = FastAPI(title="Residency Scheduler API")

# ... existing routes ...

# Auto-generate MCP server from FastAPI app
mcp = FastMCP.from_fastapi(
    app,
    name="Residency Scheduler MCP",
    # Only expose specific routes (optional)
    include_routes=[
        "/api/v1/schedule/*",
        "/api/v1/swaps/*",
        "/api/v1/acgme/*"
    ],
    # Exclude sensitive routes
    exclude_routes=[
        "/api/v1/auth/*",
        "/api/v1/admin/secrets/*"
    ]
)
```

**Benefits:**
- Zero code duplication
- Existing Pydantic schemas reused
- Dependencies and middleware preserved
- Authentication carries over

**Limitations:**
- Less control over MCP-specific behavior
- May expose REST semantics that don't fit MCP well

### Integration Pattern 2: Shared Database Sessions

```python
from contextlib import asynccontextmanager
from fastapi import FastAPI, Depends
from fastmcp import FastMCP, Context
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.session import get_db, async_session_maker

# Shared lifespan for both FastAPI and FastMCP
@asynccontextmanager
async def app_lifespan(app):
    """Manage database connections and startup tasks."""
    # Startup
    logger.info("Starting Residency Scheduler (FastAPI + MCP)")

    # Initialize database pool (shared by both)
    # Already done in app.db.session

    yield

    # Shutdown
    logger.info("Shutting down Residency Scheduler")
    await async_session_maker.close_all()

# FastAPI app with shared lifespan
app = FastAPI(lifespan=app_lifespan)

# FastMCP server
mcp = FastMCP("Residency Scheduler MCP")

# Use the SAME database session factory in MCP tools
@mcp.tool()
async def get_schedule(person_id: str, start_date: str, end_date: str) -> dict:
    """Fetch schedule for a person within a date range."""
    from datetime import date
    from app.services.schedule_service import ScheduleService

    # Get database session from existing session factory
    async with async_session_maker() as db:
        service = ScheduleService()
        assignments = await service.get_assignments(
            db=db,
            person_id=person_id,
            start_date=date.fromisoformat(start_date),
            end_date=date.fromisoformat(end_date)
        )

        return {
            "person_id": person_id,
            "assignments": [
                {
                    "block_id": a.block_id,
                    "rotation": a.rotation.name,
                    "date": a.block.date.isoformat(),
                    "session": a.block.session
                }
                for a in assignments
            ]
        }
```

### Integration Pattern 3: Middleware Compatibility

```python
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from starlette.middleware.base import BaseHTTPMiddleware

# Custom middleware (existing)
class LoggingMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request, call_next):
        logger.info(f"Request: {request.method} {request.url}")
        response = await call_next(request)
        return response

# FastAPI app
app = FastAPI()

# Add middleware
app.add_middleware(LoggingMiddleware)

# FastMCP server
mcp = FastMCP("Scheduler MCP")

# IMPORTANT: Avoid CORS conflicts
# FastMCP handles CORS for OAuth routes automatically
# Only add CORS to FastAPI sub-app if needed:

from fastapi import APIRouter

api_router = APIRouter()
# ... add routes to api_router ...

# Mount as sub-app with its own CORS
api_app = FastAPI()
api_app.include_router(api_router)
api_app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"]
)

# Mount both
app.mount("/api", api_app)
app.mount("/mcp", mcp.get_asgi_app())
```

### Integration Pattern 4: Combined App with Routing

```python
from fastapi import FastAPI
from fastmcp import FastMCP

# Main application
app = FastAPI(title="Residency Scheduler")

# Existing REST API routes
from app.api.routes import auth, schedule, swaps, acgme
app.include_router(auth.router, prefix="/api/v1/auth", tags=["auth"])
app.include_router(schedule.router, prefix="/api/v1/schedule", tags=["schedule"])
app.include_router(swaps.router, prefix="/api/v1/swaps", tags=["swaps"])
app.include_router(acgme.router, prefix="/api/v1/acgme", tags=["acgme"])

# MCP server
mcp = FastMCP(
    "Residency Scheduler MCP",
    auth=ResidencySchedulerJWTAuth()
)

# Add MCP tools (defined separately)
from app.mcp.tools import register_tools
register_tools(mcp)

# Mount MCP server at /mcp endpoint
# Supports both SSE and WebSocket transports
app.mount("/mcp", mcp.get_asgi_app())

# Now clients can:
# - Use REST API: http://localhost:8000/api/v1/schedule
# - Use MCP: http://localhost:8000/mcp (SSE transport)
```

**Routing:**
- REST API: `/api/v1/*` - Traditional HTTP endpoints
- MCP Server: `/mcp` - Model Context Protocol (SSE/WebSocket)
- Swagger Docs: `/docs` - FastAPI auto-generated docs

---

## 4. Resource & Tool Patterns

### Best Practices for Read-Only Resources

Resources expose read-only data to LLMs. They're URI-addressable and support templating.

#### Static Resources

```python
from fastmcp import FastMCP

mcp = FastMCP("Scheduler MCP")

@mcp.resource("acgme://regulations/80-hour-rule")
async def acgme_80_hour_rule() -> str:
    """
    ACGME 80-Hour Work Week Rule Documentation.

    Provides comprehensive details on the 80-hour work week requirement
    for medical residents.
    """
    return """
# ACGME 80-Hour Work Week Rule

## Summary
Residents must not exceed 80 hours of work per week, averaged over a 4-week period.

## Key Requirements
- Maximum 80 hours/week (rolling 4-week average)
- Includes all clinical and academic activities
- Does not include reading and preparation time outside scheduled work
- Strategic napping does not count toward the 80-hour limit

## Monitoring
Work hours are logged and monitored continuously. Violations trigger alerts
to program coordinators and must be addressed within 24 hours.

## Exceptions
No exceptions permitted under standard circumstances. Special circumstances
require ACGME notification and approval.
"""

@mcp.resource("acgme://regulations/list")
async def acgme_regulation_list() -> str:
    """List all ACGME regulations."""
    return """
Available ACGME regulations:
- acgme://regulations/80-hour-rule
- acgme://regulations/1-in-7-rule
- acgme://regulations/supervision-ratios
- acgme://regulations/duty-hour-exceptions
"""
```

#### Dynamic Resources with Templates

```python
@mcp.resource("schedule://person/{person_id}/current-week")
async def person_current_week_schedule(person_id: str) -> str:
    """
    Current week's schedule for a specific person.

    Args:
        person_id: Person's unique identifier
    """
    from datetime import date, timedelta
    from app.services.schedule_service import ScheduleService
    from app.db.session import async_session_maker

    # Calculate current week bounds
    today = date.today()
    week_start = today - timedelta(days=today.weekday())
    week_end = week_start + timedelta(days=6)

    async with async_session_maker() as db:
        service = ScheduleService()
        assignments = await service.get_assignments(
            db=db,
            person_id=person_id,
            start_date=week_start,
            end_date=week_end
        )

    # Format as readable text for LLM
    lines = [
        f"Schedule for {person_id}",
        f"Week of {week_start.isoformat()}",
        "",
        "Day | Session | Rotation | Location",
        "----|---------|----------|----------"
    ]

    for assignment in assignments:
        block = assignment.block
        rotation = assignment.rotation
        lines.append(
            f"{block.date.strftime('%a %m/%d')} | "
            f"{block.session} | "
            f"{rotation.name} | "
            f"{rotation.location or 'N/A'}"
        )

    return "\n".join(lines)

@mcp.resource("schedule://person/{person_id}/month/{year}/{month}")
async def person_month_schedule(person_id: str, year: int, month: int) -> str:
    """
    Full month schedule for a person.

    Args:
        person_id: Person's unique identifier
        year: Year (e.g., 2025)
        month: Month (1-12)
    """
    # Implementation similar to above
    pass
```

#### Database-Backed Resources

```python
@mcp.resource("faculty://available-for-swap")
async def available_faculty_for_swap() -> str:
    """
    List of faculty members currently available for schedule swaps.

    Returns faculty who:
    - Are not on leave
    - Have < 80% utilization
    - Are qualified for common rotations
    """
    from app.services.swap_service import SwapService
    from app.db.session import async_session_maker

    async with async_session_maker() as db:
        service = SwapService()
        available = await service.get_available_swap_candidates(db)

    lines = ["Available Faculty for Swaps", ""]

    for person in available:
        lines.append(
            f"- {person.name} ({person.email})"
            f"  - Qualifications: {', '.join(person.qualifications)}"
            f"  - Utilization: {person.utilization_percent}%"
        )

    return "\n".join(lines)
```

**Best Practices:**
- Keep resources **stateless** - always fetch from DB/files
- Use **descriptive URIs** - `schedule://person/{id}` not `res://123`
- **Cache when appropriate** - but invalidate on updates
- Return **LLM-friendly formats** - Markdown, structured text
- Include **metadata** - dates, context, relationships

### Write/Action Tool Patterns

Tools perform actions and can modify state. They should:
- Validate inputs thoroughly
- Use transactions
- Handle errors gracefully
- Return actionable results

#### Simple Tool Pattern

```python
@mcp.tool()
async def calculate_acgme_hours(
    person_id: str,
    start_date: str,
    end_date: str
) -> dict:
    """
    Calculate ACGME work hours for a person over a date range.

    Args:
        person_id: Person's unique identifier
        start_date: ISO format date (YYYY-MM-DD)
        end_date: ISO format date (YYYY-MM-DD)

    Returns:
        Dictionary with:
        - total_hours: Total hours worked
        - weekly_average: Average hours per week
        - violations: List of any violations
        - compliant: Boolean compliance status
    """
    from datetime import date
    from app.services.acgme_service import ACGMEService
    from app.db.session import async_session_maker

    # Parse dates
    start = date.fromisoformat(start_date)
    end = date.fromisoformat(end_date)

    async with async_session_maker() as db:
        service = ACGMEService()
        result = await service.calculate_hours(
            db=db,
            person_id=person_id,
            start_date=start,
            end_date=end
        )

    return {
        "person_id": person_id,
        "period": f"{start_date} to {end_date}",
        "total_hours": result.total_hours,
        "weekly_average": result.weekly_average,
        "violations": [
            {
                "week": v.week,
                "hours": v.hours,
                "threshold": v.threshold
            }
            for v in result.violations
        ],
        "compliant": len(result.violations) == 0
    }
```

#### Complex Tool with Transaction

```python
from pydantic import BaseModel, Field

class SwapRequestParams(BaseModel):
    """Parameters for creating a swap request."""
    from_block_id: str = Field(..., description="Block to swap from")
    to_block_id: str = Field(..., description="Block to swap to")
    reason: str = Field(..., min_length=10, description="Justification")
    swap_type: str = Field("ONE_TO_ONE", description="Type of swap")

@mcp.tool()
async def create_swap_request(
    ctx: Context,
    params: SwapRequestParams
) -> dict:
    """
    Create a schedule swap request.

    This tool:
    1. Validates the swap is possible
    2. Checks ACGME compliance
    3. Creates the swap request
    4. Notifies relevant parties

    Requires FACULTY or ADMIN role.
    """
    from app.services.swap_service import SwapService
    from app.db.session import async_session_maker
    from sqlalchemy.exc import IntegrityError

    # Get authenticated user
    user_id = ctx.request_context.auth_result.user_id
    user_role = ctx.request_context.auth_result.metadata.get("role")

    # Check permissions
    if user_role not in ["FACULTY", "ADMIN"]:
        return {
            "success": False,
            "error": "Insufficient permissions",
            "required_role": "FACULTY or ADMIN"
        }

    async with async_session_maker() as db:
        try:
            # Use existing service layer (reuse business logic!)
            service = SwapService()

            # Validate swap is possible
            validation = await service.validate_swap(
                db=db,
                from_block_id=params.from_block_id,
                to_block_id=params.to_block_id,
                user_id=user_id
            )

            if not validation.is_valid:
                return {
                    "success": False,
                    "error": "Swap validation failed",
                    "details": validation.errors
                }

            # Create swap request (transactional)
            swap = await service.create_swap_request(
                db=db,
                from_block_id=params.from_block_id,
                to_block_id=params.to_block_id,
                requester_id=user_id,
                reason=params.reason,
                swap_type=params.swap_type
            )

            await db.commit()

            return {
                "success": True,
                "swap_id": swap.id,
                "status": swap.status,
                "created_at": swap.created_at.isoformat(),
                "auto_match_available": validation.auto_match_candidates > 0
            }

        except IntegrityError as e:
            await db.rollback()
            return {
                "success": False,
                "error": "Database integrity error",
                "message": "Swap may already exist or blocks are invalid"
            }
        except Exception as e:
            await db.rollback()
            logger.error(f"Swap creation failed: {e}", exc_info=True)
            return {
                "success": False,
                "error": "Internal error",
                "message": "An unexpected error occurred"
            }
```

#### Background Task Tool (Long-Running Operations)

```python
@mcp.tool(task=True)  # Enable background task support
async def generate_schedule(
    ctx: Context,
    academic_year: int,
    force_regenerate: bool = False
) -> dict:
    """
    Generate complete schedule for an academic year.

    This is a long-running operation that reports progress.

    Args:
        ctx: FastMCP context for progress reporting
        academic_year: Year to generate (e.g., 2026)
        force_regenerate: If True, regenerate even if exists

    Returns:
        Summary of generated schedule
    """
    from app.scheduling.engine import ScheduleEngine
    from app.db.session import async_session_maker

    async with async_session_maker() as db:
        engine = ScheduleEngine()

        # Report progress: Phase 1
        await ctx.report_progress(
            progress=0.0,
            total=100.0,
            message="Validating constraints and requirements"
        )

        # Validate
        validation = await engine.validate_requirements(db, academic_year)
        if not validation.is_valid:
            return {
                "success": False,
                "error": "Validation failed",
                "details": validation.errors
            }

        # Report progress: Phase 2
        await ctx.report_progress(
            progress=20.0,
            total=100.0,
            message="Generating block assignments"
        )

        # Generate assignments
        assignments = await engine.generate_assignments(
            db,
            academic_year,
            progress_callback=lambda p: ctx.report_progress(
                progress=20.0 + (p * 0.6),  # 20-80%
                total=100.0,
                message=f"Assigning blocks: {p:.1f}%"
            )
        )

        # Report progress: Phase 3
        await ctx.report_progress(
            progress=80.0,
            total=100.0,
            message="Validating ACGME compliance"
        )

        # Validate ACGME
        compliance = await engine.validate_acgme_compliance(db, assignments)

        # Report progress: Phase 4
        await ctx.report_progress(
            progress=90.0,
            total=100.0,
            message="Saving schedule to database"
        )

        # Save
        await engine.save_schedule(db, assignments)
        await db.commit()

        # Complete
        await ctx.report_progress(
            progress=100.0,
            total=100.0,
            message="Schedule generation complete"
        )

        return {
            "success": True,
            "academic_year": academic_year,
            "total_assignments": len(assignments),
            "acgme_compliant": compliance.is_compliant,
            "warnings": compliance.warnings
        }
```

### Async Database Operations

**Always use async operations** with FastMCP:

```python
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from app.models import Person, Assignment

@mcp.tool()
async def get_faculty_workload(faculty_id: str) -> dict:
    """Get current workload for a faculty member."""
    from app.db.session import async_session_maker

    async with async_session_maker() as db:
        # Async query with eager loading
        result = await db.execute(
            select(Person)
            .options(selectinload(Person.assignments))
            .where(Person.id == faculty_id)
        )
        person = result.scalar_one_or_none()

        if not person:
            raise ValueError(f"Faculty not found: {faculty_id}")

        # Calculate workload
        total_hours = sum(a.hours for a in person.assignments)

        return {
            "faculty_id": faculty_id,
            "name": person.name,
            "total_assignments": len(person.assignments),
            "total_hours": total_hours,
            "utilization_percent": (total_hours / 2080) * 100  # Annual hours
        }
```

**Best Practices:**
- Always use `async with async_session_maker() as db`
- Use `await db.execute()` for queries
- Use transactions: `await db.commit()` or `await db.rollback()`
- Eager load relationships with `selectinload()` to avoid N+1 queries
- Handle database errors gracefully

---

## 5. Implementation Architecture

### Recommended Project Structure

```
backend/app/
├── mcp/                          # NEW: MCP server implementation
│   ├── __init__.py
│   ├── server.py                 # Main MCP server setup
│   ├── auth.py                   # JWT validator for MCP
│   ├── tools/                    # MCP tools (write operations)
│   │   ├── __init__.py
│   │   ├── schedule_tools.py     # Schedule management tools
│   │   ├── swap_tools.py         # Swap request tools
│   │   ├── acgme_tools.py        # ACGME analysis tools
│   │   └── admin_tools.py        # Admin-only tools
│   ├── resources/                # MCP resources (read operations)
│   │   ├── __init__.py
│   │   ├── schedule_resources.py # Schedule data resources
│   │   ├── acgme_resources.py    # ACGME regulation resources
<<<<<<< HEAD
│   │   └── faculty_resources.py  # Faculty/staff resources
=======
│   │   └── faculty_resources.py  ***REMOVED***/staff resources
>>>>>>> origin/docs/session-14-summary
│   └── testing/                  # MCP-specific tests
│       ├── __init__.py
│       ├── test_tools.py
│       └── test_resources.py
│
├── api/                          # Existing FastAPI routes
├── services/                     # Existing business logic (REUSE!)
├── models/                       # Existing SQLAlchemy models
├── schemas/                      # Existing Pydantic schemas
└── main.py                       # Updated to mount MCP server
```

### Code Scaffolding Plan

#### Step 1: Create MCP Server Foundation

**File: `backend/app/mcp/server.py`**

```python
"""
FastMCP server for Residency Scheduler.

Exposes scheduling domain through Model Context Protocol.
"""
from fastmcp import FastMCP
from app.mcp.auth import ResidencySchedulerJWTAuth
import logging

logger = logging.getLogger(__name__)

# Create MCP server
mcp = FastMCP(
    name="Residency Scheduler MCP",
    version="1.0.0",
    auth=ResidencySchedulerJWTAuth(),
    dependencies={
        "sqlalchemy": "^2.0.0",
        "pydantic": "^2.5.0"
    }
)

# Import and register all tools and resources
from app.mcp.tools import register_tools
from app.mcp.resources import register_resources

register_tools(mcp)
register_resources(mcp)

logger.info("MCP server initialized")
```

#### Step 2: Create Authentication Provider

**File: `backend/app/mcp/auth.py`**

```python
"""Authentication provider for MCP server."""
from fastmcp.auth import AuthProvider, AuthResult
from jose import jwt, JWTError
from app.core.config import settings
import logging

logger = logging.getLogger(__name__)

class ResidencySchedulerJWTAuth(AuthProvider):
    """
    JWT authentication provider for MCP server.

    Validates JWT tokens issued by the FastAPI backend's auth system.
    """

    def __init__(self):
        self.secret_key = settings.SECRET_KEY
        self.algorithm = "HS256"

    async def validate(self, credentials: str) -> AuthResult:
        """
        Validate JWT token from Authorization header.

        Args:
            credentials: Authorization header value (e.g., "Bearer <token>")

        Returns:
            AuthResult with user information if valid
        """
        # Check format
        if not credentials or not credentials.startswith("Bearer "):
            return AuthResult(
                success=False,
                error="Invalid authorization header format"
            )

        # Extract token
        token = credentials.removeprefix("Bearer ").strip()

        try:
            # Decode JWT (same as FastAPI auth)
            payload = jwt.decode(
                token,
                self.secret_key,
                algorithms=[self.algorithm]
            )

            # Extract claims
            user_id = payload.get("sub")
            email = payload.get("email")
            role = payload.get("role")
            scopes = payload.get("scopes", [])

            if not user_id:
                return AuthResult(
                    success=False,
                    error="Missing user ID in token"
                )

            logger.info(f"MCP auth successful: user={user_id}, role={role}")

            return AuthResult(
                success=True,
                user_id=user_id,
                metadata={
                    "email": email,
                    "role": role,
                    "scopes": scopes
                }
            )

        except JWTError as e:
            logger.warning(f"JWT validation failed: {e}")
            return AuthResult(
                success=False,
                error=f"Invalid token: {str(e)}"
            )
```

#### Step 3: Create Tool Registry

**File: `backend/app/mcp/tools/__init__.py`**

```python
"""MCP tools registry."""
from fastmcp import FastMCP

def register_tools(mcp: FastMCP):
    """Register all MCP tools."""
    from app.mcp.tools import (
        schedule_tools,
        swap_tools,
        acgme_tools,
        admin_tools
    )

    # Tools are registered via decorators in each module
    # Just importing them registers them with the server
    pass
```

**File: `backend/app/mcp/tools/schedule_tools.py`**

```python
"""Schedule management tools."""
from fastmcp import Context
from app.mcp.server import mcp
from app.db.session import async_session_maker
from app.services.schedule_service import ScheduleService
from datetime import date
import logging

logger = logging.getLogger(__name__)

@mcp.tool()
async def get_person_schedule(
    person_id: str,
    start_date: str,
    end_date: str
) -> dict:
    """
    Retrieve schedule assignments for a person.

    Args:
        person_id: Person's unique identifier
        start_date: Start date (ISO format: YYYY-MM-DD)
        end_date: End date (ISO format: YYYY-MM-DD)

    Returns:
        Dictionary containing:
        - person_id: Person identifier
        - assignments: List of schedule assignments
        - total_hours: Total hours scheduled
    """
    async with async_session_maker() as db:
        service = ScheduleService()

        assignments = await service.get_assignments(
            db=db,
            person_id=person_id,
            start_date=date.fromisoformat(start_date),
            end_date=date.fromisoformat(end_date)
        )

        return {
            "person_id": person_id,
            "period": {"start": start_date, "end": end_date},
            "assignments": [
                {
                    "assignment_id": a.id,
                    "block_date": a.block.date.isoformat(),
                    "session": a.block.session,
                    "rotation": a.rotation.name,
                    "hours": a.hours
                }
                for a in assignments
            ],
            "total_hours": sum(a.hours for a in assignments)
        }

# Additional tools...
```

#### Step 4: Create Resource Registry

**File: `backend/app/mcp/resources/__init__.py`**

```python
"""MCP resources registry."""
from fastmcp import FastMCP

def register_resources(mcp: FastMCP):
    """Register all MCP resources."""
    from app.mcp.resources import (
        schedule_resources,
        acgme_resources,
        faculty_resources
    )
    pass
```

**File: `backend/app/mcp/resources/acgme_resources.py`**

```python
"""ACGME regulation resources."""
from app.mcp.server import mcp

@mcp.resource("acgme://regulations/80-hour-rule")
async def acgme_80_hour_rule() -> str:
    """Complete documentation for ACGME 80-hour work week rule."""
    return """
# ACGME 80-Hour Work Week Rule

[Full documentation as shown earlier]
"""

@mcp.resource("acgme://regulations/1-in-7-rule")
async def acgme_one_in_seven_rule() -> str:
    """Documentation for ACGME 1-in-7 day off rule."""
    # Implementation
    pass

# Additional resources...
```

#### Step 5: Integrate with FastAPI Main App

**File: `backend/app/main.py` (updated)**

```python
"""Main FastAPI application."""
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager

from app.api.routes import auth, schedule, swaps, acgme
from app.core.config import settings
from app.db.session import async_session_maker

# Import MCP server
from app.mcp.server import mcp

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan manager."""
    # Startup
    logger.info("Starting Residency Scheduler")
    yield
    # Shutdown
    logger.info("Shutting down Residency Scheduler")
    await async_session_maker.close_all()

# Create FastAPI app
app = FastAPI(
    title="Residency Scheduler",
    version="1.0.0",
    lifespan=lifespan
)

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_methods=["*"],
    allow_headers=["*"]
)

# REST API routes
app.include_router(auth.router, prefix="/api/v1/auth", tags=["auth"])
app.include_router(schedule.router, prefix="/api/v1/schedule", tags=["schedule"])
app.include_router(swaps.router, prefix="/api/v1/swaps", tags=["swaps"])
app.include_router(acgme.router, prefix="/api/v1/acgme", tags=["acgme"])

# Mount MCP server
# Accessible via SSE at http://localhost:8000/mcp
app.mount("/mcp", mcp.get_asgi_app())

@app.get("/")
async def root():
    return {
        "message": "Residency Scheduler API",
        "version": "1.0.0",
        "endpoints": {
            "rest_api": "/api/v1",
            "docs": "/docs",
            "mcp": "/mcp"
        }
    }
```

### Service Layer Integration

**Key Principle:** **Reuse existing service layer** - don't duplicate business logic!

```python
# MCP tool wraps existing service
from app.services.swap_service import SwapService  # Existing service

@mcp.tool()
async def approve_swap(ctx: Context, swap_id: str) -> dict:
    """Approve a pending swap request."""
    user_id = ctx.request_context.auth_result.user_id

    async with async_session_maker() as db:
        # Reuse existing service method
        service = SwapService()
        result = await service.approve_swap(
            db=db,
            swap_id=swap_id,
            approver_id=user_id
        )
        await db.commit()

        return {"success": True, "swap_id": result.id}
```

**Benefits:**
- Single source of truth for business logic
- Consistent validation and behavior
- Easier testing and maintenance
- Reduced code duplication

---

## 6. Testing Strategy

### Unit Testing MCP Tools

FastMCP provides **in-memory testing** - no subprocess or network overhead:

#### Basic Tool Test

```python
"""Tests for MCP tools."""
import pytest
from fastmcp import FastMCP, Client
from datetime import date

from app.mcp.server import mcp

@pytest.mark.asyncio
async def test_get_person_schedule():
    """Test fetching a person's schedule."""
    # Use in-memory client (no subprocess!)
    async with Client(mcp) as client:
        # Call the tool
        result = await client.call_tool(
            "get_person_schedule",
            {
                "person_id": "test-person-1",
                "start_date": "2025-01-01",
                "end_date": "2025-01-31"
            }
        )

        # Verify result
        assert len(result) == 1
        data = result[0].text  # JSON string

        import json
        schedule = json.loads(data)

        assert schedule["person_id"] == "test-person-1"
        assert "assignments" in schedule
        assert isinstance(schedule["assignments"], list)
```

#### Test with Authentication

```python
from app.mcp.auth import ResidencySchedulerJWTAuth
from jose import jwt
from app.core.config import settings

@pytest.fixture
def auth_token():
    """Generate valid JWT for testing."""
    payload = {
        "sub": "test-user-123",
        "email": "test@example.com",
        "role": "FACULTY",
        "scopes": ["schedules:read", "swaps:manage"]
    }
    token = jwt.encode(payload, settings.SECRET_KEY, algorithm="HS256")
    return f"Bearer {token}"

@pytest.mark.asyncio
async def test_create_swap_with_auth(auth_token):
    """Test creating swap request with authentication."""
    async with Client(mcp, auth=auth_token) as client:
        result = await client.call_tool(
            "create_swap_request",
            {
                "params": {
                    "from_block_id": "block-1",
                    "to_block_id": "block-2",
                    "reason": "Personal emergency requiring schedule change",
                    "swap_type": "ONE_TO_ONE"
                }
            }
        )

        data = json.loads(result[0].text)
        assert data["success"] is True
        assert "swap_id" in data
```

#### Test Resource Fetching

```python
@pytest.mark.asyncio
async def test_read_acgme_regulation():
    """Test reading ACGME regulation resource."""
    async with Client(mcp) as client:
        # Read resource
        content = await client.read_resource("acgme://regulations/80-hour-rule")

        # Verify content
        assert "80-Hour Work Week Rule" in content[0].text
        assert "Maximum 80 hours/week" in content[0].text
```

### Integration Testing

Test real database operations and service layer integration:

```python
import pytest
from fastmcp import Client
from app.db.session import async_session_maker
from app.models import Person, Block, Assignment, Rotation
from sqlalchemy import select

@pytest.mark.integration
@pytest.mark.asyncio
async def test_schedule_generation_integration():
    """Integration test for schedule generation."""
    # Setup test data
    async with async_session_maker() as db:
        # Create test person
        person = Person(
            id="test-faculty-1",
            name="Dr. Test",
            email="test@example.com",
            role="FACULTY"
        )
        db.add(person)
        await db.commit()

    # Test MCP tool
    async with Client(mcp) as client:
        result = await client.call_tool(
            "get_person_schedule",
            {
                "person_id": "test-faculty-1",
                "start_date": "2025-01-01",
                "end_date": "2025-01-31"
            }
        )

        data = json.loads(result[0].text)
        assert data["person_id"] == "test-faculty-1"

    # Cleanup
    async with async_session_maker() as db:
        await db.execute(delete(Person).where(Person.id == "test-faculty-1"))
        await db.commit()
```

### Mock Patterns

Mock external dependencies while testing tools:

```python
from unittest.mock import patch, AsyncMock

@pytest.mark.asyncio
async def test_swap_with_notification_mock():
    """Test swap creation with mocked notification service."""
    with patch("app.services.notification_service.NotificationService") as mock_notif:
        # Setup mock
        mock_notif.return_value.send_email = AsyncMock(return_value=True)

        async with Client(mcp) as client:
            result = await client.call_tool(
                "create_swap_request",
                {
                    "params": {
                        "from_block_id": "block-1",
                        "to_block_id": "block-2",
                        "reason": "Testing notification mock",
                        "swap_type": "ONE_TO_ONE"
                    }
                }
            )

            # Verify notification was called
            mock_notif.return_value.send_email.assert_called_once()
```

### Test Organization

```
backend/tests/
├── mcp/                          # MCP-specific tests
│   ├── __init__.py
│   ├── test_auth.py             # Authentication tests
│   ├── test_tools.py            # Tool unit tests
│   ├── test_resources.py        # Resource tests
│   └── integration/             # Integration tests
│       ├── test_schedule_flow.py
│       ├── test_swap_flow.py
│       └── test_acgme_validation.py
│
├── conftest.py                   # Shared fixtures
└── ... (existing tests)
```

### Running Tests

```bash
# All MCP tests
pytest tests/mcp/

# Unit tests only (fast)
pytest tests/mcp/test_tools.py -v

# Integration tests
pytest tests/mcp/integration/ -m integration

# With coverage
pytest tests/mcp/ --cov=app.mcp --cov-report=html

# Specific test
pytest tests/mcp/test_tools.py::test_get_person_schedule -v
```

---

## 7. Implementation Roadmap

### Phase 1: Foundation (Week 1)

**Goals:**
- Set up basic MCP server
- Implement authentication
- Create 2-3 simple read-only resources
- Write initial tests

**Tasks:**
1. Install FastMCP: `pip install fastmcp`
2. Create `app/mcp/` directory structure
3. Implement `ResidencySchedulerJWTAuth`
4. Create basic MCP server in `server.py`
5. Add 2-3 ACGME regulation resources
6. Write unit tests for auth and resources
7. Mount MCP server in `main.py`
8. Test SSE endpoint manually

**Deliverables:**
- Working MCP server at `/mcp` endpoint
- JWT authentication functional
- Basic resources accessible
- 80%+ test coverage for new code

### Phase 2: Read Operations (Week 2)

**Goals:**
- Implement all read-only resources
- Database-backed resources
- Comprehensive testing

**Tasks:**
1. Create schedule resources (person schedules, block info)
2. Create faculty resources (availability, qualifications)
3. Create ACGME compliance resources
4. Add resource templates (e.g., `schedule://person/{id}/week`)
5. Optimize database queries (eager loading)
6. Write integration tests
7. Performance testing

**Deliverables:**
- 15-20 read-only resources
- Sub-100ms response times for simple resources
- Integration tests passing

### Phase 3: Write Operations (Week 3)

**Goals:**
- Implement core action tools
- Transaction handling
- Error management

**Tasks:**
1. Create schedule management tools
2. Create swap request tools
3. Create ACGME analysis tools
4. Implement permission checks
5. Add transaction support
6. Error handling and rollback
7. Comprehensive tool testing

**Deliverables:**
- 10-15 action tools
- Proper transaction handling
- Role-based access control enforced

### Phase 4: Advanced Features (Week 4)

**Goals:**
- Background tasks
- Admin tools
- Performance optimization

**Tasks:**
1. Implement background task for schedule generation
2. Add progress reporting
3. Create admin-only tools
4. Performance profiling and optimization
5. Load testing
6. Documentation

**Deliverables:**
- Background task support
- Admin tools functional
- Performance benchmarks established
- API documentation complete

### Phase 5: Production Readiness (Week 5)

**Goals:**
- Security hardening
- Monitoring
- Deployment preparation

**Tasks:**
1. Security audit (auth, permissions, data exposure)
2. Add request logging
3. Add metrics/monitoring
4. Rate limiting
5. Error tracking integration
6. Deployment documentation
7. User guide for LLM clients

**Deliverables:**
- Production-ready MCP server
- Monitoring dashboards
- Deployment runbook
- User documentation

---

## 8. References

### Official Documentation

- [FastMCP 2.0 Documentation](https://gofastmcp.com/getting-started/welcome)
- [FastMCP GitHub Repository](https://github.com/jlowin/fastmcp)
- [Building MCP Server with FastMCP Guide](https://mcpcat.io/guides/building-mcp-server-python-fastmcp/)
- [DataCamp: Building MCP Server and Client with FastMCP 2.0](https://www.datacamp.com/tutorial/building-mcp-server-client-fastmcp)

### Authentication & Security

- [FastMCP Authentication Documentation](https://deepwiki.com/jlowin/fastmcp/6.1-authentication-and-security)
- [FastAPI MCP SSE Server with JWT Auth Tutorial](https://newsletter.adaptiveengineer.com/p/how-to-create-a-fastapi-mcp-sse-server)
- [OAuth2 Authentication for MCP Tutorial](https://newsletter.adaptiveengineer.com/p/how-to-add-oauth2-authentication)
- [FastAPI OAuth2 with JWT Tokens](https://fastapi.tiangolo.com/tutorial/security/oauth2-jwt/)

### Integration & Tools

- [FastMCP FastAPI Integration](https://gofastmcp.com/integrations/fastapi)
- [FastMCP Tools Documentation](https://gofastmcp.com/servers/tools)
- [FastMCP Resources Documentation](https://github.com/yjacquin/fast-mcp/blob/main/docs/resources.md)
- [Speakeasy: Building FastAPI Server with FastMCP](https://www.speakeasy.com/mcp/framework-guides/building-fastapi-server)

### Testing

- [FastMCP Testing Documentation](https://gofastmcp.com/development/tests)
- [MCPcat: Unit Testing MCP Servers Guide](https://mcpcat.io/guides/writing-unit-tests-mcp-servers/)
- [MCPcat: MCP Integration Testing Guide](https://mcpcat.io/guides/integration-tests-mcp-flows/)
- [Stop Vibe-Testing Your MCP Server](https://www.jlowin.dev/blog/stop-vibe-testing-mcp-servers)

### Advanced Topics

- [Introducing FastMCP 2.0](https://www.jlowin.dev/blog/fastmcp-2)
- [FastAPI-MCP Package](https://github.com/tadata-org/fastapi_mcp)
- [Sharing Middleware Discussion](https://github.com/jlowin/fastmcp/discussions/732)
- [FastMCP PyPI Package](https://pypi.org/project/fastmcp/)

### Community Resources

- [Firecrawl: Complete FastMCP Tutorial](https://www.firecrawl.dev/blog/fastmcp-tutorial-building-mcp-servers-python)
- [Apidog: Beginner's Guide to FastMCP](https://apidog.com/blog/fastmcp/)
- [InfoQ: FastAPI-MCP Integration](https://www.infoq.com/news/2025/04/fastapi-mcp/)
- [Medium: FastMCP with LangGraph](https://medium.com/@ssiddharth408/from-crud-to-llm-in-minutes-fastmcp-langgraph-magic-ce530c70912d)

---

## Appendix A: Example Tool Implementation

### Complete Example: Swap Request Tool

```python
"""
Complete example of a production-ready MCP tool.

Demonstrates:
- Authentication and authorization
- Input validation with Pydantic
- Database transactions
- Service layer reuse
- Error handling
- Comprehensive return values
"""
from fastmcp import Context
from pydantic import BaseModel, Field, validator
from app.mcp.server import mcp
from app.db.session import async_session_maker
from app.services.swap_service import SwapService
from app.models import SwapType
from datetime import datetime
import logging

logger = logging.getLogger(__name__)


class SwapRequestInput(BaseModel):
    """Input schema for creating a swap request."""

    from_block_id: str = Field(
        ...,
        description="Block ID to swap from",
        min_length=1
    )
    to_block_id: str = Field(
        ...,
        description="Block ID to swap to",
        min_length=1
    )
    reason: str = Field(
        ...,
        description="Reason for swap (minimum 10 characters)",
        min_length=10,
        max_length=500
    )
    swap_type: SwapType = Field(
        SwapType.ONE_TO_ONE,
        description="Type of swap (ONE_TO_ONE or ABSORB)"
    )

    @validator("from_block_id", "to_block_id")
    def block_ids_different(cls, v, values):
        """Ensure from and to blocks are different."""
        if "from_block_id" in values and v == values["from_block_id"]:
            raise ValueError("Cannot swap a block with itself")
        return v


@mcp.tool()
async def create_swap_request(
    ctx: Context,
    input_data: SwapRequestInput
) -> dict:
    """
    Create a schedule swap request.

    This tool allows faculty members to request swapping their scheduled
    blocks with other faculty. The swap is subject to:
    - ACGME compliance validation
    - Qualification matching
    - Coordinator approval

    Required Permissions: FACULTY or ADMIN

    Args:
        ctx: FastMCP context with authentication
        input_data: Swap request parameters

    Returns:
        Dictionary containing:
        - success: Boolean indicating if swap was created
        - swap_id: Unique ID of created swap (if successful)
        - status: Current status of swap
        - created_at: Timestamp of creation
        - auto_match_available: Whether auto-match found candidates
        - error: Error message (if unsuccessful)
        - validation_errors: List of validation failures (if any)

    Example:
        ```python
        result = await client.call_tool("create_swap_request", {
            "input_data": {
                "from_block_id": "2025-01-15-AM",
                "to_block_id": "2025-01-22-AM",
                "reason": "Personal appointment conflict",
                "swap_type": "ONE_TO_ONE"
            }
        })
        ```
    """
    # Extract authenticated user
    user_id = ctx.request_context.auth_result.user_id
    user_role = ctx.request_context.auth_result.metadata.get("role")
    user_email = ctx.request_context.auth_result.metadata.get("email")

    logger.info(
        f"Swap request initiated: user={user_email}, "
        f"from={input_data.from_block_id}, to={input_data.to_block_id}"
    )

    # Check permissions
    if user_role not in ["FACULTY", "ADMIN", "COORDINATOR"]:
        logger.warning(
            f"Unauthorized swap attempt: user={user_email}, role={user_role}"
        )
        return {
            "success": False,
            "error": "Insufficient permissions",
            "required_role": "FACULTY, COORDINATOR, or ADMIN",
            "current_role": user_role
        }

    async with async_session_maker() as db:
        try:
            # Initialize service
            service = SwapService()

            # Phase 1: Validate swap is possible
            logger.debug("Validating swap request...")
            validation = await service.validate_swap(
                db=db,
                from_block_id=input_data.from_block_id,
                to_block_id=input_data.to_block_id,
                user_id=user_id
            )

            if not validation.is_valid:
                logger.warning(
                    f"Swap validation failed: {validation.errors}"
                )
                return {
                    "success": False,
                    "error": "Swap validation failed",
                    "validation_errors": validation.errors,
                    "suggestions": validation.suggestions
                }

            # Phase 2: Create swap request (transactional)
            logger.debug("Creating swap request...")
            swap = await service.create_swap_request(
                db=db,
                from_block_id=input_data.from_block_id,
                to_block_id=input_data.to_block_id,
                requester_id=user_id,
                reason=input_data.reason,
                swap_type=input_data.swap_type
            )

            # Phase 3: Attempt auto-matching
            logger.debug("Attempting auto-match...")
            auto_match_result = await service.find_swap_matches(
                db=db,
                swap_id=swap.id
            )

            # Commit transaction
            await db.commit()

            logger.info(
                f"Swap created successfully: swap_id={swap.id}, "
                f"auto_matches={len(auto_match_result.matches)}"
            )

            return {
                "success": True,
                "swap_id": swap.id,
                "status": swap.status,
                "created_at": swap.created_at.isoformat(),
                "from_block": {
                    "id": input_data.from_block_id,
                    "date": swap.from_block.date.isoformat(),
                    "session": swap.from_block.session
                },
                "to_block": {
                    "id": input_data.to_block_id,
                    "date": swap.to_block.date.isoformat(),
                    "session": swap.to_block.session
                },
                "auto_match_available": len(auto_match_result.matches) > 0,
                "potential_matches": len(auto_match_result.matches),
                "next_steps": (
                    "Waiting for coordinator approval"
                    if len(auto_match_result.matches) > 0
                    else "No automatic matches found - manual coordination required"
                )
            }

        except ValueError as e:
            # Business logic error (e.g., invalid block ID)
            await db.rollback()
            logger.error(f"Swap creation failed - validation error: {e}")
            return {
                "success": False,
                "error": "Invalid request",
                "message": str(e)
            }

        except PermissionError as e:
            # Authorization error
            await db.rollback()
            logger.error(f"Swap creation failed - permission denied: {e}")
            return {
                "success": False,
                "error": "Permission denied",
                "message": str(e)
            }

        except Exception as e:
            # Unexpected error
            await db.rollback()
            logger.exception("Swap creation failed - unexpected error")
            return {
                "success": False,
                "error": "Internal error",
                "message": "An unexpected error occurred. Please try again.",
                "support": "Contact support if this persists"
            }
```

---

## Appendix B: Performance Considerations

### Database Query Optimization

```python
from sqlalchemy.orm import selectinload, joinedload

@mcp.tool()
async def get_faculty_schedule_with_rotations(faculty_id: str) -> dict:
    """
    Get faculty schedule with eager-loaded relationships.

    Avoids N+1 query problem by loading related data upfront.
    """
    from app.db.session import async_session_maker
    from app.models import Person
    from sqlalchemy import select

    async with async_session_maker() as db:
        # BAD: N+1 queries
        # result = await db.execute(select(Person).where(Person.id == faculty_id))
        # person = result.scalar_one()
        # for assignment in person.assignments:  # Triggers separate query!
        #     rotation = assignment.rotation  # Another query!

        # GOOD: Single query with eager loading
        result = await db.execute(
            select(Person)
            .where(Person.id == faculty_id)
            .options(
                selectinload(Person.assignments)
                .selectinload(Assignment.rotation),
                selectinload(Person.assignments)
                .selectinload(Assignment.block)
            )
        )
        person = result.scalar_one()

        # Now all data is loaded, no additional queries
        return {
            "person": person.name,
            "assignments": [
                {
                    "rotation": a.rotation.name,
                    "block": a.block.date.isoformat()
                }
                for a in person.assignments
            ]
        }
```

### Caching Strategy

```python
from functools import lru_cache
from datetime import datetime, timedelta

# Cache static resources
@lru_cache(maxsize=10)
@mcp.resource("acgme://regulations/{regulation_name}")
async def get_acgme_regulation(regulation_name: str) -> str:
    """Cached ACGME regulation (static content)."""
    # This won't hit database repeatedly
    pass

# Cache with TTL for semi-static data
_cache = {}
_cache_ttl = {}

async def get_cached_or_fetch(key: str, fetch_func, ttl_seconds: int = 300):
    """Simple time-based cache."""
    now = datetime.now()

    if key in _cache and key in _cache_ttl:
        if now < _cache_ttl[key]:
            return _cache[key]

    # Cache miss or expired
    value = await fetch_func()
    _cache[key] = value
    _cache_ttl[key] = now + timedelta(seconds=ttl_seconds)

    return value
```

---

**End of Document**

This implementation plan provides a comprehensive roadmap for integrating FastMCP 2.0 with the Residency Scheduler application. The phased approach ensures steady progress while maintaining code quality and test coverage.
