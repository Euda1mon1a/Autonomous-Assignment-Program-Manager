# API Design Standards

> **Last Updated:** 2025-12-19
> **Status:** Active
> **Audience:** Backend developers, frontend developers, API consumers

---

## Table of Contents

1. [Overview](#overview)
2. [RESTful API Conventions](#restful-api-conventions)
3. [Error Response Format](#error-response-format)
4. [Authentication Patterns](#authentication-patterns)
5. [Rate Limiting Policies](#rate-limiting-policies)
6. [Versioning Strategy](#versioning-strategy)
7. [Pagination Standards](#pagination-standards)
8. [Security Headers](#security-headers)
9. [Performance Considerations](#performance-considerations)

---

## Overview

The Residency Scheduler API follows RESTful principles with modern security practices including JWT-based authentication, rate limiting, and comprehensive error handling. This document defines the standards that all API endpoints must follow.

### Design Principles

- **Security First**: Defense-in-depth approach
- **Consistency**: Predictable patterns across all endpoints
- **Developer Experience**: Clear error messages, comprehensive documentation
- **Type Safety**: Full Pydantic validation on all inputs/outputs
- **Performance**: Optimized for healthcare workloads with proper caching

---

## RESTful API Conventions

### 1. URL Structure Patterns

All API endpoints follow a consistent hierarchical structure:

```
/api/v1/{resource}/{id?}/{sub-resource?}/{action?}
```

#### Examples

```
# Resource collections
GET    /api/v1/people                    # List all people
POST   /api/v1/people                    # Create new person

# Individual resources
GET    /api/v1/people/{person_id}        # Get specific person
PUT    /api/v1/people/{person_id}        # Update person (full)
PATCH  /api/v1/people/{person_id}        # Update person (partial)
DELETE /api/v1/people/{person_id}        # Delete person

# Sub-resources
GET    /api/v1/people/{person_id}/credentials          # Person's credentials
GET    /api/v1/people/{person_id}/procedures           # Person's procedures

# Actions (non-CRUD operations)
POST   /api/v1/schedule/generate                       # Generate schedule
POST   /api/v1/swap/{swap_id}/execute                  # Execute swap
POST   /api/v1/auth/logout                             # Logout user
```

### 2. HTTP Method Usage

| Method | Usage | Idempotent | Request Body | Response Body |
|--------|-------|------------|--------------|---------------|
| **GET** | Retrieve resource(s) | ✅ Yes | ❌ No | ✅ Yes |
| **POST** | Create resource or action | ❌ No | ✅ Yes | ✅ Yes |
| **PUT** | Replace resource (full update) | ✅ Yes | ✅ Yes | ✅ Yes |
| **PATCH** | Update resource (partial) | ❌ No* | ✅ Yes | ✅ Yes |
| **DELETE** | Remove resource | ✅ Yes | ❌ No | ⚠️ Optional |

*PATCH can be idempotent depending on implementation

### 3. Resource Naming Conventions

#### Use Plural Nouns

```python
# ✅ Good
/api/v1/people
/api/v1/assignments
/api/v1/rotations

# ❌ Bad
/api/v1/person
/api/v1/assignment
```

#### Use Kebab-Case for Multi-Word Resources

```python
# ✅ Good
/api/v1/rotation-templates
/api/v1/daily-manifest
/api/v1/academic-blocks

# ❌ Bad
/api/v1/rotation_templates
/api/v1/rotationTemplates
```

#### Actions Should Be Verbs

```python
# ✅ Good
POST /api/v1/schedule/generate
POST /api/v1/swap/{id}/execute
POST /api/v1/auth/logout

# ❌ Bad
POST /api/v1/schedule/generation
GET  /api/v1/swap/{id}/execute
```

### 4. Query Parameters

Use query parameters for filtering, sorting, and pagination:

```python
# Filtering
GET /api/v1/people?type=resident
GET /api/v1/people?type=faculty&specialty=cardiology
GET /api/v1/assignments?date_start=2024-01-01&date_end=2024-01-31

# Sorting
GET /api/v1/people?sort=name&order=asc
GET /api/v1/assignments?sort=date&order=desc

# Pagination
GET /api/v1/people?page=1&page_size=25
GET /api/v1/audit/logs?offset=50&limit=25

# Inclusion/Expansion
GET /api/v1/people/{id}?include=assignments,credentials
```

### 5. Status Codes

Standard HTTP status codes with consistent meanings:

#### Success Codes (2xx)

| Code | Usage | Example |
|------|-------|---------|
| **200 OK** | Successful GET, PUT, PATCH | Retrieved/updated person |
| **201 Created** | Successful POST (resource created) | Created new person |
| **204 No Content** | Successful DELETE | Deleted person |
| **207 Multi-Status** | Partial success with warnings | Schedule generated with warnings |

#### Client Error Codes (4xx)

| Code | Usage | Example |
|------|-------|---------|
| **400 Bad Request** | Invalid input format | Malformed JSON |
| **401 Unauthorized** | Missing/invalid authentication | No token provided |
| **403 Forbidden** | Valid auth but insufficient permissions | Faculty trying to delete schedule |
| **404 Not Found** | Resource doesn't exist | Person ID not found |
| **409 Conflict** | Resource state conflict | Schedule generation already in progress |
| **422 Unprocessable Entity** | Validation failed | PGY level must be 1-3 |
| **429 Too Many Requests** | Rate limit exceeded | Too many login attempts |

#### Server Error Codes (5xx)

| Code | Usage | Example |
|------|-------|---------|
| **500 Internal Server Error** | Unexpected server error | Database connection failed |
| **503 Service Unavailable** | Service temporarily unavailable | Maintenance mode |

---

## Error Response Format

We use **RFC 7807 Problem Details** for HTTP APIs with healthcare-specific adaptations.

### Standard Error Structure

```typescript
interface ProblemDetails {
  type: string;        // URI reference identifying the problem type
  title: string;       // Short, human-readable summary
  status: number;      // HTTP status code
  detail: string;      // Human-readable explanation
  instance?: string;   // URI reference for this specific occurrence
  errors?: Record<string, string[]>;  // Field-level validation errors
}
```

### Example Error Responses

#### 1. Validation Error (422)

```json
{
  "type": "/errors/validation-error",
  "title": "Validation Error",
  "status": 422,
  "detail": "Input validation failed for one or more fields",
  "instance": "/api/v1/people",
  "errors": {
    "pgy_level": ["pgy_level must be between 1 and 3"],
    "email": ["email must be a valid email address"]
  }
}
```

#### 2. Not Found Error (404)

```json
{
  "type": "/errors/not-found",
  "title": "Resource Not Found",
  "status": 404,
  "detail": "Person with ID 12345678-1234-1234-1234-123456789abc not found",
  "instance": "/api/v1/people/12345678-1234-1234-1234-123456789abc"
}
```

#### 3. Conflict Error (409)

```json
{
  "type": "/errors/conflict",
  "title": "Resource Conflict",
  "status": 409,
  "detail": "Schedule generation is already in progress for year 2024",
  "instance": "/api/v1/schedule/generate"
}
```

#### 4. Rate Limit Error (429)

```json
{
  "type": "/errors/rate-limit",
  "title": "Rate Limit Exceeded",
  "status": 429,
  "detail": "Too many requests. Please try again in 60 seconds.",
  "retry_after": 60
}
```

#### 5. ACGME Compliance Error (422)

```json
{
  "type": "/errors/acgme-compliance",
  "title": "ACGME Compliance Violation",
  "status": 422,
  "detail": "Assignment would violate ACGME 80-hour work week rule",
  "instance": "/api/v1/assignments",
  "violations": [
    {
      "rule": "80_hour_week",
      "person_id": "abc-123",
      "week_start": "2024-01-01",
      "projected_hours": 85.5,
      "limit": 80
    }
  ]
}
```

### Python Implementation

```python
"""Custom exception classes for application errors."""
from fastapi import HTTPException
from fastapi.responses import JSONResponse


class AppException(Exception):
    """Base exception for application errors (RFC 7807 compatible)."""

    def __init__(
        self,
        message: str,
        status_code: int = 400,
        error_type: str = None,
        errors: dict = None
    ):
        self.message = message
        self.status_code = status_code
        self.error_type = error_type or f"/errors/{self.__class__.__name__.lower()}"
        self.errors = errors
        super().__init__(message)


class NotFoundError(AppException):
    """Resource not found error (HTTP 404)."""
    def __init__(self, message: str = "Resource not found"):
        super().__init__(message, status_code=404, error_type="/errors/not-found")


class ValidationError(AppException):
    """Validation error for invalid input (HTTP 422)."""
    def __init__(self, message: str, errors: dict = None):
        super().__init__(
            message,
            status_code=422,
            error_type="/errors/validation-error",
            errors=errors
        )


class ConflictError(AppException):
    """Resource conflict error (HTTP 409)."""
    def __init__(self, message: str):
        super().__init__(message, status_code=409, error_type="/errors/conflict")


# Global exception handler (in main.py)
@app.exception_handler(AppException)
async def app_exception_handler(request: Request, exc: AppException):
    """Handle custom application exceptions with RFC 7807 format."""
    content = {
        "type": exc.error_type,
        "title": exc.__class__.__name__.replace("Error", " Error"),
        "status": exc.status_code,
        "detail": exc.message,
        "instance": str(request.url.path),
    }

    if exc.errors:
        content["errors"] = exc.errors

    return JSONResponse(
        status_code=exc.status_code,
        content=content
    )
```

### TypeScript Client Handling

```typescript
/**
 * Standardized API error shape (RFC 7807)
 */
export interface ApiError {
  type: string;
  title: string;
  status: number;
  detail: string;
  instance?: string;
  errors?: Record<string, string[]>;
  retry_after?: number;
}

/**
 * Transform axios errors into RFC 7807 ApiError
 */
function transformError(error: AxiosError): ApiError {
  if (error.response) {
    const { status, data } = error.response;
    const problemDetails = data as ApiError;

    return {
      type: problemDetails.type || `/errors/http-${status}`,
      title: problemDetails.title || getStatusTitle(status),
      status,
      detail: problemDetails.detail || getStatusMessage(status),
      instance: problemDetails.instance,
      errors: problemDetails.errors,
      retry_after: problemDetails.retry_after,
    };
  }

  // Network error
  return {
    type: '/errors/network',
    title: 'Network Error',
    status: 0,
    detail: 'Unable to reach server. Please check your connection.',
  };
}

/**
 * User-friendly error display
 */
function displayError(error: ApiError) {
  // Show field-level errors if available
  if (error.errors) {
    Object.entries(error.errors).forEach(([field, messages]) => {
      messages.forEach(msg => {
        toast.error(`${field}: ${msg}`);
      });
    });
  } else {
    // Show general error
    toast.error(error.detail || error.title);
  }

  // Handle rate limiting with retry
  if (error.status === 429 && error.retry_after) {
    toast.warning(`Rate limited. Retry in ${error.retry_after}s`);
  }
}
```

---

## Authentication Patterns

### JWT Token Structure

The API uses **JWT (JSON Web Tokens)** with the following claims:

```json
{
  "sub": "user-uuid-here",           // Subject: User ID
  "username": "dr.johnson",           // Username
  "jti": "token-uuid-here",          // JWT ID (for blacklist)
  "iat": 1640000000,                 // Issued At (Unix timestamp)
  "exp": 1640086400                  // Expiration (Unix timestamp)
}
```

### PGY2-01ie-Based Authentication Flow

**Security Note**: Tokens are stored in **httpOnly cookies** to prevent XSS attacks.

#### 1. Login

```http
POST /api/v1/auth/login
Content-Type: application/json

{
  "username": "dr.johnson",
  "password": "SecurePassword123!"
}
```

**Response:**

```http
HTTP/1.1 200 OK
Set-PGY2-01ie: access_token=Bearer eyJ...; HttpOnly; Secure; SameSite=Lax; Max-Age=86400; Path=/
Content-Type: application/json

{
  "access_token": "eyJ0eXAiOiJKV1QiLCJhbGc...",
  "token_type": "bearer",
  "expires_in": 86400
}
```

**PGY2-01ie Attributes:**
- `HttpOnly`: JavaScript cannot access (XSS protection)
- `Secure`: HTTPS only in production
- `SameSite=Lax`: CSRF protection
- `Max-Age`: 24 hours (configurable)
- `Path=/`: Available for all routes

#### 2. Authenticated Requests

PGY2-01ies are sent automatically by the browser:

```http
GET /api/v1/people
PGY2-01ie: access_token=Bearer eyJ0eXAiOiJKV1QiLCJhbGc...

HTTP/1.1 200 OK
{
  "items": [...],
  "total": 42
}
```

#### 3. Logout

```http
POST /api/v1/auth/logout
PGY2-01ie: access_token=Bearer eyJ0eXAiOiJKV1QiLCJhbGc...

HTTP/1.1 200 OK
Set-PGY2-01ie: access_token=; Max-Age=0; Path=/
{
  "message": "Successfully logged out"
}
```

**Security**: Token is added to Redis blacklist and cookie is cleared.

### Token Refresh Mechanism

**Current Implementation**: Long-lived tokens (24 hours) with blacklist support.

**Future Enhancement** (planned): Refresh token rotation.

```python
# Planned refresh endpoint
@router.post("/auth/refresh", response_model=Token)
async def refresh_token(
    refresh_token: str = PGY2-01ie(None),
    db: Session = Depends(get_db)
):
    """Refresh access token using refresh token."""
    # Validate refresh token
    # Issue new access token
    # Rotate refresh token (for security)
    pass
```

### Authorization Patterns

Role-Based Access Control (RBAC) with FastAPI dependencies:

```python
from app.core.security import get_current_active_user, get_admin_user

# Public endpoint (no auth required)
@router.get("/health")
async def health_check():
    return {"status": "healthy"}

# Authenticated endpoint (any logged-in user)
@router.get("/people")
async def list_people(
    current_user: User = Depends(get_current_active_user)
):
    # current_user is guaranteed to be authenticated
    pass

# Admin-only endpoint
@router.delete("/people/{person_id}")
async def delete_person(
    person_id: UUID,
    current_user: User = Depends(get_admin_user)
):
    # current_user is guaranteed to be admin
    pass

# Custom permission check
async def require_schedule_permission(
    current_user: User = Depends(get_current_active_user)
) -> User:
    if not current_user.can_manage_schedules:
        raise HTTPException(
            status_code=403,
            detail="Schedule management access required"
        )
    return current_user

@router.post("/schedule/generate")
async def generate_schedule(
    current_user: User = Depends(require_schedule_permission)
):
    pass
```

### TypeScript Client Authentication

```typescript
import { api } from '@/lib/api';

/**
 * Login with automatic cookie handling
 */
export async function login(credentials: LoginCredentials): Promise<LoginResponse> {
  const response = await api.post<LoginResponse>('/v1/auth/login', credentials);
  // PGY2-01ie is automatically set by browser from Set-PGY2-01ie header
  return response.data;
}

/**
 * Logout and clear cookie
 */
export async function logout(): Promise<void> {
  await api.post('/v1/auth/logout');
  // PGY2-01ie is automatically cleared by Set-PGY2-01ie header
  window.location.href = '/login';
}

/**
 * All authenticated requests automatically include cookie
 */
export async function getPeople(): Promise<PersonListResponse> {
  // PGY2-01ie sent automatically - no manual header needed!
  const response = await api.get<PersonListResponse>('/v1/people');
  return response.data;
}

/**
 * Axios configuration for cookies
 */
const api = axios.create({
  baseURL: '/api',
  withCredentials: true,  // ← Critical: Enable cookie support
  headers: {
    'Content-Type': 'application/json',
  },
});
```

---

## Rate Limiting Policies

Rate limiting prevents brute force attacks and API abuse using **Redis-based sliding window**.

### Limits by Endpoint Type

| Endpoint Type | Limit | Window | Key Prefix |
|--------------|-------|---------|-----------|
| **Login** | 5 requests | 60 seconds | `rate_limit:login:{ip}` |
| **Register** | 3 requests | 60 seconds | `rate_limit:register:{ip}` |
| **Password Reset** | 3 requests | 300 seconds | `rate_limit:reset:{ip}` |
| **General API** | 100 requests | 60 seconds | `rate_limit:api:{ip}` |

### Rate Limit Headers

All responses include rate limit information:

```http
HTTP/1.1 200 OK
X-RateLimit-Limit: 5
X-RateLimit-Remaining: 3
X-RateLimit-Reset: 1640000060
```

**Header Definitions:**
- `X-RateLimit-Limit`: Maximum requests allowed in window
- `X-RateLimit-Remaining`: Requests remaining in current window
- `X-RateLimit-Reset`: Unix timestamp when limit resets

### Retry-After Handling

When rate limited, response includes `Retry-After`:

```http
HTTP/1.1 429 Too Many Requests
X-RateLimit-Limit: 5
X-RateLimit-Remaining: 0
X-RateLimit-Reset: 1640000060
Retry-After: 60
Content-Type: application/json

{
  "type": "/errors/rate-limit",
  "title": "Rate Limit Exceeded",
  "status": 429,
  "detail": "Too many requests. Please try again in 60 seconds.",
  "retry_after": 60
}
```

### Python Implementation

```python
from app.core.rate_limit import create_rate_limit_dependency

# Create rate limiter for login endpoint
rate_limit_login = create_rate_limit_dependency(
    max_requests=5,
    window_seconds=60,
    key_prefix="login"
)

@router.post("/login")
async def login(
    form_data: OAuth2PasswordRequestForm = Depends(),
    db: Session = Depends(get_db),
    _rate_limit: None = Depends(rate_limit_login),  # ← Applied here
):
    """Login with rate limiting (5 attempts per minute)."""
    # Rate limit checked before handler executes
    pass
```

**Rate Limiting Algorithm**: Sliding window using Redis sorted sets.

```python
class RateLimiter:
    """Sliding window rate limiter using Redis."""

    def is_rate_limited(
        self,
        key: str,
        max_requests: int,
        window_seconds: int
    ) -> tuple[bool, dict]:
        """
        Check if request should be rate limited.

        Returns:
            (is_limited, info_dict)
        """
        current_time = time.time()
        window_start = current_time - window_seconds

        # Redis pipeline for atomicity
        pipe = self.redis.pipeline()

        # Remove old entries outside window
        pipe.zremrangebyscore(key, 0, window_start)

        # Count requests in current window
        pipe.zcard(key)

        # Add current request
        pipe.zadd(key, {str(current_time): current_time})

        # Set expiration (cleanup)
        pipe.expire(key, window_seconds + 10)

        results = pipe.execute()
        current_count = results[1]

        is_limited = current_count >= max_requests
        remaining = max(0, max_requests - current_count - 1)
        reset_at = int(current_time + window_seconds)

        return is_limited, {
            "remaining": remaining,
            "limit": max_requests,
            "reset_at": reset_at,
        }
```

### TypeScript Client Handling

```typescript
/**
 * Retry logic with exponential backoff for rate limits
 */
async function fetchWithRetry<T>(
  fetchFn: () => Promise<T>,
  maxRetries: number = 3
): Promise<T> {
  try {
    return await fetchFn();
  } catch (error) {
    const apiError = error as ApiError;

    // Rate limited - retry with backoff
    if (apiError.status === 429 && maxRetries > 0) {
      const retryAfter = apiError.retry_after || 60;

      // Show user-friendly message
      toast.warning(`Rate limited. Retrying in ${retryAfter}s...`);

      // Wait and retry
      await new Promise(resolve => setTimeout(resolve, retryAfter * 1000));
      return fetchWithRetry(fetchFn, maxRetries - 1);
    }

    throw error;
  }
}

// Usage
const people = await fetchWithRetry(() => getPeople());
```

---

## Versioning Strategy

### URL-Based Versioning

API version is specified in the URL path:

```
/api/v1/people
/api/v2/people  (future)
```

**Why URL-based?**
- ✅ Explicit and visible
- ✅ Easy to test multiple versions
- ✅ Clear in logs and monitoring
- ✅ Simple for clients to understand

### Current Version

**Version 1.0**: `/api/v1/`

All endpoints must include the version prefix:
```python
# In main.py
app.include_router(api_router, prefix="/api/v1")
```

### Backwards Compatibility

Deprecated endpoints are redirected temporarily:

```python
@app.middleware("http")
async def redirect_old_api(request: Request, call_next):
    """Redirect legacy /api routes to /api/v1 for backwards compatibility."""
    if request.url.path.startswith("/api/") and not request.url.path.startswith("/api/v1/"):
        new_path = request.url.path.replace("/api/", "/api/v1/", 1)
        return RedirectResponse(url=new_path, status_code=307)  # Temporary redirect
    return await call_next(request)
```

**Example:**
```
GET /api/people  →  307 Temporary Redirect  →  GET /api/v1/people
```

### Deprecation Policy

When introducing breaking changes:

1. **6 months before deprecation**:
   - Add `Deprecation` header to old endpoint
   - Document new endpoint in API docs
   - Send email to API consumers

```http
HTTP/1.1 200 OK
Deprecation: true
Sunset: Wed, 01 Jul 2024 00:00:00 GMT
Link: </api/v2/people>; rel="successor-version"
```

2. **3 months before deprecation**:
   - Add warning to response body
   - Increase monitoring alerts

3. **Deprecation date**:
   - Return `410 Gone` or `301 Permanent Redirect`
   - Provide migration guide

### Breaking Change Handling

**Breaking changes** require a new version:

- Removing a field from response
- Changing field type (string → integer)
- Renaming a field
- Changing validation rules (stricter)
- Removing an endpoint

**Non-breaking changes** (can stay in same version):

- Adding new optional field
- Adding new endpoint
- Making validation less strict
- Performance improvements
- Bug fixes

---

## Pagination Standards

### Offset/Limit Pattern

Standard pagination for most list endpoints:

```http
GET /api/v1/people?offset=0&limit=25
```

**Query Parameters:**
- `offset`: Number of items to skip (default: 0)
- `limit`: Number of items to return (default: 25, max: 100)

**Response Format:**

```json
{
  "items": [
    {
      "id": "uuid-1",
      "name": "Dr. Sarah Johnson",
      "type": "faculty"
    },
    {
      "id": "uuid-2",
      "name": "Dr. Michael Chen",
      "type": "resident",
      "pgy_level": 2
    }
  ],
  "total": 142,
  "offset": 0,
  "limit": 25,
  "has_more": true
}
```

**Response Fields:**
- `items`: Array of resources
- `total`: Total count of all items (ignoring pagination)
- `offset`: Current offset (for verification)
- `limit`: Current limit (for verification)
- `has_more`: Boolean indicating if more items exist

### Page-Based Pattern (Alternative)

For simpler UIs with page numbers:

```http
GET /api/v1/audit/logs?page=1&page_size=25
```

**Query Parameters:**
- `page`: Page number (1-indexed, default: 1)
- `page_size`: Items per page (default: 25, max: 100)

**Response Format:**

```json
{
  "items": [...],
  "total": 142,
  "page": 1,
  "page_size": 25,
  "total_pages": 6
}
```

### Cursor-Based Pagination (Future)

For real-time feeds and large datasets:

```http
GET /api/v1/assignments?cursor=eyJ0aW1lc3RhbXA...&limit=25
```

**Benefits:**
- ✅ Consistent results even with concurrent updates
- ✅ Better performance for large offsets
- ✅ Prevents duplicate/missing items

**Response Format:**

```json
{
  "items": [...],
  "next_cursor": "eyJ0aW1lc3RhbXA6MTY0MDAwMDAwMH0=",
  "has_more": true
}
```

### Python Implementation

```python
from pydantic import BaseModel

class PaginatedResponse(BaseModel):
    """Standard paginated response."""
    items: list
    total: int
    offset: int = 0
    limit: int = 25
    has_more: bool

def paginate_query(
    query,
    offset: int = 0,
    limit: int = 25,
    max_limit: int = 100
) -> PaginatedResponse:
    """
    Apply pagination to SQLAlchemy query.

    Args:
        query: SQLAlchemy query object
        offset: Number of items to skip
        limit: Number of items to return
        max_limit: Maximum allowed limit

    Returns:
        Paginated response with items and metadata
    """
    # Enforce max limit
    limit = min(limit, max_limit)

    # Get total count
    total = query.count()

    # Apply pagination
    items = query.offset(offset).limit(limit).all()

    # Check if more items exist
    has_more = (offset + limit) < total

    return PaginatedResponse(
        items=items,
        total=total,
        offset=offset,
        limit=limit,
        has_more=has_more
    )

# Usage in route
@router.get("/people", response_model=PersonListResponse)
def list_people(
    offset: int = Query(0, ge=0),
    limit: int = Query(25, ge=1, le=100),
    db: Session = Depends(get_db)
):
    """List all people with pagination."""
    query = db.query(Person)
    return paginate_query(query, offset, limit)
```

### TypeScript Client

```typescript
interface PaginatedResponse<T> {
  items: T[];
  total: number;
  offset: number;
  limit: number;
  has_more: boolean;
}

/**
 * Fetch paginated data with automatic cursor management
 */
async function fetchPaginated<T>(
  url: string,
  params: {
    offset?: number;
    limit?: number;
  } = {}
): Promise<PaginatedResponse<T>> {
  const { offset = 0, limit = 25 } = params;

  const response = await api.get<PaginatedResponse<T>>(url, {
    params: { offset, limit }
  });

  return response.data;
}

/**
 * React hook for infinite scroll pagination
 */
function useInfinitePagination<T>(url: string, pageSize: number = 25) {
  const [items, setItems] = useState<T[]>([]);
  const [offset, setOffset] = useState(0);
  const [hasMore, setHasMore] = useState(true);
  const [loading, setLoading] = useState(false);

  const loadMore = async () => {
    if (loading || !hasMore) return;

    setLoading(true);
    try {
      const response = await fetchPaginated<T>(url, {
        offset,
        limit: pageSize
      });

      setItems(prev => [...prev, ...response.items]);
      setOffset(prev => prev + pageSize);
      setHasMore(response.has_more);
    } catch (error) {
      toast.error('Failed to load more items');
    } finally {
      setLoading(false);
    }
  };

  return { items, loadMore, hasMore, loading };
}

// Usage in component
function PeopleList() {
  const { items, loadMore, hasMore, loading } = useInfinitePagination<Person>(
    '/v1/people',
    25
  );

  return (
    <div>
      {items.map(person => <PersonCard key={person.id} person={person} />)}
      {hasMore && (
        <button onClick={loadMore} disabled={loading}>
          {loading ? 'Loading...' : 'Load More'}
        </button>
      )}
    </div>
  );
}
```

---

## Security Headers

All responses include security headers:

```http
HTTP/1.1 200 OK
Strict-Transport-Security: max-age=31536000; includeSubDomains
X-Content-Type-Options: nosniff
X-Frame-Options: DENY
X-XSS-Protection: 1; mode=block
Content-Security-Policy: default-src 'self'
```

Configured in middleware (main.py):

```python
@app.middleware("http")
async def add_security_headers(request: Request, call_next):
    """Add security headers to all responses."""
    response = await call_next(request)

    # HSTS (HTTPS enforcement)
    if not settings.DEBUG:
        response.headers["Strict-Transport-Security"] = (
            "max-age=31536000; includeSubDomains; preload"
        )

    # Prevent MIME sniffing
    response.headers["X-Content-Type-Options"] = "nosniff"

    # Prevent clickjacking
    response.headers["X-Frame-Options"] = "DENY"

    # XSS protection (legacy)
    response.headers["X-XSS-Protection"] = "1; mode=block"

    # Content Security Policy
    response.headers["Content-Security-Policy"] = (
        "default-src 'self'; "
        "script-src 'self' 'unsafe-inline' 'unsafe-eval'; "
        "style-src 'self' 'unsafe-inline';"
    )

    return response
```

---

## Performance Considerations

### 1. Request Timeouts

```typescript
// Frontend: 120 second timeout for long operations
const api = axios.create({
  timeout: 120000,  // Schedule generation can take time
});
```

```python
# Backend: FastAPI timeout (via Uvicorn)
uvicorn app.main:app --timeout-keep-alive 120
```

### 2. Compression

Enable gzip compression for responses > 1KB:

```python
from fastapi.middleware.gzip import GZipMiddleware

app.add_middleware(GZipMiddleware, minimum_size=1000)
```

### 3. Caching Headers

```python
@router.get("/rotation-templates")
async def list_templates(response: Response):
    """List rotation templates with caching."""
    response.headers["Cache-Control"] = "public, max-age=3600"  # 1 hour
    return templates
```

### 4. Database Connection Pooling

```python
# In config.py
DB_POOL_SIZE: int = 10              # Base connections
DB_POOL_MAX_OVERFLOW: int = 20      # Additional connections
DB_POOL_TIMEOUT: int = 30           # Wait timeout (seconds)
DB_POOL_RECYCLE: int = 1800         # Recycle after 30 minutes
DB_POOL_PRE_PING: bool = True       # Verify before use
```

### 5. Async All The Way

```python
# ✅ Good - fully async
@router.get("/people")
async def list_people(db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(Person))
    return result.scalars().all()

# ❌ Bad - blocking I/O
@router.get("/people")
def list_people(db: Session = Depends(get_db)):
    return db.query(Person).all()
```

---

## Summary Checklist

When implementing a new API endpoint, ensure:

- [ ] URL follows RESTful conventions (`/api/v1/resource`)
- [ ] HTTP method matches operation (GET/POST/PUT/DELETE)
- [ ] Returns appropriate status codes (200, 201, 204, 404, etc.)
- [ ] Error responses use RFC 7807 Problem Details format
- [ ] Authentication required (unless public endpoint)
- [ ] Rate limiting applied (for sensitive endpoints)
- [ ] Pydantic schemas for request/response validation
- [ ] Pagination implemented for list endpoints
- [ ] Documentation includes code examples
- [ ] Security headers present
- [ ] Async/await used throughout
- [ ] Tests written (unit + integration)

---

*This document is a living standard. Update it when API patterns evolve.*
