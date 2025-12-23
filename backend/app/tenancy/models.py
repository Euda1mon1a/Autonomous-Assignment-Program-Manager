"""
Tenant models for multitenancy support.

This module defines the database models for managing tenants in the system.
Each tenant represents an isolated organization (e.g., hospital, residency program).
"""
import uuid
from datetime import datetime
from enum import Enum

from sqlalchemy import (
    Boolean,
    CheckConstraint,
    Column,
    DateTime,
    Integer,
    JSON,
    String,
    Text,
)
from sqlalchemy.orm import relationship

from app.db.base import Base
from app.db.types import GUID


class TenantStatus(str, Enum):
    """
    Tenant lifecycle status.

    Status transitions:
    PENDING -> ACTIVE -> SUSPENDED -> INACTIVE
                  |
                  -> INACTIVE (deprovisioned)
    """

    PENDING = "pending"  # Tenant created but not yet provisioned
    ACTIVE = "active"  # Tenant is active and operational
    SUSPENDED = "suspended"  # Tenant temporarily suspended (billing, violation)
    INACTIVE = "inactive"  # Tenant deprovisioned (soft delete)


class IsolationStrategy(str, Enum):
    """
    Data isolation strategy for the tenant.

    SCHEMA: Each tenant gets a dedicated PostgreSQL schema
    - Best for: Large tenants, compliance requirements, performance isolation
    - Pros: Complete isolation, easier to backup/restore individual tenants
    - Cons: Higher resource usage, schema migration complexity

    ROW_LEVEL: All tenants share tables with tenant_id filtering
    - Best for: Many small tenants, cost optimization
    - Pros: Efficient resource usage, simpler migrations
    - Cons: Requires careful query filtering, risk of data leaks
    """

    SCHEMA = "schema"
    ROW_LEVEL = "row_level"


class Tenant(Base):
    """
    Tenant model representing an isolated organization.

    Each tenant is a separate residency program or hospital that uses the
    scheduler. Tenants can have different isolation strategies, settings,
    and resource limits.

    Attributes:
        id: Unique tenant identifier (UUID)
        slug: URL-friendly identifier (e.g., 'johns-hopkins-fm')
        name: Human-readable name (e.g., 'Johns Hopkins Family Medicine')
        status: Current tenant status (pending, active, suspended, inactive)
        isolation_strategy: Data isolation method (schema or row_level)
        schema_name: PostgreSQL schema name (for schema-based isolation)
        settings: JSON field for tenant-specific configuration
        resource_limits: JSON field for usage quotas and limits
        metadata: Additional tenant information
        created_at: When the tenant was created
        updated_at: When the tenant was last modified
        activated_at: When the tenant was activated
        suspended_at: When the tenant was suspended (if applicable)
    """

    __tablename__ = "tenants"

    # Primary identification
    id = Column(GUID(), primary_key=True, default=uuid.uuid4)
    slug = Column(
        String(100), unique=True, nullable=False, index=True,
        doc="URL-friendly tenant identifier"
    )
    name = Column(String(255), nullable=False, doc="Human-readable tenant name")

    # Status and lifecycle
    status = Column(
        String(50), nullable=False, default=TenantStatus.PENDING.value, index=True,
        doc="Current tenant status"
    )

    # Isolation configuration
    isolation_strategy = Column(
        String(50), nullable=False, default=IsolationStrategy.ROW_LEVEL.value,
        doc="Data isolation strategy"
    )
    schema_name = Column(
        String(100), unique=True, nullable=True,
        doc="PostgreSQL schema name for schema-based isolation"
    )

    # Contact and billing
    admin_email = Column(String(255), nullable=False, doc="Primary admin contact")
    billing_email = Column(String(255), nullable=True, doc="Billing contact")

    # Configuration and limits
    settings = Column(
        JSON, nullable=False, default=dict,
        doc="Tenant-specific settings (ACGME rules, scheduling preferences)"
    )
    resource_limits = Column(
        JSON, nullable=False, default=dict,
        doc="Resource quotas (max users, schedules, storage)"
    )
    metadata = Column(
        JSON, nullable=False, default=dict,
        doc="Additional tenant information (address, phone, etc.)"
    )

    # Audit and tracking
    created_by = Column(GUID(), nullable=True, doc="User who created the tenant")
    notes = Column(Text, nullable=True, doc="Internal notes about the tenant")

    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(
        DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False
    )
    activated_at = Column(
        DateTime, nullable=True, doc="When tenant became active"
    )
    suspended_at = Column(
        DateTime, nullable=True, doc="When tenant was suspended"
    )

    # Relationships (if we add user-tenant mapping)
    # users = relationship("TenantUser", back_populates="tenant")

    __table_args__ = (
        CheckConstraint(
            "status IN ('pending', 'active', 'suspended', 'inactive')",
            name="check_tenant_status",
        ),
        CheckConstraint(
            "isolation_strategy IN ('schema', 'row_level')",
            name="check_isolation_strategy",
        ),
        CheckConstraint(
            "(isolation_strategy = 'schema' AND schema_name IS NOT NULL) OR "
            "(isolation_strategy = 'row_level' AND schema_name IS NULL)",
            name="check_schema_name_consistency",
        ),
    )

    def __repr__(self):
        return f"<Tenant(slug='{self.slug}', name='{self.name}', status='{self.status}')>"

    @property
    def is_active(self) -> bool:
        """Check if tenant is active and operational."""
        return self.status == TenantStatus.ACTIVE.value

    @property
    def is_suspended(self) -> bool:
        """Check if tenant is suspended."""
        return self.status == TenantStatus.SUSPENDED.value

    @property
    def uses_schema_isolation(self) -> bool:
        """Check if tenant uses schema-based isolation."""
        return self.isolation_strategy == IsolationStrategy.SCHEMA.value

    @property
    def uses_row_level_isolation(self) -> bool:
        """Check if tenant uses row-level isolation."""
        return self.isolation_strategy == IsolationStrategy.ROW_LEVEL.value

    def get_setting(self, key: str, default=None):
        """
        Get a tenant-specific setting.

        Args:
            key: Setting key (supports dot notation, e.g., 'acgme.max_hours')
            default: Default value if setting not found

        Returns:
            Setting value or default
        """
        settings = self.settings or {}
        keys = key.split(".")
        value = settings
        for k in keys:
            if isinstance(value, dict):
                value = value.get(k)
            else:
                return default
        return value if value is not None else default

    def get_resource_limit(self, key: str, default=None):
        """
        Get a resource limit for this tenant.

        Args:
            key: Limit key (e.g., 'max_users', 'max_schedules')
            default: Default value if limit not found

        Returns:
            Limit value or default
        """
        limits = self.resource_limits or {}
        return limits.get(key, default)


class TenantUser(Base):
    """
    Many-to-many relationship between tenants and users.

    Allows users to belong to multiple tenants (e.g., faculty who work
    at multiple residency programs).

    Attributes:
        id: Unique identifier
        tenant_id: Reference to tenant
        user_id: Reference to user
        role: User's role within this tenant (admin, coordinator, faculty, etc.)
        is_primary: Whether this is the user's primary tenant
        created_at: When the user was added to the tenant
    """

    __tablename__ = "tenant_users"

    id = Column(GUID(), primary_key=True, default=uuid.uuid4)
    tenant_id = Column(
        GUID(), nullable=False, index=True,
        doc="Tenant this user belongs to"
    )
    user_id = Column(
        GUID(), nullable=False, index=True,
        doc="User account"
    )

    # Role within this tenant (can differ from global role)
    role = Column(
        String(50), nullable=False, default="coordinator",
        doc="User's role within this tenant"
    )

    # Primary tenant flag
    is_primary = Column(
        Boolean, default=False,
        doc="Whether this is the user's primary tenant"
    )

    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(
        DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False
    )

    # Relationships
    # tenant = relationship("Tenant", back_populates="users")
    # user = relationship("User", back_populates="tenants")

    __table_args__ = (
        # Ensure user can only be in a tenant once
        CheckConstraint(
            "tenant_id IS NOT NULL AND user_id IS NOT NULL",
            name="check_tenant_user_not_null",
        ),
        # Note: We'd add a unique constraint on (tenant_id, user_id)
        # but that requires creating the constraint separately
    )

    def __repr__(self):
        return f"<TenantUser(tenant_id='{self.tenant_id}', user_id='{self.user_id}')>"


class TenantAuditLog(Base):
    """
    Audit log for tenant-related operations.

    Tracks tenant creation, updates, provisioning, suspension, and
    cross-tenant access by administrators.

    Attributes:
        id: Unique identifier
        tenant_id: Tenant this event relates to
        user_id: User who performed the action
        action: Action performed (create, update, suspend, etc.)
        resource_type: Type of resource affected (tenant, user, schedule)
        resource_id: ID of the affected resource
        changes: JSON field with before/after values
        ip_address: IP address of the user
        user_agent: User agent string
        created_at: When the event occurred
    """

    __tablename__ = "tenant_audit_logs"

    id = Column(GUID(), primary_key=True, default=uuid.uuid4)
    tenant_id = Column(
        GUID(), nullable=True, index=True,
        doc="Tenant this audit event relates to"
    )
    user_id = Column(
        GUID(), nullable=True, index=True,
        doc="User who performed the action"
    )

    # Event details
    action = Column(
        String(100), nullable=False, index=True,
        doc="Action performed (create_tenant, suspend_tenant, cross_tenant_query)"
    )
    resource_type = Column(
        String(100), nullable=True,
        doc="Type of resource affected"
    )
    resource_id = Column(
        GUID(), nullable=True,
        doc="ID of affected resource"
    )

    # Change tracking
    changes = Column(
        JSON, nullable=True,
        doc="Before/after values for the change"
    )

    # Request context
    ip_address = Column(String(45), nullable=True, doc="IPv4 or IPv6 address")
    user_agent = Column(Text, nullable=True, doc="User agent string")

    # Timestamp
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False, index=True)

    def __repr__(self):
        return f"<TenantAuditLog(action='{self.action}', tenant_id='{self.tenant_id}')>"
