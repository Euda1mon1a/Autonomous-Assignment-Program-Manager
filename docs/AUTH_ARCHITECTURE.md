# Authentication Architecture

## Document Purpose

This document defines the complete authentication and authorization architecture for the Residency Scheduler application. It serves as the specification for Sonnet's implementation.

**Author:** Opus 4.5 (Strategic Architect)
**Status:** APPROVED FOR IMPLEMENTATION
**Last Updated:** 2024-12-13

---

## Table of Contents

1. [Executive Summary](#executive-summary)
2. [Architecture Decision: JWT vs Sessions](#architecture-decision-jwt-vs-sessions)
3. [User Model Design](#user-model-design)
4. [Role-Based Access Control (RBAC)](#role-based-access-control-rbac)
5. [JWT Token Flow](#jwt-token-flow)
6. [Token Storage Strategy](#token-storage-strategy)
7. [Backend Implementation Patterns](#backend-implementation-patterns)
8. [Frontend Implementation Patterns](#frontend-implementation-patterns)
9. [Security Considerations](#security-considerations)
10. [ACGME Audit Trail Requirements](#acgme-audit-trail-requirements)
11. [API Endpoint Specifications](#api-endpoint-specifications)
12. [Implementation Checklist](#implementation-checklist)

---

## Executive Summary

The Residency Scheduler requires a robust authentication system that:

- Secures all schedule management operations
- Enforces role-based permissions (admin, coordinator, faculty)
- Maintains an audit trail for ACGME compliance
- Provides seamless user experience with automatic token refresh
- Works across browser sessions with secure token storage

**Key Decisions:**
- **Strategy:** JWT with access + refresh token pattern
- **Storage:** HttpOnly cookies for security
- **User Model:** Separate from Person model (schedulable entities)
- **Password Storage:** bcrypt with 12 rounds

---

## Architecture Decision: JWT vs Sessions

### Decision: JWT with Dual Token Pattern

**Rationale:**

| Criteria | JWT | Sessions |
|----------|-----|----------|
| Statelessness | ✅ No server-side storage | ❌ Requires session store |
| Horizontal scaling | ✅ Trivial | ⚠️ Requires sticky sessions or shared store |
| API-first design | ✅ Native fit | ⚠️ PGY2-01ie management complexity |
| Revocation | ⚠️ Requires refresh token rotation | ✅ Immediate |
| Existing dependencies | ✅ python-jose already installed | ❌ Would need redis/memcached |

**Chosen Pattern:** Access Token + Refresh Token

- **Access Token:** Short-lived (15 minutes), contains user claims
- **Refresh Token:** Long-lived (7 days), used only to obtain new access tokens
- **Token Rotation:** Refresh tokens are single-use; each refresh issues a new pair

---

## User Model Design

### Distinction: User vs Person

**Important:** The existing `Person` model represents **schedulable entities** (residents and faculty who appear on schedules). The `User` model represents **system users** (people who log in and manage schedules).

A User MAY be linked to a Person (e.g., a faculty member who both appears on schedules AND manages them), but this is not required (e.g., an admin who doesn't appear on schedules).

### User Model Schema

```python
# backend/app/models/user.py

class User(Base):
    """System user for authentication and authorization."""
    __tablename__ = "users"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    email = Column(String(255), unique=True, nullable=False, index=True)
    hashed_password = Column(String(255), nullable=False)

    # Profile
    full_name = Column(String(255), nullable=False)

    # Role and permissions
    role = Column(String(50), nullable=False, default="faculty")

    # Optional link to Person (for faculty who also manage schedules)
    person_id = Column(UUID(as_uuid=True), ForeignKey("people.id"), nullable=True)

    # Account status
    is_active = Column(Boolean, default=True)
    is_verified = Column(Boolean, default=False)  # Email verified

    # Security
    failed_login_attempts = Column(Integer, default=0)
    locked_until = Column(DateTime, nullable=True)
    password_changed_at = Column(DateTime, default=datetime.utcnow)

    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    last_login_at = Column(DateTime, nullable=True)

    # Relationships
    person = relationship("Person", foreign_keys=[person_id])
    audit_logs = relationship("AuditLog", back_populates="user")
    refresh_tokens = relationship("RefreshToken", back_populates="user", cascade="all, delete-orphan")

    __table_args__ = (
        CheckConstraint("role IN ('admin', 'coordinator', 'faculty')", name="check_user_role"),
    )
```

### Refresh Token Model

```python
# backend/app/models/refresh_token.py

class RefreshToken(Base):
    """Tracks active refresh tokens for revocation and rotation."""
    __tablename__ = "refresh_tokens"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)
    token_hash = Column(String(255), nullable=False, index=True)  # SHA-256 hash

    # Token metadata
    device_info = Column(String(255), nullable=True)  # User-agent or device ID
    ip_address = Column(String(45), nullable=True)    # IPv6-compatible

    # Lifecycle
    issued_at = Column(DateTime, default=datetime.utcnow)
    expires_at = Column(DateTime, nullable=False)
    revoked_at = Column(DateTime, nullable=True)
    replaced_by = Column(UUID(as_uuid=True), nullable=True)  # For token rotation tracking

    # Relationships
    user = relationship("User", back_populates="refresh_tokens")
```

---

## Role-Based Access Control (RBAC)

### Role Hierarchy

```
┌─────────────────────────────────────────────────────────────────┐
│                         ADMIN                                    │
│  Full system access. Can manage users, settings, all schedules. │
└───────────────────────────┬─────────────────────────────────────┘
                            │ inherits
                            ▼
┌─────────────────────────────────────────────────────────────────┐
│                      COORDINATOR                                 │
│  Schedule management. Can create/modify schedules, manage       │
│  people, handle emergency coverage. Cannot manage users.        │
└───────────────────────────┬─────────────────────────────────────┘
                            │ inherits
                            ▼
┌─────────────────────────────────────────────────────────────────┐
│                        FACULTY                                   │
│  View access. Can view schedules, their own assignments,        │
│  request absences. Limited modification rights.                 │
└─────────────────────────────────────────────────────────────────┘
```

### Permission Matrix

| Resource | Action | Admin | Coordinator | Faculty |
|----------|--------|-------|-------------|---------|
| **Users** | Create | ✅ | ❌ | ❌ |
| **Users** | Read (all) | ✅ | ❌ | ❌ |
| **Users** | Read (self) | ✅ | ✅ | ✅ |
| **Users** | Update (any) | ✅ | ❌ | ❌ |
| **Users** | Update (self) | ✅ | ✅ | ✅ |
| **Users** | Delete | ✅ | ❌ | ❌ |
| **Users** | Change role | ✅ | ❌ | ❌ |
| **People** | Create | ✅ | ✅ | ❌ |
| **People** | Read | ✅ | ✅ | ✅ |
| **People** | Update | ✅ | ✅ | ❌ |
| **People** | Delete | ✅ | ✅ | ❌ |
| **Schedules** | Generate | ✅ | ✅ | ❌ |
| **Schedules** | Read | ✅ | ✅ | ✅ |
| **Schedules** | Export | ✅ | ✅ | ✅ |
| **Assignments** | Create | ✅ | ✅ | ❌ |
| **Assignments** | Update | ✅ | ✅ | ❌ |
| **Assignments** | Delete | ✅ | ✅ | ❌ |
| **Absences** | Create (any) | ✅ | ✅ | ❌ |
| **Absences** | Create (self*) | ✅ | ✅ | ✅ |
| **Absences** | Read | ✅ | ✅ | ✅ |
| **Absences** | Update (any) | ✅ | ✅ | ❌ |
| **Absences** | Delete | ✅ | ✅ | ❌ |
| **Templates** | Create | ✅ | ✅ | ❌ |
| **Templates** | Read | ✅ | ✅ | ✅ |
| **Templates** | Update | ✅ | ✅ | ❌ |
| **Templates** | Delete | ✅ | ❌ | ❌ |
| **Compliance** | View reports | ✅ | ✅ | ✅ |
| **Compliance** | Override violations | ✅ | ✅ | ❌ |
| **Emergency Coverage** | Request | ✅ | ✅ | ❌ |
| **Settings** | View | ✅ | ✅ | ✅ |
| **Settings** | Modify | ✅ | ❌ | ❌ |
| **Audit Logs** | View | ✅ | ❌ | ❌ |

*\* Faculty can only create absence requests for their linked Person record*

### Permission Implementation

```python
# backend/app/core/permissions.py

from enum import Enum
from typing import Set

class Permission(str, Enum):
    # User management
    USERS_CREATE = "users:create"
    USERS_READ_ALL = "users:read:all"
    USERS_READ_SELF = "users:read:self"
    USERS_UPDATE_ANY = "users:update:any"
    USERS_UPDATE_SELF = "users:update:self"
    USERS_DELETE = "users:delete"
    USERS_CHANGE_ROLE = "users:change_role"

    # People management
    PEOPLE_CREATE = "people:create"
    PEOPLE_READ = "people:read"
    PEOPLE_UPDATE = "people:update"
    PEOPLE_DELETE = "people:delete"

    # Schedule management
    SCHEDULES_GENERATE = "schedules:generate"
    SCHEDULES_READ = "schedules:read"
    SCHEDULES_EXPORT = "schedules:export"

    # Assignment management
    ASSIGNMENTS_CREATE = "assignments:create"
    ASSIGNMENTS_UPDATE = "assignments:update"
    ASSIGNMENTS_DELETE = "assignments:delete"

    # Absence management
    ABSENCES_CREATE_ANY = "absences:create:any"
    ABSENCES_CREATE_SELF = "absences:create:self"
    ABSENCES_READ = "absences:read"
    ABSENCES_UPDATE_ANY = "absences:update:any"
    ABSENCES_DELETE = "absences:delete"

    # Template management
    TEMPLATES_CREATE = "templates:create"
    TEMPLATES_READ = "templates:read"
    TEMPLATES_UPDATE = "templates:update"
    TEMPLATES_DELETE = "templates:delete"

    # Compliance
    COMPLIANCE_VIEW = "compliance:view"
    COMPLIANCE_OVERRIDE = "compliance:override"

    # Emergency coverage
    EMERGENCY_REQUEST = "emergency:request"

    # Settings
    SETTINGS_VIEW = "settings:view"
    SETTINGS_MODIFY = "settings:modify"

    # Audit
    AUDIT_VIEW = "audit:view"


# Role to permissions mapping
ROLE_PERMISSIONS: dict[str, Set[Permission]] = {
    "faculty": {
        Permission.USERS_READ_SELF,
        Permission.USERS_UPDATE_SELF,
        Permission.PEOPLE_READ,
        Permission.SCHEDULES_READ,
        Permission.SCHEDULES_EXPORT,
        Permission.ABSENCES_CREATE_SELF,
        Permission.ABSENCES_READ,
        Permission.TEMPLATES_READ,
        Permission.COMPLIANCE_VIEW,
        Permission.SETTINGS_VIEW,
    },
    "coordinator": {
        # Inherits all faculty permissions
        Permission.USERS_READ_SELF,
        Permission.USERS_UPDATE_SELF,
        Permission.PEOPLE_CREATE,
        Permission.PEOPLE_READ,
        Permission.PEOPLE_UPDATE,
        Permission.PEOPLE_DELETE,
        Permission.SCHEDULES_GENERATE,
        Permission.SCHEDULES_READ,
        Permission.SCHEDULES_EXPORT,
        Permission.ASSIGNMENTS_CREATE,
        Permission.ASSIGNMENTS_UPDATE,
        Permission.ASSIGNMENTS_DELETE,
        Permission.ABSENCES_CREATE_ANY,
        Permission.ABSENCES_CREATE_SELF,
        Permission.ABSENCES_READ,
        Permission.ABSENCES_UPDATE_ANY,
        Permission.ABSENCES_DELETE,
        Permission.TEMPLATES_CREATE,
        Permission.TEMPLATES_READ,
        Permission.TEMPLATES_UPDATE,
        Permission.COMPLIANCE_VIEW,
        Permission.COMPLIANCE_OVERRIDE,
        Permission.EMERGENCY_REQUEST,
        Permission.SETTINGS_VIEW,
    },
    "admin": {
        # All permissions
        Permission.USERS_CREATE,
        Permission.USERS_READ_ALL,
        Permission.USERS_READ_SELF,
        Permission.USERS_UPDATE_ANY,
        Permission.USERS_UPDATE_SELF,
        Permission.USERS_DELETE,
        Permission.USERS_CHANGE_ROLE,
        Permission.PEOPLE_CREATE,
        Permission.PEOPLE_READ,
        Permission.PEOPLE_UPDATE,
        Permission.PEOPLE_DELETE,
        Permission.SCHEDULES_GENERATE,
        Permission.SCHEDULES_READ,
        Permission.SCHEDULES_EXPORT,
        Permission.ASSIGNMENTS_CREATE,
        Permission.ASSIGNMENTS_UPDATE,
        Permission.ASSIGNMENTS_DELETE,
        Permission.ABSENCES_CREATE_ANY,
        Permission.ABSENCES_CREATE_SELF,
        Permission.ABSENCES_READ,
        Permission.ABSENCES_UPDATE_ANY,
        Permission.ABSENCES_DELETE,
        Permission.TEMPLATES_CREATE,
        Permission.TEMPLATES_READ,
        Permission.TEMPLATES_UPDATE,
        Permission.TEMPLATES_DELETE,
        Permission.COMPLIANCE_VIEW,
        Permission.COMPLIANCE_OVERRIDE,
        Permission.EMERGENCY_REQUEST,
        Permission.SETTINGS_VIEW,
        Permission.SETTINGS_MODIFY,
        Permission.AUDIT_VIEW,
    },
}


def has_permission(role: str, permission: Permission) -> bool:
    """Check if a role has a specific permission."""
    return permission in ROLE_PERMISSIONS.get(role, set())


def get_permissions(role: str) -> Set[Permission]:
    """Get all permissions for a role."""
    return ROLE_PERMISSIONS.get(role, set())
```

---

## JWT Token Flow

### Token Specifications

| Token Type | Lifetime | Storage | Contains |
|------------|----------|---------|----------|
| Access Token | 15 minutes | HttpOnly cookie | user_id, email, role, permissions |
| Refresh Token | 7 days | HttpOnly cookie | token_id (jti), user_id |

### Token Payloads

**Access Token Claims:**
```json
{
  "sub": "550e8400-e29b-41d4-a716-446655440000",  // user_id
  "email": "coordinator@hospital.org",
  "role": "coordinator",
  "permissions": ["schedules:generate", "people:create", ...],
  "person_id": "660e8400-e29b-41d4-a716-446655440000",  // optional
  "iat": 1702483200,
  "exp": 1702484100,
  "type": "access"
}
```

**Refresh Token Claims:**
```json
{
  "sub": "550e8400-e29b-41d4-a716-446655440000",  // user_id
  "jti": "770e8400-e29b-41d4-a716-446655440000",  // token_id for revocation
  "iat": 1702483200,
  "exp": 1703088000,
  "type": "refresh"
}
```

### Authentication Flows

#### 1. Login Flow

```
┌──────────┐                    ┌──────────┐                    ┌──────────┐
│  Client  │                    │  Backend │                    │ Database │
└────┬─────┘                    └────┬─────┘                    └────┬─────┘
     │                               │                               │
     │  POST /api/auth/login         │                               │
     │  {email, password}            │                               │
     │──────────────────────────────>│                               │
     │                               │                               │
     │                               │  Query user by email          │
     │                               │──────────────────────────────>│
     │                               │                               │
     │                               │  User record                  │
     │                               │<──────────────────────────────│
     │                               │                               │
     │                               │  Verify password (bcrypt)     │
     │                               │  Check account status         │
     │                               │                               │
     │                               │  Generate access token (JWT)  │
     │                               │  Generate refresh token (JWT) │
     │                               │                               │
     │                               │  Store refresh token hash     │
     │                               │──────────────────────────────>│
     │                               │                               │
     │  Set-PGY2-01ie: access_token     │                               │
     │  Set-PGY2-01ie: refresh_token    │                               │
     │  {user: {...}}                │                               │
     │<──────────────────────────────│                               │
     │                               │                               │
```

#### 2. Authenticated Request Flow

```
┌──────────┐                    ┌──────────┐
│  Client  │                    │  Backend │
└────┬─────┘                    └────┬─────┘
     │                               │
     │  GET /api/schedule            │
     │  PGY2-01ie: access_token=...     │
     │──────────────────────────────>│
     │                               │
     │                               │  Validate JWT signature
     │                               │  Check expiration
     │                               │  Extract user claims
     │                               │  Verify permissions
     │                               │
     │  200 OK                       │
     │  {schedule data}              │
     │<──────────────────────────────│
     │                               │
```

#### 3. Token Refresh Flow (Silent Refresh)

```
┌──────────┐                    ┌──────────┐                    ┌──────────┐
│  Client  │                    │  Backend │                    │ Database │
└────┬─────┘                    └────┬─────┘                    └────┬─────┘
     │                               │                               │
     │  Access token expired!        │                               │
     │                               │                               │
     │  POST /api/auth/refresh       │                               │
     │  PGY2-01ie: refresh_token=...    │                               │
     │──────────────────────────────>│                               │
     │                               │                               │
     │                               │  Validate refresh JWT         │
     │                               │  Extract jti (token_id)       │
     │                               │                               │
     │                               │  Lookup token by hash         │
     │                               │──────────────────────────────>│
     │                               │                               │
     │                               │  Token record                 │
     │                               │<──────────────────────────────│
     │                               │                               │
     │                               │  Check not revoked            │
     │                               │  Check not expired            │
     │                               │                               │
     │                               │  Mark old token as revoked    │
     │                               │  Generate NEW token pair      │
     │                               │  Store new refresh hash       │
     │                               │──────────────────────────────>│
     │                               │                               │
     │  Set-PGY2-01ie: access_token     │                               │
     │  Set-PGY2-01ie: refresh_token    │                               │
     │<──────────────────────────────│                               │
     │                               │                               │
```

#### 4. Logout Flow

```
┌──────────┐                    ┌──────────┐                    ┌──────────┐
│  Client  │                    │  Backend │                    │ Database │
└────┬─────┘                    └────┬─────┘                    └────┬─────┘
     │                               │                               │
     │  POST /api/auth/logout        │                               │
     │  PGY2-01ie: refresh_token=...    │                               │
     │──────────────────────────────>│                               │
     │                               │                               │
     │                               │  Revoke refresh token         │
     │                               │──────────────────────────────>│
     │                               │                               │
     │  Set-PGY2-01ie: access_token=""  │                               │
     │  Set-PGY2-01ie: refresh_token="" │                               │
     │  (expires=0, clear cookies)   │                               │
     │<──────────────────────────────│                               │
     │                               │                               │
```

---

## Token Storage Strategy

### Decision: HttpOnly PGY2-01ies

**Rationale:**

| Storage Method | XSS Vulnerable | CSRF Vulnerable | Automatic Sending |
|----------------|----------------|-----------------|-------------------|
| localStorage | ✅ Yes | ❌ No | ❌ No (manual) |
| sessionStorage | ✅ Yes | ❌ No | ❌ No (manual) |
| HttpOnly PGY2-01ie | ❌ No | ✅ Yes (mitigable) | ✅ Yes |

HttpOnly cookies cannot be accessed by JavaScript, making them immune to XSS attacks. CSRF is mitigated through:
- SameSite=Lax cookie attribute
- CSRF token for state-changing operations (optional, layered defense)

### PGY2-01ie Configuration

```python
# Access token cookie
Set-PGY2-01ie: access_token=<jwt>;
    HttpOnly;
    Secure;
    SameSite=Lax;
    Path=/api;
    Max-Age=900

# Refresh token cookie
Set-PGY2-01ie: refresh_token=<jwt>;
    HttpOnly;
    Secure;
    SameSite=Lax;
    Path=/api/auth/refresh;  # Restricted path!
    Max-Age=604800
```

**Key Points:**
- `HttpOnly`: Cannot be read by JavaScript
- `Secure`: Only sent over HTTPS (omit in development)
- `SameSite=Lax`: Prevents CSRF on POST requests
- `Path=/api/auth/refresh`: Refresh token ONLY sent to refresh endpoint
- `Max-Age`: PGY2-01ie expiration matches token expiration

---

## Backend Implementation Patterns

### Configuration Updates

```python
# backend/app/core/config.py - Add to Settings class

# JWT Settings
JWT_SECRET_KEY: str = "your-jwt-secret-key-change-in-production"
JWT_ALGORITHM: str = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES: int = 15
REFRESH_TOKEN_EXPIRE_DAYS: int = 7

# Security Settings
BCRYPT_ROUNDS: int = 12
MAX_LOGIN_ATTEMPTS: int = 5
LOCKOUT_DURATION_MINUTES: int = 30

# PGY2-01ie Settings
COOKIE_SECURE: bool = True  # Set False for local dev without HTTPS
COOKIE_SAMESITE: str = "lax"
COOKIE_DOMAIN: str | None = None  # Set for cross-subdomain auth
```

### Authentication Service

```python
# backend/app/services/auth.py

from datetime import datetime, timedelta
from typing import Optional
from uuid import UUID
import hashlib

from jose import jwt, JWTError
from passlib.context import CryptContext

from app.core.config import get_settings
from app.core.permissions import get_permissions
from app.models.user import User
from app.models.refresh_token import RefreshToken

settings = get_settings()
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


class AuthService:
    """Handles authentication operations."""

    @staticmethod
    def hash_password(password: str) -> str:
        """Hash a password using bcrypt."""
        return pwd_context.hash(password)

    @staticmethod
    def verify_password(plain_password: str, hashed_password: str) -> bool:
        """Verify a password against its hash."""
        return pwd_context.verify(plain_password, hashed_password)

    @staticmethod
    def create_access_token(user: User) -> str:
        """Create a short-lived access token."""
        permissions = [p.value for p in get_permissions(user.role)]

        payload = {
            "sub": str(user.id),
            "email": user.email,
            "role": user.role,
            "permissions": permissions,
            "person_id": str(user.person_id) if user.person_id else None,
            "type": "access",
            "iat": datetime.utcnow(),
            "exp": datetime.utcnow() + timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES),
        }

        return jwt.encode(payload, settings.JWT_SECRET_KEY, algorithm=settings.JWT_ALGORITHM)

    @staticmethod
    def create_refresh_token(user_id: UUID, token_id: UUID) -> str:
        """Create a long-lived refresh token."""
        payload = {
            "sub": str(user_id),
            "jti": str(token_id),
            "type": "refresh",
            "iat": datetime.utcnow(),
            "exp": datetime.utcnow() + timedelta(days=settings.REFRESH_TOKEN_EXPIRE_DAYS),
        }

        return jwt.encode(payload, settings.JWT_SECRET_KEY, algorithm=settings.JWT_ALGORITHM)

    @staticmethod
    def hash_token(token: str) -> str:
        """Create SHA-256 hash of token for storage."""
        return hashlib.sha256(token.encode()).hexdigest()

    @staticmethod
    def decode_token(token: str) -> Optional[dict]:
        """Decode and validate a JWT token."""
        try:
            payload = jwt.decode(
                token,
                settings.JWT_SECRET_KEY,
                algorithms=[settings.JWT_ALGORITHM]
            )
            return payload
        except JWTError:
            return None
```

### FastAPI Dependencies

```python
# backend/app/api/deps.py

from typing import Optional
from uuid import UUID
from fastapi import Depends, HTTPException, status, Request
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.models.user import User
from app.services.auth import AuthService
from app.core.permissions import Permission, has_permission


class TokenData:
    """Parsed token data."""
    def __init__(self, payload: dict):
        self.user_id = UUID(payload["sub"])
        self.email = payload["email"]
        self.role = payload["role"]
        self.permissions = payload["permissions"]
        self.person_id = UUID(payload["person_id"]) if payload.get("person_id") else None


def get_token_from_cookie(request: Request) -> Optional[str]:
    """Extract access token from HttpOnly cookie."""
    return request.cookies.get("access_token")


async def get_current_user(
    request: Request,
    db: Session = Depends(get_db),
) -> User:
    """
    Dependency to get the current authenticated user.
    Raises 401 if not authenticated.
    """
    token = get_token_from_cookie(request)
    if not token:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Not authenticated",
            headers={"WWW-Authenticate": "Bearer"},
        )

    payload = AuthService.decode_token(token)
    if not payload or payload.get("type") != "access":
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired token",
            headers={"WWW-Authenticate": "Bearer"},
        )

    user = db.query(User).filter(User.id == payload["sub"]).first()
    if not user or not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User not found or inactive",
        )

    return user


async def get_current_active_user(
    current_user: User = Depends(get_current_user),
) -> User:
    """Dependency that also checks user is active."""
    if not current_user.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Inactive user",
        )
    return current_user


def require_permission(permission: Permission):
    """
    Dependency factory for permission-based access control.

    Usage:
        @router.post("/people", dependencies=[Depends(require_permission(Permission.PEOPLE_CREATE))])
        def create_person(...):
            ...
    """
    async def permission_checker(
        current_user: User = Depends(get_current_active_user),
    ) -> User:
        if not has_permission(current_user.role, permission):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Permission denied: {permission.value}",
            )
        return current_user

    return permission_checker


def require_any_permission(*permissions: Permission):
    """Dependency that allows access if user has ANY of the specified permissions."""
    async def permission_checker(
        current_user: User = Depends(get_current_active_user),
    ) -> User:
        for permission in permissions:
            if has_permission(current_user.role, permission):
                return current_user
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Insufficient permissions",
        )

    return permission_checker
```

### Protected Route Example

```python
# backend/app/api/routes/people.py (modified)

from fastapi import APIRouter, Depends
from app.api.deps import get_current_active_user, require_permission
from app.core.permissions import Permission
from app.models.user import User

router = APIRouter()


@router.get("")
def list_people(
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db),
):
    """List all people - requires authentication."""
    # All authenticated users can list people
    ...


@router.post("", dependencies=[Depends(require_permission(Permission.PEOPLE_CREATE))])
def create_person(
    person_in: PersonCreate,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db),
):
    """Create a person - requires PEOPLE_CREATE permission."""
    ...


@router.delete("/{person_id}", dependencies=[Depends(require_permission(Permission.PEOPLE_DELETE))])
def delete_person(
    person_id: UUID,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db),
):
    """Delete a person - requires PEOPLE_DELETE permission."""
    ...
```

---

## Frontend Implementation Patterns

### Auth Context Provider

```typescript
// frontend/src/contexts/AuthContext.tsx

import React, { createContext, useContext, useState, useEffect, useCallback } from 'react'

interface User {
  id: string
  email: string
  fullName: string
  role: 'admin' | 'coordinator' | 'faculty'
  permissions: string[]
  personId?: string
}

interface AuthContextType {
  user: User | null
  isAuthenticated: boolean
  isLoading: boolean
  login: (email: string, password: string) => Promise<void>
  logout: () => Promise<void>
  hasPermission: (permission: string) => boolean
}

const AuthContext = createContext<AuthContextType | undefined>(undefined)

export function AuthProvider({ children }: { children: React.ReactNode }) {
  const [user, setUser] = useState<User | null>(null)
  const [isLoading, setIsLoading] = useState(true)

  // Check auth status on mount
  useEffect(() => {
    checkAuthStatus()
  }, [])

  const checkAuthStatus = async () => {
    try {
      const response = await fetch('/api/auth/me', {
        credentials: 'include', // Important: send cookies
      })
      if (response.ok) {
        const data = await response.json()
        setUser(data.user)
      }
    } catch (error) {
      // Not authenticated
    } finally {
      setIsLoading(false)
    }
  }

  const login = async (email: string, password: string) => {
    const response = await fetch('/api/auth/login', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      credentials: 'include',
      body: JSON.stringify({ email, password }),
    })

    if (!response.ok) {
      const error = await response.json()
      throw new Error(error.detail || 'Login failed')
    }

    const data = await response.json()
    setUser(data.user)
  }

  const logout = async () => {
    await fetch('/api/auth/logout', {
      method: 'POST',
      credentials: 'include',
    })
    setUser(null)
  }

  const hasPermission = useCallback((permission: string) => {
    return user?.permissions.includes(permission) ?? false
  }, [user])

  return (
    <AuthContext.Provider value={{
      user,
      isAuthenticated: !!user,
      isLoading,
      login,
      logout,
      hasPermission,
    }}>
      {children}
    </AuthContext.Provider>
  )
}

export function useAuth() {
  const context = useContext(AuthContext)
  if (context === undefined) {
    throw new Error('useAuth must be used within an AuthProvider')
  }
  return context
}
```

### API Client with Token Refresh

```typescript
// frontend/src/lib/api.ts

class ApiClient {
  private baseUrl = '/api'
  private isRefreshing = false
  private refreshPromise: Promise<boolean> | null = null

  async fetch<T>(
    endpoint: string,
    options: RequestInit = {}
  ): Promise<T> {
    const response = await this.makeRequest(endpoint, options)

    // If 401 and not already refreshing, try to refresh
    if (response.status === 401 && !this.isRefreshing) {
      const refreshed = await this.refreshToken()
      if (refreshed) {
        // Retry original request
        const retryResponse = await this.makeRequest(endpoint, options)
        if (!retryResponse.ok) {
          throw new ApiError(retryResponse.status, await retryResponse.json())
        }
        return retryResponse.json()
      } else {
        // Refresh failed, redirect to login
        window.location.href = '/login'
        throw new ApiError(401, { detail: 'Session expired' })
      }
    }

    if (!response.ok) {
      throw new ApiError(response.status, await response.json())
    }

    return response.json()
  }

  private async makeRequest(endpoint: string, options: RequestInit): Promise<Response> {
    return fetch(`${this.baseUrl}${endpoint}`, {
      ...options,
      credentials: 'include', // Always include cookies
      headers: {
        'Content-Type': 'application/json',
        ...options.headers,
      },
    })
  }

  private async refreshToken(): Promise<boolean> {
    // Prevent multiple simultaneous refresh attempts
    if (this.isRefreshing) {
      return this.refreshPromise!
    }

    this.isRefreshing = true
    this.refreshPromise = this.doRefresh()

    try {
      return await this.refreshPromise
    } finally {
      this.isRefreshing = false
      this.refreshPromise = null
    }
  }

  private async doRefresh(): Promise<boolean> {
    try {
      const response = await fetch(`${this.baseUrl}/auth/refresh`, {
        method: 'POST',
        credentials: 'include',
      })
      return response.ok
    } catch {
      return false
    }
  }
}

export const api = new ApiClient()
```

### Protected Route Component

```typescript
// frontend/src/components/ProtectedRoute.tsx

import { useAuth } from '@/contexts/AuthContext'
import { useRouter } from 'next/navigation'
import { useEffect } from 'react'

interface ProtectedRouteProps {
  children: React.ReactNode
  requiredPermission?: string
  requiredRole?: 'admin' | 'coordinator' | 'faculty'
}

export function ProtectedRoute({
  children,
  requiredPermission,
  requiredRole,
}: ProtectedRouteProps) {
  const { isAuthenticated, isLoading, user, hasPermission } = useAuth()
  const router = useRouter()

  useEffect(() => {
    if (!isLoading && !isAuthenticated) {
      router.push('/login')
    }
  }, [isLoading, isAuthenticated, router])

  if (isLoading) {
    return <LoadingSpinner />
  }

  if (!isAuthenticated) {
    return null
  }

  if (requiredPermission && !hasPermission(requiredPermission)) {
    return <AccessDenied />
  }

  if (requiredRole) {
    const roleHierarchy = { admin: 3, coordinator: 2, faculty: 1 }
    const userRoleLevel = roleHierarchy[user!.role]
    const requiredRoleLevel = roleHierarchy[requiredRole]

    if (userRoleLevel < requiredRoleLevel) {
      return <AccessDenied />
    }
  }

  return <>{children}</>
}
```

---

## Security Considerations

### Password Security

- **Hashing:** bcrypt with cost factor 12 (≈250ms per hash)
- **Requirements:** Minimum 8 characters, enforce complexity in frontend
- **Storage:** Never log or return passwords in any form

### Account Security

- **Rate Limiting:** 5 failed attempts trigger 30-minute lockout
- **Lockout:** Store `failed_login_attempts` and `locked_until` on User model
- **Reset:** Lockout clears after successful login

### Token Security

- **Access Token:** Short-lived (15 min), contains no sensitive data
- **Refresh Token:**
  - Single-use with rotation (prevents replay attacks)
  - Hash stored in DB (never store raw token)
  - Revocable (logout, password change, suspicious activity)
- **Secret Key:**
  - Use cryptographically secure random key (min 256 bits)
  - Different for each environment
  - Rotate periodically (existing tokens invalidated)

### Session Management

- **Concurrent Sessions:** Allow multiple (user can be on phone + desktop)
- **Logout All:** Admin/user can revoke all refresh tokens
- **Password Change:** Revoke all existing refresh tokens

### HTTPS Enforcement

- All production traffic must be HTTPS
- `Secure` cookie flag ensures cookies not sent over HTTP
- Consider HSTS header for strict enforcement

---

## ACGME Audit Trail Requirements

### Audit Log Model

```python
# backend/app/models/audit_log.py

class AuditLog(Base):
    """
    Tracks all user actions for ACGME compliance.
    Immutable - no updates or deletes allowed.
    """
    __tablename__ = "audit_logs"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)

    # Who
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)
    user_email = Column(String(255), nullable=False)  # Denormalized for history
    user_role = Column(String(50), nullable=False)    # Denormalized for history

    # What
    action = Column(String(100), nullable=False)  # e.g., "assignment.create"
    resource_type = Column(String(100), nullable=False)  # e.g., "assignment"
    resource_id = Column(UUID(as_uuid=True), nullable=True)

    # Details
    changes = Column(JSON, nullable=True)  # {field: {old: x, new: y}}
    metadata = Column(JSON, nullable=True)  # Additional context

    # Context
    ip_address = Column(String(45), nullable=True)
    user_agent = Column(String(500), nullable=True)

    # When
    created_at = Column(DateTime, default=datetime.utcnow, index=True)

    # Relationships
    user = relationship("User", back_populates="audit_logs")
```

### Audited Actions

| Action | Resource | Logged Data |
|--------|----------|-------------|
| Login | auth | success/failure, IP |
| Logout | auth | - |
| Password change | user | - |
| User create | user | new user details |
| User role change | user | old role, new role |
| Schedule generate | schedule | parameters, date range |
| Assignment create | assignment | full assignment details |
| Assignment update | assignment | changed fields |
| Assignment delete | assignment | deleted assignment |
| Absence create | absence | full absence details |
| Compliance override | compliance | violation, justification |

### Audit Service

```python
# backend/app/services/audit.py

from fastapi import Request

class AuditService:
    @staticmethod
    async def log(
        db: Session,
        user: User,
        action: str,
        resource_type: str,
        resource_id: UUID | None = None,
        changes: dict | None = None,
        metadata: dict | None = None,
        request: Request | None = None,
    ):
        """Create an audit log entry."""
        log = AuditLog(
            user_id=user.id,
            user_email=user.email,
            user_role=user.role,
            action=action,
            resource_type=resource_type,
            resource_id=resource_id,
            changes=changes,
            metadata=metadata,
            ip_address=request.client.host if request else None,
            user_agent=request.headers.get("user-agent") if request else None,
        )
        db.add(log)
        db.commit()
```

---

## API Endpoint Specifications

### Authentication Endpoints

```
POST /api/auth/login
  Request: { email: string, password: string }
  Response: { user: User }
  PGY2-01ies: Sets access_token, refresh_token

POST /api/auth/logout
  Response: { message: "Logged out" }
  PGY2-01ies: Clears access_token, refresh_token

POST /api/auth/refresh
  PGY2-01ies: Requires refresh_token
  Response: { message: "Token refreshed" }
  PGY2-01ies: Sets new access_token, refresh_token

GET /api/auth/me
  Response: { user: User }
  Note: Returns current user from access token

POST /api/auth/change-password
  Request: { current_password: string, new_password: string }
  Response: { message: "Password changed" }
  Note: Revokes all refresh tokens
```

### User Management Endpoints (Admin only)

```
GET /api/users
  Query: ?role=<role>&is_active=<bool>
  Response: { items: User[], total: number }

GET /api/users/{id}
  Response: User

POST /api/users
  Request: { email, password, full_name, role, person_id? }
  Response: User

PATCH /api/users/{id}
  Request: { full_name?, role?, is_active?, person_id? }
  Response: User

DELETE /api/users/{id}
  Response: 204 No Content

POST /api/users/{id}/revoke-sessions
  Response: { message: "All sessions revoked" }
```

---

## Implementation Checklist

### Backend Tasks (For Sonnet)

- [ ] Create `User` model in `backend/app/models/user.py`
- [ ] Create `RefreshToken` model in `backend/app/models/refresh_token.py`
- [ ] Create `AuditLog` model in `backend/app/models/audit_log.py`
- [ ] Create Alembic migration for new tables
- [ ] Implement `Permission` enum in `backend/app/core/permissions.py`
- [ ] Implement `AuthService` in `backend/app/services/auth.py`
- [ ] Implement `AuditService` in `backend/app/services/audit.py`
- [ ] Create dependencies in `backend/app/api/deps.py`
- [ ] Create auth routes in `backend/app/api/routes/auth.py`
- [ ] Create user management routes in `backend/app/api/routes/users.py`
- [ ] Update existing routes to require authentication
- [ ] Add settings to `backend/app/core/config.py`
- [ ] Create user schemas in `backend/app/schemas/user.py`
- [ ] Write tests for auth flow
- [ ] Create seed script for initial admin user

### Frontend Tasks (For Sonnet)

- [ ] Create `AuthContext` and `AuthProvider`
- [ ] Create login page at `/login`
- [ ] Update API client with refresh logic
- [ ] Create `ProtectedRoute` component
- [ ] Wrap app in `AuthProvider`
- [ ] Add logout functionality to navigation
- [ ] Create user management page (admin only)
- [ ] Add permission checks to existing pages
- [ ] Create "Access Denied" component

### Testing Requirements

- [ ] Login with valid credentials
- [ ] Login with invalid credentials (rate limiting)
- [ ] Token refresh works silently
- [ ] Logout clears session
- [ ] Permission checks work correctly
- [ ] Admin can manage users
- [ ] Coordinator cannot manage users
- [ ] Faculty has read-only access where appropriate
- [ ] Audit logs capture all actions

---

## Escalation Points

**Sonnet should escalate to Opus if:**

1. Token rotation logic seems incorrect
2. Permission boundary is unclear for a specific action
3. Audit log requirements conflict with performance needs
4. Security vulnerability is identified
5. ACGME compliance interpretation is needed

---

*End of Authentication Architecture Document*
