***REMOVED*** Authentication Endpoints

Base path: `/api/auth`

Manages user authentication, registration, and session management.

***REMOVED******REMOVED*** Endpoints Overview

| Method | Endpoint | Description | Auth Required |
|--------|----------|-------------|---------------|
| POST | `/login` | Login (OAuth2 form data) | No |
| POST | `/login/json` | Login (JSON body) | No |
| POST | `/logout` | Logout current user | Yes |
| GET | `/me` | Get current user info | Yes |
| POST | `/register` | Register new user | No |
| GET | `/users` | List all users | Yes (Admin) |

---

***REMOVED******REMOVED*** POST /api/auth/login

Authenticates a user using OAuth2 password flow and returns a JWT token.

***REMOVED******REMOVED******REMOVED*** Request

**Content-Type:** `application/x-www-form-urlencoded`

**Parameters:**

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `username` | string | Yes | User's username |
| `password` | string | Yes | User's password |

***REMOVED******REMOVED******REMOVED*** Example Request

```bash
curl -X POST http://localhost:8000/api/auth/login \
  -H "Content-Type: application/x-www-form-urlencoded" \
  -d "username=john.doe&password=SecurePassword123!"
```

***REMOVED******REMOVED******REMOVED*** Response

**Status:** `200 OK`

```json
{
  "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOiI1NTBlODQwMC1lMjliLTQxZDQtYTcxNi00NDY2NTU0NDAwMDAiLCJ1c2VybmFtZSI6ImpvaG4uZG9lIiwiZXhwIjoxNzA0MDY3MjAwfQ.signature",
  "token_type": "bearer"
}
```

***REMOVED******REMOVED******REMOVED*** Errors

| Status | Description |
|--------|-------------|
| 401 | Invalid username or password |

```json
{
  "detail": "Incorrect username or password"
}
```

---

***REMOVED******REMOVED*** POST /api/auth/login/json

Authenticates a user using JSON request body and returns a JWT token.

***REMOVED******REMOVED******REMOVED*** Request

**Content-Type:** `application/json`

**Body:**

```json
{
  "username": "john.doe",
  "password": "SecurePassword123!"
}
```

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `username` | string | Yes | User's username |
| `password` | string | Yes | User's password |

***REMOVED******REMOVED******REMOVED*** Example Request

```bash
curl -X POST http://localhost:8000/api/auth/login/json \
  -H "Content-Type: application/json" \
  -d '{
    "username": "john.doe",
    "password": "SecurePassword123!"
  }'
```

***REMOVED******REMOVED******REMOVED*** Response

**Status:** `200 OK`

```json
{
  "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "token_type": "bearer"
}
```

***REMOVED******REMOVED******REMOVED*** Errors

| Status | Description |
|--------|-------------|
| 401 | Invalid username or password |
| 422 | Validation error (missing fields) |

---

***REMOVED******REMOVED*** POST /api/auth/logout

Logs out the current authenticated user.

***REMOVED******REMOVED******REMOVED*** Request

**Headers:**

| Header | Value |
|--------|-------|
| `Authorization` | `Bearer <token>` |

***REMOVED******REMOVED******REMOVED*** Example Request

```bash
curl -X POST http://localhost:8000/api/auth/logout \
  -H "Authorization: Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9..."
```

***REMOVED******REMOVED******REMOVED*** Response

**Status:** `200 OK`

```json
{
  "message": "Successfully logged out"
}
```

***REMOVED******REMOVED******REMOVED*** Errors

| Status | Description |
|--------|-------------|
| 401 | Not authenticated |

---

***REMOVED******REMOVED*** GET /api/auth/me

Returns information about the currently authenticated user.

***REMOVED******REMOVED******REMOVED*** Request

**Headers:**

| Header | Value |
|--------|-------|
| `Authorization` | `Bearer <token>` |

***REMOVED******REMOVED******REMOVED*** Example Request

```bash
curl http://localhost:8000/api/auth/me \
  -H "Authorization: Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9..."
```

***REMOVED******REMOVED******REMOVED*** Response

**Status:** `200 OK`

```json
{
  "id": "550e8400-e29b-41d4-a716-446655440000",
  "username": "john.doe",
  "email": "john.doe@hospital.org",
  "role": "coordinator",
  "is_active": true
}
```

***REMOVED******REMOVED******REMOVED*** Errors

| Status | Description |
|--------|-------------|
| 401 | Not authenticated or invalid token |

---

***REMOVED******REMOVED*** POST /api/auth/register

Registers a new user account. The first user registered automatically becomes an admin.

***REMOVED******REMOVED******REMOVED*** Request

**Content-Type:** `application/json`

**Body:**

```json
{
  "username": "john.doe",
  "email": "john.doe@hospital.org",
  "password": "SecurePassword123!",
  "role": "coordinator"
}
```

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `username` | string | Yes | Unique username |
| `email` | string | Yes | Valid email address (unique) |
| `password` | string | Yes | User password |
| `role` | string | No | `admin`, `coordinator`, or `faculty` (default: `coordinator`) |

***REMOVED******REMOVED******REMOVED*** Example Request

```bash
curl -X POST http://localhost:8000/api/auth/register \
  -H "Content-Type: application/json" \
  -d '{
    "username": "john.doe",
    "email": "john.doe@hospital.org",
    "password": "SecurePassword123!",
    "role": "coordinator"
  }'
```

***REMOVED******REMOVED******REMOVED*** Response

**Status:** `201 Created`

```json
{
  "id": "550e8400-e29b-41d4-a716-446655440000",
  "username": "john.doe",
  "email": "john.doe@hospital.org",
  "role": "coordinator",
  "is_active": true
}
```

***REMOVED******REMOVED******REMOVED*** Errors

| Status | Description |
|--------|-------------|
| 400 | Username or email already exists |
| 422 | Validation error |

```json
{
  "detail": "Username already registered"
}
```

---

***REMOVED******REMOVED*** GET /api/auth/users

Returns a list of all users in the system. **Admin only.**

***REMOVED******REMOVED******REMOVED*** Request

**Headers:**

| Header | Value |
|--------|-------|
| `Authorization` | `Bearer <admin_token>` |

***REMOVED******REMOVED******REMOVED*** Example Request

```bash
curl http://localhost:8000/api/auth/users \
  -H "Authorization: Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9..."
```

***REMOVED******REMOVED******REMOVED*** Response

**Status:** `200 OK`

```json
[
  {
    "id": "550e8400-e29b-41d4-a716-446655440000",
    "username": "admin",
    "email": "admin@hospital.org",
    "role": "admin",
    "is_active": true
  },
  {
    "id": "550e8400-e29b-41d4-a716-446655440001",
    "username": "john.doe",
    "email": "john.doe@hospital.org",
    "role": "coordinator",
    "is_active": true
  }
]
```

***REMOVED******REMOVED******REMOVED*** Errors

| Status | Description |
|--------|-------------|
| 401 | Not authenticated |
| 403 | Not authorized (requires admin role) |

---

***REMOVED******REMOVED*** User Roles

| Role | Description | Capabilities |
|------|-------------|--------------|
| `admin` | System administrator | Full access to all endpoints |
| `coordinator` | Schedule coordinator | Manage schedules, people, and assignments |
| `faculty` | Faculty member | View-only access |

***REMOVED******REMOVED*** Token Format

The JWT token contains:

```json
{
  "sub": "550e8400-e29b-41d4-a716-446655440000",
  "username": "john.doe",
  "exp": 1704067200,
  "iat": 1703980800
}
```

| Claim | Description |
|-------|-------------|
| `sub` | User's UUID |
| `username` | Username |
| `exp` | Expiration timestamp |
| `iat` | Issued at timestamp |

***REMOVED******REMOVED*** Usage Examples

***REMOVED******REMOVED******REMOVED*** Complete Authentication Flow

```bash
***REMOVED*** 1. Register a new user
curl -X POST http://localhost:8000/api/auth/register \
  -H "Content-Type: application/json" \
  -d '{
    "username": "scheduler",
    "email": "scheduler@hospital.org",
    "password": "SecurePass123!"
  }'

***REMOVED*** 2. Login to get token
TOKEN=$(curl -s -X POST http://localhost:8000/api/auth/login/json \
  -H "Content-Type: application/json" \
  -d '{
    "username": "scheduler",
    "password": "SecurePass123!"
  }' | jq -r '.access_token')

echo "Token: $TOKEN"

***REMOVED*** 3. Use token for authenticated requests
curl http://localhost:8000/api/auth/me \
  -H "Authorization: Bearer $TOKEN"

***REMOVED*** 4. Logout when done
curl -X POST http://localhost:8000/api/auth/logout \
  -H "Authorization: Bearer $TOKEN"
```

---

*See also: [Authentication Guide](../authentication.md) for detailed authentication information*
