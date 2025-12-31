# Authentication API Documentation

**Comprehensive Reference for Auth Endpoints**
Last Updated: 2025-12-30

---

## Table of Contents

1. [Overview](#overview)
2. [Authentication Model](#authentication-model)
3. [Endpoints](#endpoints)
   - [Login](#login)
   - [Login (JSON)](#login-json)
   - [Registration](#registration)
   - [Token Refresh](#token-refresh)
   - [Get Current User](#get-current-user)
   - [Logout](#logout)
   - [List Users](#list-users)
4. [Token Structure](#token-structure)
5. [Security Features](#security-features)
6. [Error Handling](#error-handling)
7. [Integration Guide](#integration-guide)
8. [Rate Limiting](#rate-limiting)
9. [Troubleshooting](#troubleshooting)
10. [Password Requirements](#password-requirements)

---

## Overview

The Residency Scheduler API uses **JWT (JSON Web Tokens)** for stateless authentication with a dual-token system:

- **Access Token**: Short-lived (default: 15 minutes), used for API requests
- **Refresh Token**: Long-lived (default: 7 days), used to obtain new access tokens without re-authentication

### Key Features

- **Dual-Token System**: Separates concerns between short-lived and long-lived credentials
- **httpOnly Cookies**: Access tokens stored in secure httpOnly cookies (XSS protection)
- **Token Rotation**: Refresh tokens automatically rotated on use
- **Token Blacklisting**: Logout and rotated tokens are permanently invalidated
- **Account Lockout**: Exponential backoff after failed login attempts
- **Rate Limiting**: IP and username-based rate limiting to prevent brute force attacks
- **Role-Based Access**: 8 user roles with granular permissions

---

## Authentication Model

### User Roles

| Role | Permissions | Description |
|------|-------------|-------------|
| **admin** | Full system access | Create/delete users, manage all features |
| **coordinator** | Manage schedules & people | Generate schedules, manage personnel |
| **faculty** | View/manage schedules | View own schedule, manage availability |
| **resident** | Limited schedule access | View own schedule, manage swaps |
| **clinical_staff** | View manifest/roster | General clinical staff access |
| **rn** | Clinical staff permissions | Registered Nurse role |
| **lpn** | Clinical staff permissions | Licensed Practical Nurse role |
| **msa** | Clinical staff permissions | Medical Support Assistant role |

### User Permissions Matrix

| Feature | Admin | Coordinator | Faculty | Resident | Clinical Staff |
|---------|-------|------------|---------|----------|---|
| Create users | ✓ | ✗ | ✗ | ✗ | ✗ |
| Manage schedules | ✓ | ✓ | ✗ | ✗ | ✗ |
| View own schedule | ✓ | ✓ | ✓ | ✓ | ✗ |
| Manage swaps | ✓ | ✓ | ✓ | ✓ | ✗ |
| View call roster | ✓ | ✓ | ✓ | ✓ | ✓ |

---

## Endpoints

### Login

<div class="endpoint-badge post">POST</div> `/api/auth/login`

Authenticate using OAuth2 password flow (form data).

#### Request

**Content-Type**: `application/x-www-form-urlencoded`

```
username=user@example.com&password=SecurePassword123!
```

#### Response

**Status**: 200 OK

```json
{
  "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "refresh_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "token_type": "bearer"
}
```

#### Headers Set by Server

```
Set-Cookie: access_token=Bearer eyJhbGciOiJIUzI1NiIs...;
            Path=/;
            HttpOnly;
            SameSite=Lax;
            Max-Age=900;
            Secure  (in production only)
```

#### Example cURL

```bash
curl -X POST http://localhost:8000/api/auth/login \
  -H "Content-Type: application/x-www-form-urlencoded" \
  -d "username=user@example.com&password=SecurePassword123!"
```

#### Example Python

```python
import httpx

response = httpx.post(
    "http://localhost:8000/api/auth/login",
    data={
        "username": "user@example.com",
        "password": "SecurePassword123!"
    }
)

tokens = response.json()
access_token = tokens["access_token"]
refresh_token = tokens["refresh_token"]

# The access token is also set as a cookie automatically
```

#### Example JavaScript

```javascript
const response = await fetch('/api/auth/login', {
  method: 'POST',
  headers: {
    'Content-Type': 'application/x-www-form-urlencoded',
  },
  body: `username=user@example.com&password=SecurePassword123!`,
  credentials: 'include'  // Include cookies
});

const { access_token, refresh_token } = await response.json();
```

#### Error Responses

**401 Unauthorized - Invalid Credentials**

```json
{
  "detail": "Incorrect username or password"
}
```

**429 Too Many Requests - Rate Limited**

```json
{
  "error": "Account temporarily locked",
  "message": "Too many failed login attempts. Try again in 300 seconds.",
  "lockout_seconds": 300
}
```

**422 Unprocessable Entity - Validation Error**

```json
{
  "detail": [
    {
      "loc": ["body", "username"],
      "msg": "field required",
      "type": "value_error.missing"
    }
  ]
}
```

---

### Login (JSON)

<div class="endpoint-badge post">POST</div> `/api/auth/login/json`

Alternative JSON-based authentication (preferred for API clients).

#### Request

**Content-Type**: `application/json`

```json
{
  "username": "user@example.com",
  "password": "SecurePassword123!"
}
```

#### Response

**Status**: 200 OK

```json
{
  "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "refresh_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "token_type": "bearer"
}
```

#### Example cURL

```bash
curl -X POST http://localhost:8000/api/auth/login/json \
  -H "Content-Type: application/json" \
  -d '{
    "username": "user@example.com",
    "password": "SecurePassword123!"
  }'
```

#### Example Python

```python
import httpx

response = httpx.post(
    "http://localhost:8000/api/auth/login/json",
    json={
        "username": "user@example.com",
        "password": "SecurePassword123!"
    }
)

tokens = response.json()
```

#### Note

This endpoint is identical to `/api/auth/login` in functionality but accepts JSON instead of form data. Preferred for API clients and REST clients.

---

### Registration

<div class="endpoint-badge post">POST</div> `/api/auth/register`

Create a new user account.

#### Request

**Content-Type**: `application/json`

```json
{
  "username": "newuser",
  "email": "newuser@example.com",
  "password": "SecurePassword123!",
  "role": "coordinator"
}
```

#### Parameters

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `username` | string | Yes | Unique username (1-100 characters) |
| `email` | string | Yes | Unique email address |
| `password` | string | Yes | Minimum 12 characters, complexity requirements |
| `role` | string | No | Default: `coordinator`. See [User Roles](#user-roles) for options |

#### Response

**Status**: 201 Created

```json
{
  "id": "550e8400-e29b-41d4-a716-446655440000",
  "username": "newuser",
  "email": "newuser@example.com",
  "role": "coordinator",
  "is_active": true
}
```

#### Authorization Rules

- **First user**: Automatically becomes `admin` (ignores `role` parameter)
- **Subsequent users**: Must be created by an admin user (requires authentication)

#### Password Requirements

Passwords must meet ALL of these criteria:

1. **Length**: 12-128 characters
2. **Complexity**: At least 3 of the following:
   - Lowercase letters (a-z)
   - Uppercase letters (A-Z)
   - Numbers (0-9)
   - Special characters (!@#$%^&*(),.?":{}\|<>)
3. **Not common**: Cannot be in the common password list (e.g., "password", "admin", "123456")

#### Example cURL

```bash
curl -X POST http://localhost:8000/api/auth/register \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer <admin_token>" \
  -d '{
    "username": "newuser",
    "email": "newuser@example.com",
    "password": "SecurePassword123!",
    "role": "faculty"
  }'
```

#### Error Responses

**400 Bad Request - Validation Error**

```json
{
  "detail": "Password must be at least 12 characters"
}
```

**400 Bad Request - Duplicate User**

```json
{
  "detail": "Username already registered"
}
```

**400 Bad Request - Duplicate Email**

```json
{
  "detail": "Email already registered"
}
```

**403 Forbidden - Insufficient Permissions**

```json
{
  "detail": "Admin access required to create users"
}
```

**429 Too Many Requests**

```json
{
  "detail": "Rate limit exceeded"
}
```

---

### Token Refresh

<div class="endpoint-badge post">POST</div> `/api/auth/refresh`

Exchange a refresh token for a new access token.

#### Request

**Content-Type**: `application/json`

```json
{
  "refresh_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9..."
}
```

#### Response

**Status**: 200 OK

```json
{
  "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "refresh_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "token_type": "bearer"
}
```

#### Token Rotation Behavior

When `REFRESH_TOKEN_ROTATE=true` (production default):

1. New access token issued
2. New refresh token issued
3. Old refresh token IMMEDIATELY blacklisted
4. Reusing old token returns 401 Unauthorized

**This prevents token theft**: If attacker steals a refresh token, the legitimate user's next refresh will invalidate it.

#### Example cURL

```bash
curl -X POST http://localhost:8000/api/auth/refresh \
  -H "Content-Type: application/json" \
  -d '{
    "refresh_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9..."
  }'
```

#### Example Python

```python
import httpx

def refresh_access_token(refresh_token: str) -> dict:
    """Get a new access token using refresh token."""
    response = httpx.post(
        "http://localhost:8000/api/auth/refresh",
        json={"refresh_token": refresh_token}
    )
    response.raise_for_status()
    return response.json()

# Usage
new_tokens = refresh_access_token(old_refresh_token)
new_access = new_tokens["access_token"]
new_refresh = new_tokens["refresh_token"]  # Store this
```

#### Error Responses

**401 Unauthorized - Invalid Token**

```json
{
  "detail": "Invalid or expired refresh token"
}
```

**401 Unauthorized - Blacklisted Token**

```json
{
  "detail": "Invalid or expired refresh token"
}
```

**401 Unauthorized - User Inactive**

```json
{
  "detail": "User not found or inactive"
}
```

---

### Get Current User

<div class="endpoint-badge get">GET</div> `/api/auth/me`

Get the authenticated user's information.

#### Request

**Headers**:
```
Authorization: Bearer <access_token>
```

Or automatically included via httpOnly cookie.

#### Response

**Status**: 200 OK

```json
{
  "id": "550e8400-e29b-41d4-a716-446655440000",
  "username": "user@example.com",
  "email": "user@example.com",
  "role": "coordinator",
  "is_active": true
}
```

#### Example cURL

```bash
curl -X GET http://localhost:8000/api/auth/me \
  -H "Authorization: Bearer eyJhbGciOiJIUzI1NiIs..."
```

#### Example Python

```python
import httpx

def get_current_user(access_token: str) -> dict:
    response = httpx.get(
        "http://localhost:8000/api/auth/me",
        headers={"Authorization": f"Bearer {access_token}"}
    )
    response.raise_for_status()
    return response.json()
```

#### Error Responses

**401 Unauthorized - Missing Token**

```json
{
  "detail": "Not authenticated"
}
```

**401 Unauthorized - Invalid Token**

```json
{
  "detail": "Not authenticated"
}
```

---

### Logout

<div class="endpoint-badge post">POST</div> `/api/auth/logout`

Invalidate the current token by adding it to the blacklist.

#### Request

**Headers**:
```
Authorization: Bearer <access_token>
```

#### Response

**Status**: 200 OK

```json
{
  "message": "Successfully logged out"
}
```

#### Side Effects

1. Access token added to blacklist (cannot be reused)
2. httpOnly cookie is deleted by client
3. User session effectively terminated

#### Example cURL

```bash
curl -X POST http://localhost:8000/api/auth/logout \
  -H "Authorization: Bearer eyJhbGciOiJIUzI1NiIs..." \
  -H "Cookie: access_token=Bearer eyJhbGciOiJIUzI1NiIs..."
```

#### Example JavaScript

```javascript
async function logout(accessToken) {
  const response = await fetch('/api/auth/logout', {
    method: 'POST',
    headers: {
      'Authorization': `Bearer ${accessToken}`,
    },
    credentials: 'include'
  });

  if (response.ok) {
    console.log('Logged out successfully');
    // Clear local state
  }
}
```

#### Error Responses

**401 Unauthorized - Not Authenticated**

```json
{
  "detail": "Not authenticated"
}
```

---

### List Users

<div class="endpoint-badge get">GET</div> `/api/auth/users`

List all users in the system. **Admin only**.

#### Request

**Headers**:
```
Authorization: Bearer <admin_token>
```

#### Response

**Status**: 200 OK

```json
[
  {
    "id": "550e8400-e29b-41d4-a716-446655440000",
    "username": "admin",
    "email": "admin@example.com",
    "role": "admin",
    "is_active": true
  },
  {
    "id": "660e8400-e29b-41d4-a716-446655440001",
    "username": "coordinator",
    "email": "coordinator@example.com",
    "role": "coordinator",
    "is_active": true
  }
]
```

#### Example cURL

```bash
curl -X GET http://localhost:8000/api/auth/users \
  -H "Authorization: Bearer <admin_token>"
```

#### Error Responses

**403 Forbidden - Insufficient Permissions**

```json
{
  "detail": "Admin access required"
}
```

**401 Unauthorized - Not Authenticated**

```json
{
  "detail": "Not authenticated"
}
```

---

## Token Structure

### Access Token Payload

```json
{
  "sub": "550e8400-e29b-41d4-a716-446655440000",
  "username": "user@example.com",
  "exp": 1735689600,
  "iat": 1735688700,
  "jti": "f47ac10b-58cc-4372-a567-0e02b2c3d479"
}
```

| Field | Description |
|-------|-------------|
| `sub` | Subject - User ID (UUID) |
| `username` | Username/email |
| `exp` | Expiration time (Unix timestamp) |
| `iat` | Issued at (Unix timestamp) |
| `jti` | JWT ID - Unique token identifier for blacklisting |

### Refresh Token Payload

```json
{
  "sub": "550e8400-e29b-41d4-a716-446655440000",
  "username": "user@example.com",
  "exp": 1736294400,
  "iat": 1735689600,
  "jti": "a47ac10b-58cc-4372-a567-0e02b2c3d479",
  "type": "refresh"
}
```

**Additional Field**:
- `type: "refresh"` - Distinguishes from access tokens (access tokens lack this field)

### Token Decoding Example

```python
import jwt
from app.core.config import get_settings

settings = get_settings()

def decode_token(token: str) -> dict:
    """Decode a JWT token (for inspection only)."""
    payload = jwt.decode(
        token,
        settings.SECRET_KEY,
        algorithms=["HS256"]
    )
    return payload
```

---

## Security Features

### 1. httpOnly Cookies (XSS Protection)

Access tokens are stored in httpOnly cookies that:

- Cannot be accessed by JavaScript (`httpOnly=True`)
- Only sent over HTTPS in production (`Secure=True`)
- Same-site restrictions prevent CSRF (`SameSite=Lax`)

```javascript
// This will NOT work - httpOnly prevents access
const token = document.cookie.match(/access_token=([^;]*)/);
// Result: null (cookie is inaccessible)
```

### 2. Token Type Validation

Refresh tokens explicitly cannot be used as access tokens:

```python
# In security.py - verify_token()
if payload.get("type") == "refresh":
    return None  # Reject refresh tokens as access tokens
```

This prevents privilege escalation where an attacker uses a long-lived refresh token as a short-lived access token.

### 3. Token Rotation

When enabled (`REFRESH_TOKEN_ROTATE=true`):

1. User calls `/api/auth/refresh` with refresh token
2. New access + refresh tokens issued
3. **Old refresh token immediately blacklisted**
4. Attacker reusing stolen token gets 401

**Timeline of token theft protection**:

```
T=0:00  Legitimate user calls /refresh
        - Receives new tokens
        - Old token blacklisted (instantly)

T=0:30  Attacker tries to use stolen old token
        - Request rejected (token already blacklisted)
        - User is alerted to attempt
```

### 4. Token Blacklisting

Tokens added to blacklist when:

- User explicitly logs out
- Refresh token is rotated
- User account is disabled
- Admin manually revokes token

Blacklist checked on every protected request:

```python
if TokenBlacklist.is_blacklisted(db, jti):
    return None  # Reject request
```

### 5. Account Lockout (Exponential Backoff)

Failed login attempts trigger exponential backoff:

```
Attempt 1-3: Allowed
Attempt 4: Locked for 60 seconds
Attempt 5: Locked for 120 seconds
Attempt 6: Locked for 240 seconds
...
(Max: 3600 seconds / 1 hour)
```

Per-username tracking prevents distributed attacks.

### 6. Rate Limiting

Multiple layers:

- **IP-based**: Max 5 login attempts per minute
- **Username-based**: Exponential backoff after failures
- **Global**: Falls back to allow if Redis is down

---

## Error Handling

### Error Response Format

All auth endpoints return standardized error responses:

```json
{
  "detail": "Error message or structured object"
}
```

### Error Types

#### 400 Bad Request - Validation Errors

```json
{
  "detail": [
    {
      "loc": ["body", "password"],
      "msg": "Password must be at least 12 characters",
      "type": "value_error"
    }
  ]
}
```

#### 401 Unauthorized - Authentication Failures

```json
{
  "detail": "Incorrect username or password"
}
```

Or with custom structure:

```json
{
  "detail": {
    "error": "Account temporarily locked",
    "message": "Too many failed login attempts. Try again in 300 seconds.",
    "lockout_seconds": 300
  }
}
```

#### 403 Forbidden - Authorization Failures

```json
{
  "detail": "Admin access required"
}
```

#### 429 Too Many Requests - Rate Limit

```json
{
  "detail": {
    "error": "Account temporarily locked",
    "message": "Too many failed login attempts. Try again in 300 seconds.",
    "lockout_seconds": 300
  }
}
```

Additional headers:

```
Retry-After: 300
WWW-Authenticate: Bearer
```

#### 422 Unprocessable Entity - Schema Validation

```json
{
  "detail": [
    {
      "loc": ["body", "email"],
      "msg": "invalid email format",
      "type": "value_error.email"
    }
  ]
}
```

### Common Error Scenarios

**Scenario 1: User tries to login with wrong password**

Request:
```bash
curl -X POST http://localhost:8000/api/auth/login/json \
  -d '{"username": "user@example.com", "password": "wrong"}'
```

Response: 401
```json
{
  "detail": "Incorrect username or password"
}
```

**Scenario 2: User exceeds login attempts**

After 5 failed attempts within 1 minute:

Response: 429
```json
{
  "detail": {
    "error": "Account temporarily locked",
    "message": "Too many failed login attempts. Try again in 60 seconds.",
    "lockout_seconds": 60
  }
}
```

**Scenario 3: Weak password during registration**

Request:
```bash
curl -X POST http://localhost:8000/api/auth/register \
  -d '{"username": "new", "email": "new@example.com", "password": "weak"}'
```

Response: 400
```json
{
  "detail": "Password must be at least 12 characters"
}
```

**Scenario 4: Token expired, need refresh**

Request with expired token:
```bash
curl -X GET http://localhost:8000/api/auth/me \
  -H "Authorization: Bearer <expired_token>"
```

Response: 401
```json
{
  "detail": "Not authenticated"
}
```

Solution: Use refresh token to get new access token.

---

## Integration Guide

### Browser-Based Frontend (React/Next.js)

#### 1. Login Flow

```javascript
async function login(username, password) {
  try {
    const response = await fetch('/api/auth/login/json', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ username, password }),
      credentials: 'include'  // Include cookies
    });

    if (!response.ok) {
      const error = await response.json();
      throw new Error(error.detail);
    }

    const { access_token, refresh_token } = await response.json();

    // Store refresh token in secure storage (not localStorage!)
    sessionStorage.setItem('refresh_token', refresh_token);

    return { success: true };
  } catch (error) {
    return { success: false, error: error.message };
  }
}
```

#### 2. Protected Requests

```javascript
async function fetchWithAuth(url, options = {}) {
  const response = await fetch(url, {
    ...options,
    credentials: 'include'  // Send httpOnly cookie
  });

  if (response.status === 401) {
    // Token expired, try refresh
    const refreshed = await refreshToken();
    if (!refreshed) {
      // Redirect to login
      window.location.href = '/login';
      return null;
    }
    // Retry original request
    return fetchWithAuth(url, options);
  }

  return response;
}
```

#### 3. Token Refresh

```javascript
async function refreshToken() {
  const refreshToken = sessionStorage.getItem('refresh_token');

  try {
    const response = await fetch('/api/auth/refresh', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ refresh_token: refreshToken }),
      credentials: 'include'
    });

    if (!response.ok) {
      return false;  // Refresh failed
    }

    const { refresh_token: newRefresh } = await response.json();
    sessionStorage.setItem('refresh_token', newRefresh);
    return true;
  } catch {
    return false;
  }
}
```

#### 4. Logout

```javascript
async function logout() {
  try {
    await fetch('/api/auth/logout', {
      method: 'POST',
      credentials: 'include'
    });
  } finally {
    sessionStorage.removeItem('refresh_token');
    window.location.href = '/login';
  }
}
```

### Python Backend Client

#### 1. Simple API Client

```python
import httpx
from typing import Optional

class AuthAPIClient:
    def __init__(self, base_url: str = "http://localhost:8000"):
        self.base_url = base_url
        self.access_token: Optional[str] = None
        self.refresh_token: Optional[str] = None
        self.client = httpx.Client()

    def login(self, username: str, password: str) -> bool:
        """Login and store tokens."""
        try:
            response = self.client.post(
                f"{self.base_url}/api/auth/login/json",
                json={"username": username, "password": password}
            )
            response.raise_for_status()

            data = response.json()
            self.access_token = data["access_token"]
            self.refresh_token = data["refresh_token"]
            return True
        except httpx.HTTPError as e:
            print(f"Login failed: {e}")
            return False

    def get_current_user(self) -> Optional[dict]:
        """Get current user info."""
        try:
            response = self.client.get(
                f"{self.base_url}/api/auth/me",
                headers={"Authorization": f"Bearer {self.access_token}"}
            )
            response.raise_for_status()
            return response.json()
        except httpx.HTTPError:
            return None

    def refresh_access_token(self) -> bool:
        """Get new access token."""
        try:
            response = self.client.post(
                f"{self.base_url}/api/auth/refresh",
                json={"refresh_token": self.refresh_token}
            )
            response.raise_for_status()

            data = response.json()
            self.access_token = data["access_token"]
            self.refresh_token = data["refresh_token"]
            return True
        except httpx.HTTPError:
            return False

    def logout(self) -> bool:
        """Logout and invalidate tokens."""
        try:
            self.client.post(
                f"{self.base_url}/api/auth/logout",
                headers={"Authorization": f"Bearer {self.access_token}"}
            )
            self.access_token = None
            self.refresh_token = None
            return True
        except httpx.HTTPError:
            return False

# Usage
client = AuthAPIClient()
if client.login("user@example.com", "password"):
    user = client.get_current_user()
    print(f"Logged in as: {user['username']}")
    client.logout()
```

#### 2. Async HTTP Client

```python
import httpx

async def login_async(username: str, password: str) -> dict:
    """Login with async HTTP client."""
    async with httpx.AsyncClient() as client:
        response = await client.post(
            "http://localhost:8000/api/auth/login/json",
            json={"username": username, "password": password}
        )
        response.raise_for_status()
        return response.json()
```

### cURL Examples

#### Login

```bash
curl -X POST http://localhost:8000/api/auth/login/json \
  -H "Content-Type: application/json" \
  -d '{"username": "user@example.com", "password": "SecurePassword123!"}'
```

#### Protected Request

```bash
curl -X GET http://localhost:8000/api/auth/me \
  -H "Authorization: Bearer <access_token>"
```

#### Refresh Token

```bash
curl -X POST http://localhost:8000/api/auth/refresh \
  -H "Content-Type: application/json" \
  -d '{"refresh_token": "<refresh_token>"}'
```

#### Logout

```bash
curl -X POST http://localhost:8000/api/auth/logout \
  -H "Authorization: Bearer <access_token>"
```

---

## Rate Limiting

### Endpoints and Limits

| Endpoint | Limit | Window | Behavior |
|----------|-------|--------|----------|
| `/api/auth/login` | 5 | 1 minute | IP + username lockout |
| `/api/auth/login/json` | 5 | 1 minute | IP + username lockout |
| `/api/auth/register` | 3 | 1 minute | IP-based |

### Account Lockout

After failed login attempts, the account is locked with exponential backoff:

```python
Attempt 1-3:   Allowed
Attempt 4:     Locked for 60s
Attempt 5:     Locked for 120s
Attempt 6:     Locked for 240s
Attempt 7:     Locked for 480s
...
(Caps at 3600s / 1 hour)
```

### Response Headers

When rate limited:

```
HTTP/1.1 429 Too Many Requests
Retry-After: 300
```

### Configuration

In `.env`:

```
RATE_LIMIT_ENABLED=true
RATE_LIMIT_LOGIN_ATTEMPTS=5
RATE_LIMIT_LOGIN_WINDOW=60
RATE_LIMIT_REGISTER_ATTEMPTS=3
RATE_LIMIT_REGISTER_WINDOW=60
```

---

## Troubleshooting

### Issue: "Not authenticated" on protected endpoints

**Cause**: Token not being sent or is invalid.

**Solutions**:
1. Verify token is included in `Authorization: Bearer <token>` header
2. Check if token has expired (default: 15 minutes)
3. Refresh token using `/api/auth/refresh` endpoint
4. Check if token is blacklisted (was logged out)

### Issue: "Invalid or expired refresh token"

**Cause**: Refresh token has expired or been rotated.

**Solutions**:
1. Check refresh token hasn't been used elsewhere (token rotation)
2. Refresh token default lifetime: 7 days
3. If using mobile app, implement token refresh before expiry
4. Login again to get new tokens

### Issue: Account locked after failed logins

**Cause**: Too many failed login attempts.

**Solutions**:
1. Wait for lockout period (60s minimum, up to 1 hour)
2. Check `lockout_seconds` in error response
3. Use `Retry-After` header for retry timing
4. Admin can reset lockout by querying database

### Issue: CORS errors when calling API

**Cause**: Browser blocking cross-origin requests.

**Solutions**:
1. Ensure frontend and backend are on same origin (localhost:3000 vs localhost:8000)
2. API should have CORS middleware enabled
3. Check `Access-Control-Allow-Origin` header in response
4. Ensure `credentials: 'include'` in fetch calls

### Issue: Token not being sent in cookies

**Cause**: `credentials: 'include'` not set or `Secure` flag issues.

**Solutions**:
1. Include `credentials: 'include'` in fetch requests
2. In production, ensure HTTPS is enabled (triggers `Secure` flag)
3. Check `SameSite=Lax` allows cross-site cookie sending
4. Verify httpOnly cookie is set in response headers

### Issue: "Incorrect username or password" but credentials are correct

**Cause**: Case-sensitive username, account inactive, or database issue.

**Solutions**:
1. Username comparison is case-sensitive
2. Check `is_active` field in user record
3. Verify user exists in database
4. Reset password if needed

### Issue: First user registration not becoming admin

**Cause**: First user logic only applies on initial registration.

**Solutions**:
1. First user is automatically admin (this is working correctly)
2. If database already has users, first registration won't be admin
3. Check user count in database: `SELECT COUNT(*) FROM users;`
4. Manual override: Update `role` column in users table

### Debug Checklist

```
[ ] Token is valid and not expired
[ ] Token type is correct (access vs refresh)
[ ] Token is not blacklisted
[ ] User account is active (is_active=true)
[ ] User role has required permissions
[ ] Authorization header format is correct
[ ] Request includes credentials: 'include' (browser)
[ ] CORS is properly configured
[ ] Rate limit not exceeded
[ ] Password meets complexity requirements
```

---

## Password Requirements

### Validation Rules

All passwords must pass these checks:

1. **Length**: 12-128 characters
2. **Complexity**: At least 3 of:
   - Lowercase: a-z
   - Uppercase: A-Z
   - Numbers: 0-9
   - Special: !@#$%^&*(),.?":{}\|<>
3. **Not common**: Cannot match common password list

### Examples

#### Valid Passwords

- `P@ssw0rd123` - ✓ (3 categories: lower, upper, number, special)
- `MySecurePass456` - ✓ (3 categories: lower, upper, number)
- `Correct-Horse-Battery!` - ✓ (3 categories: lower, upper, special)

#### Invalid Passwords

- `Password123` - ✗ (No special character, and "password" is common)
- `secure` - ✗ (Only 6 chars, only lowercase)
- `MyPassword` - ✗ (No numbers or special chars, only 2 categories)
- `Admin@123` - ✗ ("admin" is in common password list)

---

## Configuration Reference

### Environment Variables

```bash
# Token Expiration
ACCESS_TOKEN_EXPIRE_MINUTES=15      # Default: 15 minutes
REFRESH_TOKEN_EXPIRE_DAYS=7         # Default: 7 days

# Token Rotation
REFRESH_TOKEN_ROTATE=true           # Default: rotate on each refresh

# Rate Limiting
RATE_LIMIT_ENABLED=true             # Default: enabled
RATE_LIMIT_LOGIN_ATTEMPTS=5         # Per IP per minute
RATE_LIMIT_LOGIN_WINDOW=60          # Window in seconds
RATE_LIMIT_REGISTER_ATTEMPTS=3      # Per IP per minute
RATE_LIMIT_REGISTER_WINDOW=60       # Window in seconds

# Security
SECRET_KEY=<64-char-random>         # JWT signing key (REQUIRED)
DEBUG=false                         # Disables Secure flag in production
```

### Default Settings

| Setting | Default | Type | Notes |
|---------|---------|------|-------|
| `ACCESS_TOKEN_EXPIRE_MINUTES` | 15 | int | Configurable via env |
| `REFRESH_TOKEN_EXPIRE_DAYS` | 7 | int | Configurable via env |
| `REFRESH_TOKEN_ROTATE` | true | bool | Recommended for production |
| `RATE_LIMIT_ENABLED` | true | bool | Disable with caution |
| `SECRET_KEY` | (required) | str | Min 32 chars, must be random |

---

## OpenAPI Documentation

### Automatic Documentation

When running the server, documentation is available at:

- **Swagger UI**: http://localhost:8000/docs
- **ReDoc**: http://localhost:8000/redoc
- **OpenAPI JSON**: http://localhost:8000/openapi.json

### Example OpenAPI Schema

```json
{
  "paths": {
    "/api/auth/login/json": {
      "post": {
        "summary": "Authenticate user with JSON body",
        "requestBody": {
          "content": {
            "application/json": {
              "schema": {
                "type": "object",
                "properties": {
                  "username": { "type": "string" },
                  "password": { "type": "string" }
                },
                "required": ["username", "password"]
              }
            }
          }
        },
        "responses": {
          "200": {
            "description": "Login successful",
            "content": {
              "application/json": {
                "schema": {
                  "type": "object",
                  "properties": {
                    "access_token": { "type": "string" },
                    "refresh_token": { "type": "string" },
                    "token_type": { "type": "string" }
                  }
                }
              }
            }
          }
        }
      }
    }
  }
}
```

---

## Production Checklist

Before deploying to production, verify:

- [ ] `SECRET_KEY` is set to a random 64+ character value
- [ ] `WEBHOOK_SECRET` is set if using webhooks
- [ ] `DEBUG=false` in production
- [ ] `REFRESH_TOKEN_ROTATE=true`
- [ ] `RATE_LIMIT_ENABLED=true`
- [ ] HTTPS enabled (`Secure` flag on cookies)
- [ ] CORS properly configured for frontend domain
- [ ] Redis is running for rate limiting
- [ ] Database backups configured
- [ ] Token blacklist cleanup task scheduled
- [ ] Monitoring/logging configured for auth failures
- [ ] Test token refresh workflow
- [ ] Test account lockout behavior
- [ ] Test token rotation (if enabled)

---

## Additional Resources

- **Security Best Practices**: See `docs/security/DATA_SECURITY_POLICY.md`
- **Error Codes Reference**: See `docs/api/error-codes-reference.md`
- **API Index**: See `docs/api/index.md`
- **CLAUDE.md**: Project development guidelines

---

*Documentation generated: 2025-12-30*
*API Version: 1.0.0*
