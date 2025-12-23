"""
Multitenancy support for the Residency Scheduler application.

This module provides comprehensive multitenancy capabilities including:
- Tenant identification and context propagation
- Schema-based and row-level data isolation
- Tenant provisioning and management
- Cross-tenant queries for administrative operations

Architecture:
-----------
The multitenancy system supports two isolation strategies:

1. Schema-based isolation:
   - Each tenant gets a dedicated PostgreSQL schema
   - Complete data isolation at the database level
   - Better for large tenants with compliance requirements
   - Higher resource usage but maximum isolation

2. Row-level isolation:
   - All tenants share tables with tenant_id columns
   - Data filtered by tenant_id in queries
   - More efficient resource usage
   - Requires careful query filtering to prevent data leaks

Tenant Context:
--------------
Tenant context is propagated through:
- Request middleware (HTTP headers)
- Database session scoping
- Background task execution (Celery)
- OpenTelemetry baggage (distributed tracing)

Security Considerations:
-----------------------
- All queries are automatically scoped to the current tenant
- Admin users can perform cross-tenant queries (with explicit permission)
- Tenant ID validation prevents SQL injection
- Audit logging tracks all cross-tenant access
- Schema isolation prevents accidental data leaks

Usage Example:
-------------
    # In a FastAPI route
    from app.tenancy.context import get_current_tenant, require_tenant
    from app.tenancy.isolation import TenantScope

    @router.get("/people")
    async def list_people(
        db: Session = Depends(get_db),
        tenant = Depends(require_tenant),
    ):
        # Query is automatically scoped to current tenant
        async with TenantScope(db, tenant.id):
            people = await db.execute(select(Person))
            return people.scalars().all()

    # Admin cross-tenant query
    @router.get("/admin/all-people")
    async def list_all_people(
        db: Session = Depends(get_db),
        user = Depends(require_admin),
    ):
        # Explicitly bypass tenant filtering (admin only)
        async with TenantScope(db, bypass=True):
            people = await db.execute(select(Person))
            return people.scalars().all()
"""

from app.tenancy.context import (
    TenantContext,
    clear_current_tenant,
    get_current_tenant,
    get_current_tenant_id,
    require_tenant,
    set_current_tenant,
)
from app.tenancy.isolation import (
    IsolationStrategy,
    TenantFilter,
    TenantScope,
    get_tenant_schema,
)
from app.tenancy.models import Tenant, TenantStatus

__all__ = [
    # Context management
    "get_current_tenant",
    "get_current_tenant_id",
    "set_current_tenant",
    "clear_current_tenant",
    "require_tenant",
    "TenantContext",
    # Isolation
    "IsolationStrategy",
    "TenantScope",
    "TenantFilter",
    "get_tenant_schema",
    # Models
    "Tenant",
    "TenantStatus",
]
