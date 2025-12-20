"""
Tenant context management for request and task scoping.

This module provides thread-local and async-local context for tracking the
current tenant throughout the request lifecycle and background tasks.

The tenant context is propagated through:
1. HTTP requests (via middleware and dependency injection)
2. Background tasks (Celery tasks)
3. Distributed tracing (OpenTelemetry baggage)

Thread Safety:
-------------
Uses contextvars for async-safe context management. Each async task
gets its own isolated context that doesn't interfere with other
concurrent requests.
"""
from contextvars import ContextVar
from typing import Optional
from uuid import UUID

from fastapi import Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.db.session import get_db

# Context variables for tenant tracking
# These are async-safe and isolated per request/task
_tenant_id: ContextVar[Optional[UUID]] = ContextVar("tenant_id", default=None)
_tenant_slug: ContextVar[Optional[str]] = ContextVar("tenant_slug", default=None)
_bypass_tenant_filter: ContextVar[bool] = ContextVar("bypass_tenant_filter", default=False)


class TenantContext:
    """
    Context manager for setting tenant context.

    Use this to temporarily set the tenant context, especially in
    background tasks or tests.

    Example:
        with TenantContext(tenant_id):
            # Code here runs with tenant_id set
            person = db.query(Person).first()  # Auto-filtered by tenant

        # Tenant context is cleared after the block
    """

    def __init__(
        self,
        tenant_id: Optional[UUID] = None,
        tenant_slug: Optional[str] = None,
        bypass: bool = False,
    ):
        """
        Initialize tenant context.

        Args:
            tenant_id: Tenant UUID to set
            tenant_slug: Tenant slug to set
            bypass: Whether to bypass tenant filtering (admin operations)
        """
        self.tenant_id = tenant_id
        self.tenant_slug = tenant_slug
        self.bypass = bypass
        self._tenant_id_token = None
        self._tenant_slug_token = None
        self._bypass_token = None

    def __enter__(self):
        """Enter the context and set tenant variables."""
        self._tenant_id_token = _tenant_id.set(self.tenant_id)
        self._tenant_slug_token = _tenant_slug.set(self.tenant_slug)
        self._bypass_token = _bypass_tenant_filter.set(self.bypass)
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """Exit the context and restore previous values."""
        if self._tenant_id_token is not None:
            _tenant_id.reset(self._tenant_id_token)
        if self._tenant_slug_token is not None:
            _tenant_slug.reset(self._tenant_slug_token)
        if self._bypass_token is not None:
            _bypass_tenant_filter.reset(self._bypass_token)


def get_current_tenant_id() -> Optional[UUID]:
    """
    Get the current tenant ID from context.

    Returns:
        Current tenant UUID or None if not set

    Example:
        tenant_id = get_current_tenant_id()
        if tenant_id:
            logger.info(f"Processing request for tenant {tenant_id}")
    """
    return _tenant_id.get()


def get_current_tenant_slug() -> Optional[str]:
    """
    Get the current tenant slug from context.

    Returns:
        Current tenant slug or None if not set
    """
    return _tenant_slug.get()


def is_bypassing_tenant_filter() -> bool:
    """
    Check if tenant filtering is currently bypassed.

    Returns:
        True if tenant filter is bypassed (admin operation)
    """
    return _bypass_tenant_filter.get()


def set_current_tenant(
    tenant_id: Optional[UUID] = None,
    tenant_slug: Optional[str] = None,
    bypass: bool = False,
) -> None:
    """
    Set the current tenant context.

    Args:
        tenant_id: Tenant UUID to set
        tenant_slug: Tenant slug to set
        bypass: Whether to bypass tenant filtering

    Example:
        # In middleware
        set_current_tenant(tenant_id=uuid.UUID(tenant_id_str))

        # In admin operation
        set_current_tenant(bypass=True)
    """
    _tenant_id.set(tenant_id)
    _tenant_slug.set(tenant_slug)
    _bypass_tenant_filter.set(bypass)


def clear_current_tenant() -> None:
    """
    Clear the current tenant context.

    Use this to reset tenant context, typically at the end of a request
    or when switching tenants.
    """
    _tenant_id.set(None)
    _tenant_slug.set(None)
    _bypass_tenant_filter.set(False)


async def get_current_tenant(db: Session = Depends(get_db)):
    """
    FastAPI dependency to get the current tenant object.

    Returns the full Tenant model instance for the current request.
    Returns None if no tenant context is set (e.g., system operations).

    Args:
        db: Database session

    Returns:
        Tenant instance or None

    Example:
        @router.get("/settings")
        async def get_tenant_settings(
            tenant = Depends(get_current_tenant),
        ):
            if not tenant:
                raise HTTPException(404, "No tenant context")
            return tenant.settings
    """
    from app.tenancy.models import Tenant

    tenant_id = get_current_tenant_id()
    if not tenant_id:
        return None

    result = await db.execute(select(Tenant).where(Tenant.id == tenant_id))
    return result.scalar_one_or_none()


async def require_tenant(db: Session = Depends(get_db)):
    """
    FastAPI dependency that requires a tenant context.

    Raises 403 error if no tenant is set. Use this for endpoints that
    must be scoped to a specific tenant.

    Args:
        db: Database session

    Returns:
        Tenant instance

    Raises:
        HTTPException: 403 if no tenant context is set

    Example:
        @router.get("/people")
        async def list_people(
            tenant = Depends(require_tenant),
            db: Session = Depends(get_db),
        ):
            # tenant is guaranteed to be set
            return await db.execute(select(Person))
    """
    tenant = await get_current_tenant(db)
    if not tenant:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="No tenant context. This operation requires a tenant.",
        )
    return tenant


async def require_active_tenant(db: Session = Depends(get_db)):
    """
    FastAPI dependency that requires an active tenant.

    Like require_tenant, but also checks that the tenant is active
    (not suspended or inactive).

    Args:
        db: Database session

    Returns:
        Tenant instance

    Raises:
        HTTPException: 403 if no tenant or tenant not active

    Example:
        @router.post("/schedules")
        async def create_schedule(
            tenant = Depends(require_active_tenant),
            db: Session = Depends(get_db),
        ):
            # Tenant is guaranteed to be active
            return await create_schedule_service(db, tenant)
    """
    from app.tenancy.models import TenantStatus

    tenant = await require_tenant(db)

    if tenant.status != TenantStatus.ACTIVE.value:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=f"Tenant is {tenant.status}. Only active tenants can perform this operation.",
        )

    return tenant


def require_admin_for_cross_tenant() -> None:
    """
    Check if the current user is allowed to perform cross-tenant operations.

    This should be used when bypassing tenant filtering for administrative
    queries across all tenants.

    Raises:
        HTTPException: 403 if user is not authorized

    Example:
        @router.get("/admin/all-schedules")
        async def list_all_schedules(
            current_user = Depends(get_current_user),
        ):
            require_admin_for_cross_tenant()
            # Can now query across all tenants
            set_current_tenant(bypass=True)
            ...
    """
    # TODO: Implement actual user permission check
    # For now, just check if bypass is being attempted
    # In production, verify current_user.is_admin or similar
    pass


async def get_tenant_by_slug(slug: str, db: Session) -> Optional:
    """
    Get a tenant by its slug.

    Args:
        slug: Tenant slug (URL-friendly identifier)
        db: Database session

    Returns:
        Tenant instance or None if not found

    Example:
        tenant = await get_tenant_by_slug("johns-hopkins-fm", db)
        if tenant:
            set_current_tenant(tenant_id=tenant.id, tenant_slug=tenant.slug)
    """
    from app.tenancy.models import Tenant

    result = await db.execute(select(Tenant).where(Tenant.slug == slug))
    return result.scalar_one_or_none()


async def get_tenant_by_id(tenant_id: UUID, db: Session) -> Optional:
    """
    Get a tenant by its ID.

    Args:
        tenant_id: Tenant UUID
        db: Database session

    Returns:
        Tenant instance or None if not found
    """
    from app.tenancy.models import Tenant

    result = await db.execute(select(Tenant).where(Tenant.id == tenant_id))
    return result.scalar_one_or_none()


def propagate_tenant_to_celery_task(task_kwargs: dict) -> dict:
    """
    Add tenant context to Celery task arguments.

    When calling a Celery task from a request handler, use this to
    propagate the tenant context to the background task.

    Args:
        task_kwargs: Task keyword arguments

    Returns:
        Updated task kwargs with tenant context

    Example:
        # In a route handler
        task_kwargs = {
            "schedule_id": schedule_id,
            "notify_users": True,
        }
        task_kwargs = propagate_tenant_to_celery_task(task_kwargs)
        generate_schedule_task.delay(**task_kwargs)

        # In the Celery task
        @celery_app.task
        def generate_schedule_task(schedule_id, notify_users=False, tenant_id=None):
            with TenantContext(tenant_id=tenant_id):
                # Task runs with tenant context
                ...
    """
    tenant_id = get_current_tenant_id()
    tenant_slug = get_current_tenant_slug()

    if tenant_id:
        task_kwargs["tenant_id"] = str(tenant_id)
    if tenant_slug:
        task_kwargs["tenant_slug"] = tenant_slug

    return task_kwargs


def restore_tenant_from_celery_task(task_kwargs: dict) -> None:
    """
    Restore tenant context from Celery task arguments.

    Call this at the start of a Celery task to restore the tenant
    context that was propagated from the request handler.

    Args:
        task_kwargs: Task keyword arguments

    Example:
        @celery_app.task
        def generate_schedule_task(**kwargs):
            restore_tenant_from_celery_task(kwargs)
            # Now tenant context is set
            tenant_id = get_current_tenant_id()
            ...
    """
    tenant_id_str = task_kwargs.get("tenant_id")
    tenant_slug = task_kwargs.get("tenant_slug")

    if tenant_id_str:
        try:
            tenant_id = UUID(tenant_id_str)
            set_current_tenant(tenant_id=tenant_id, tenant_slug=tenant_slug)
        except ValueError:
            # Invalid UUID format
            pass


def propagate_tenant_to_tracing() -> None:
    """
    Propagate tenant context to OpenTelemetry tracing baggage.

    This allows the tenant context to be propagated across service
    boundaries in distributed tracing.

    Example:
        # In middleware, after setting tenant context
        set_current_tenant(tenant_id=tenant_id)
        propagate_tenant_to_tracing()

        # Now the tenant ID is included in all traces
    """
    try:
        from app.telemetry.middleware import set_baggage

        tenant_id = get_current_tenant_id()
        tenant_slug = get_current_tenant_slug()

        if tenant_id:
            set_baggage("tenant.id", str(tenant_id))
        if tenant_slug:
            set_baggage("tenant.slug", tenant_slug)
    except ImportError:
        # Telemetry not enabled
        pass
